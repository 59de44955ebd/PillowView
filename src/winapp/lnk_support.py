''' Simplified comtypes script for handling .LNK files in Windows '''

__all__ = ["get_lnk_target_path"]

from ctypes import *
from ctypes import _SimpleCData
from ctypes.wintypes import *
import atexit
from .dlls import ole32

_StringFromCLSID = ole32.StringFromCLSID
_CoTaskMemFree = windll.ole32.CoTaskMemFree
_ProgIDFromCLSID = ole32.ProgIDFromCLSID
_CLSIDFromString = ole32.CLSIDFromString
_CLSIDFromProgID = ole32.CLSIDFromProgID
_CoCreateGuid = ole32.CoCreateGuid

COINIT_APARTMENTTHREADED = 0x2
ole32.CoInitializeEx(None, COINIT_APARTMENTTHREADED)

def _shutdown(func=ole32.CoUninitialize):
    # Make sure no COM pointers stay in exception frames.
#    _exc_clear()
    try: func()
    except WindowsError: pass

    # Set the flag which means that calling obj.Release() is no longer
    # needed.
    if _cominterface_meta is not None:
        _cominterface_meta._com_shutting_down = True

atexit.register(_shutdown)

class GUID(Structure):
    _fields_ = [("Data1", DWORD),
                ("Data2", WORD),
                ("Data3", WORD),
                ("Data4", BYTE * 8)]

    def __init__(self, name=None):
        if name is not None:
            _CLSIDFromString(str(name), byref(self))

    def from_progid(cls, progid):
        """Get guid from progid, ...
        """
        if hasattr(progid, "_reg_clsid_"):
            progid = progid._reg_clsid_
        if isinstance(progid, cls):
            return progid
        elif isinstance(progid, str):
            if progid.startswith("{"):
                return cls(progid)
            inst = cls()
            _CLSIDFromProgID(str(progid), byref(inst))
            return inst
        else:
            raise TypeError("Cannot construct guid from %r" % progid)
    from_progid = classmethod(from_progid)


IID = GUID
LCID = DWORD
DISPID = LONG
SCODE = LONG
CLSCTX_SERVER = 5
# Not used
VARIANT = c_voidp
VARIANTARG = c_voidp

################################################################

class BSTR(_SimpleCData):
    "The windows BSTR data type"
    _type_ = "X"
    _needsfree = False
    def __repr__(self):
        return "%s(%r)" % (self.__class__.__name__, self.value)

    def __ctypes_from_outparam__(self):
        self._needsfree = True
        return self.value

    def __del__(self, _free=windll.oleaut32.SysFreeString):
        # Free the string if self owns the memory
        # or if instructed by __ctypes_from_outparam__.
        if self._b_base_ is None \
               or self._needsfree:
            _free(self)

################################################################
# global registries.

# allows to find interface classes by guid strings (iid)
com_interface_registry = {}

# allows to find coclasses by guid strings (clsid)
com_coclass_registry = {}

################################################################
# The metaclasses...

pythonapi.PyInstanceMethod_New.argtypes = [py_object]
pythonapi.PyInstanceMethod_New.restype = py_object
PyInstanceMethod_Type = type(pythonapi.PyInstanceMethod_New(id))

def instancemethod(func, inst, cls):
    mth = PyInstanceMethod_Type(func)
    if inst is None:
        return mth
    return mth.__get__(inst)

class _cominterface_meta(type):
    """Metaclass for COM interfaces.  Automatically creates high level
    methods from COMMETHOD lists.
    """

    # This flag is set to True by the atexit handler which calls
    # CoUnititialize.
    _com_shutting_down = False

    # Creates also a POINTER type for the newly created class.
    def __new__(self, name, bases, namespace):
        methods = namespace.pop("_methods_", None)
        dispmethods = namespace.pop("_disp_methods_", None)
        cls = type.__new__(self, name, bases, namespace)

        if methods is not None:
            cls._methods_ = methods
        if dispmethods is not None:
            cls._disp_methods_ = dispmethods

        # If we sublass a COM interface, for example:
        #
        # class IDispatch(IUnknown):
        #     ....
        #
        # then we need to make sure that POINTER(IDispatch) is a
        # subclass of POINTER(IUnknown) because of the way ctypes
        # typechecks work.
        if bases == (object,):
            _ptr_bases = (cls, _compointer_base)
        else:
            _ptr_bases = (cls, POINTER(bases[0]))

        # The interface 'cls' is used as a mixin.
        p = type(_compointer_base)("POINTER(%s)" % cls.__name__,
                                   _ptr_bases,
                                   {"__com_interface__": cls,
                                    "_needs_com_addref_": None})

        from ctypes import _pointer_type_cache
        _pointer_type_cache[cls] = p

#        @patcher.Patch(POINTER(p))
        class ReferenceFix(object):
            def __setitem__(self, index, value):
                # We override the __setitem__ method of the
                # POINTER(POINTER(interface)) type, so that the COM
                # reference count is managed correctly.
                #
                # This is so that we can implement COM methods that have to
                # return COM pointers more easily and consistent.  Instead of
                # using CopyComPointer in the method implementation, we can
                # simply do:
                #
                # def GetTypeInfo(self, this, ..., pptinfo):
                #     if not pptinfo: return E_POINTER
                #     pptinfo[0] = a_com_interface_pointer
                #     return S_OK
                if index != 0:
                    # CopyComPointer, which is in _ctypes, does only
                    # handle an index of 0.  This code does what
                    # CopyComPointer should do if index != 0.
                    if bool(value):
                        value.AddRef()
                    super(POINTER(p), self).__setitem__(index, value)
                    return
                from _ctypes import CopyComPointer
                CopyComPointer(value, self)

        return cls

    def __setattr__(self, name, value):
        if name == "_methods_":
            # XXX I'm no longer sure why the code generator generates
            # "_methods_ = []" in the interface definition, and later
            # overrides this by "Interface._methods_ = [...]
##            assert self.__dict__.get("_methods_", None) is None
            self._make_methods(value)
            self._make_specials()
        elif name == "_disp_methods_":
            assert self.__dict__.get("_disp_methods_", None) is None
            self._make_dispmethods(value)
            self._make_specials()
        type.__setattr__(self, name, value)

    def _make_specials(self):
        # This call installs methods that forward the Python protocols
        # to COM protocols.

        def has_name(name):
            # Determine whether a property or method named 'name'
            # exists
#            if self._case_insensitive_:
#                return name.lower() in self.__map_case__
            return hasattr(self, name)

        # XXX These special methods should be generated by the code generator.
        if has_name("Count"):
            @patcher.Patch(self)
            class _(object):
                def __len__(self):
                    "Return the the 'self.Count' property."
                    return self.Count

    def __get_baseinterface_methodcount(self):
        "Return the number of com methods in the base interfaces"
        try:
            result = 0
            for itf in self.mro()[1:-1]:
                result += len(itf.__dict__["_methods_"])
            return result
        except KeyError as err:
            (name,) = err.args
            if name == "_methods_":
                raise TypeError("baseinterface '%s' has no _methods_" % itf.__name__)
            raise

    def _make_methods(self, methods):
#        if self._case_insensitive_:
#            self._make_case_insensitive()

        # we insist on an _iid_ in THIS class!
        try:
            iid = self.__dict__["_iid_"]
        except KeyError:
            raise AttributeError("this class must define an _iid_")
        else:
            iid = str(iid)
            com_interface_registry[iid] = self
            del iid
        vtbl_offset = self.__get_baseinterface_methodcount()

        properties = {}

        # create private low level, and public high level methods
        for i, item in enumerate(methods):
            restype, name, argtypes, paramflags, idlflags, doc = item
            # the function prototype
            prototype = WINFUNCTYPE(restype, *argtypes)

            # a low level unbound method calling the com method.
            # attach it with a private name (__com_AddRef, for example),
            # so that custom method implementations can call it.

            # If the method returns a HRESULT, we pass the interface iid,
            # so that we can request error info for the interface.
            if restype == HRESULT:
##                print "%s.%s" % (self.__name__, name)
                raw_func = prototype(i + vtbl_offset, name, None, self._iid_)
                func = prototype(i + vtbl_offset, name, paramflags, self._iid_)
            else:
                raw_func = prototype(i + vtbl_offset, name, None, None)
                func = prototype(i + vtbl_offset, name, paramflags, None)
            setattr(self,
                    "_%s__com_%s" % (self.__name__, name),
                    instancemethod(raw_func, None, self))

            if paramflags:
                # see comment in the _fix_inout_args method
                dirflags = [(p[0]&3) for p in paramflags]
                if 3 in dirflags:
##                    fullname = "%s::%s" % (self.__name__, name)
##                    print "FIX %s" % fullname
                    func = self._fix_inout_args(func, argtypes, paramflags)

            # 'func' is a high level function calling the COM method
            func.__doc__ = doc
            try:
                func.__name__ = name # for pyhelp
            except TypeError:
                # In Python 2.3, __name__ is a readonly attribute
                pass
            # make it an unbound method.  Remember, 'self' is a type here.
            mth = instancemethod(func, None, self)

            # is it a property set or property get?
            is_prop = False

            # XXX Hm.  What, when paramflags is None?
            # Or does have '0' values?
            # Seems we loose then, at least for properties...

            # The following code assumes that the docstrings for
            # propget and propput are identical.
            if "propget" in idlflags:
                assert name.startswith("_get_")
                nargs = len([flags for flags in paramflags
                             if flags[0] & 7 in (0, 1)])
                # XXX or should we do this?
                # nargs = len([flags for flags in paramflags
                #             if (flags[0] & 1) or (flags[0] == 0)])
                propname = name[len("_get_"):]
                properties.setdefault((propname, doc, nargs), [None, None, None])[0] = func
                is_prop = True
            elif "propput" in idlflags:
                assert name.startswith("_set_")
                nargs = len([flags for flags in paramflags
                              if flags[0] & 7 in (0, 1)]) - 1
                propname = name[len("_set_"):]
                properties.setdefault((propname, doc, nargs), [None, None, None])[1] = func
                is_prop = True
            elif "propputref" in idlflags:
                assert name.startswith("_setref_")
                nargs = len([flags for flags in paramflags
                              if flags[0] & 7 in (0, 1)]) - 1
                propname = name[len("_setref_"):]
                properties.setdefault((propname, doc, nargs), [None, None, None])[2] = func
                is_prop = True

            # We install the method in the class, except when it's a
            # property accessor.  And we make sure we don't overwrite
            # a property that's already present in the class.
            if not is_prop:
                if hasattr(self, name):
                    setattr(self, "_" + name, mth)
                else:
                    setattr(self, name, mth)

            # COM is case insensitive.
            #
            # For a method, this is the real name.  For a property,
            # this is the name WITHOUT the _set_ or _get_ prefix.
#            if self._case_insensitive_:
#                self.__map_case__[name.lower()] = name
#                if is_prop:
#                    self.__map_case__[name[5:].lower()] = name[5:]

        # create public properties / attribute accessors
        for (name, doc, nargs), methods in list(properties.items()):
            # methods contains [propget or None, propput or None, propputref or None]
            if methods[1] is not None and methods[2] is not None:
                # both propput and propputref.
                #
                # Create a setter method that examines the argument type
                # and calls 'propputref' if it is an Object (in the VB
                # sense), or call 'propput' otherwise.
                propput = methods[1]
                propputref = methods[2]
                def put_or_putref(self, *args):
                    if _is_object(args[-1]):
                        return propputref(self, *args)
                    else:
                        return propput(self, *args)
                methods[1] = put_or_putref
                del methods[2]
            elif methods[2] is not None:
                # use propputref
                del methods[1]
            else:
                # use propput (if any)
                del methods[2]
            if nargs == 0:
                prop = property(*methods + [None, doc])
            else:
                # Hm, must be a descriptor where the __get__ method
                # returns a bound object having __getitem__ and
                # __setitem__ methods.
                prop = named_property("%s.%s" % (self.__name__, name), *methods + [doc])
            # Again, we should not overwrite class attributes that are
            # already present.
            if hasattr(self, name):
                setattr(self, "_" + name, prop)
            else:
                setattr(self, name, prop)

class _compointer_meta(type(c_void_p), _cominterface_meta):
    "metaclass for COM interface pointer classes"
    # no functionality, but needed to avoid a metaclass conflict

class _compointer_base(c_void_p, metaclass=_compointer_meta):
    "base class for COM interface pointer classes"
    def __del__(self):
        "Release the COM refcount we own."
        if self:
            if not type(self)._com_shutting_down:
                self.Release()

class EXCEPINFO(Structure):
    _fields_ = [
        ('wCode', WORD),
        ('wReserved', WORD),
        ('bstrSource', BSTR),
        ('bstrDescription', BSTR),
        ('bstrHelpFile', BSTR),
        ('dwHelpContext', DWORD),
        ('pvReserved', c_void_p),
        ('pfnDeferredFillIn', c_void_p),
        ('scode', SCODE),
    ]

################################################################

def CoCreateInstance(clsid, interface=None, clsctx=None, punkouter=None):
    """The basic windows api to create a COM class object and return a
    pointer to an interface.
    """
    if clsctx is None:
        clsctx = CLSCTX_SERVER
    if interface is None:
        interface = IUnknown
    p = POINTER(interface)()
    iid = interface._iid_
    ole32.CoCreateInstance(byref(clsid), punkouter, clsctx, byref(iid), byref(p))
    return p

def _manage(obj, clsid, interface):
    obj.__dict__['__clsid'] = str(clsid)
    return obj

def CreateObject(progid,                  # which object to create
                 clsctx=None,             # how to create the object
                 interface=None):         # the interface we want
    clsid = GUID.from_progid(progid)
    obj = CoCreateInstance(clsid, clsctx=clsctx, interface=interface)
    return _manage(obj, clsid, interface=interface)

def STDMETHOD(restype, name, argtypes=()):
    "Specifies a COM method slot without idlflags"
    # restype, name, argtypes, paramflags, idlflags, docstring
    return restype, name, argtypes, None, (), None

################################################################
# IUnknown, the root of all evil...

class IUnknown(object, metaclass=_cominterface_meta):
    """The most basic COM interface."""
    _case_insensitive_ = False
    _iid_ = GUID("{00000000-0000-0000-C000-000000000046}")

    _methods_ = [
        STDMETHOD(HRESULT, "QueryInterface", [POINTER(GUID), POINTER(c_void_p)]),
        STDMETHOD(c_ulong, "AddRef"),
        STDMETHOD(c_ulong, "Release")
    ]

    def QueryInterface(self, interface, iid=None):
        "QueryInterface(interface) -> instance"
        p = POINTER(interface)()
        if iid is None:
            iid = interface._iid_
        self.__com_QueryInterface(byref(iid), byref(p))
        clsid = self.__dict__.get('__clsid')
        if clsid is not None:
            p.__dict__['__clsid'] = clsid
        return p

_PARAMFLAGS = {
    "in": 1,
    "out": 2,
    "lcid": 4,
    "retval": 8,
    "optional": 16,
    }

def _encode_idl(names):
    # sum up all values found in _PARAMFLAGS, ignoring all others.
    return sum([_PARAMFLAGS.get(n, 0) for n in names])

_NOTHING = object()
def _unpack_argspec(idl, typ, name=None, defval=_NOTHING):
    return idl, typ, name, defval

def COMMETHOD(idlflags, restype, methodname, *argspec):
    """Specifies a COM method slot with idlflags."""
    paramflags = []
    argtypes = []
    helptext = None

    for item in argspec:
        idl, typ, argname, defval = _unpack_argspec(*item)
        pflags = _encode_idl(idl)
        if defval is _NOTHING:
            paramflags.append((pflags, argname))
        else:
            paramflags.append((pflags, argname, defval))
        argtypes.append(typ)
    if "propget" in idlflags:
        methodname = "_get_%s" % methodname
    elif "propput" in idlflags:
        methodname = "_set_%s" % methodname
    elif "propputref" in idlflags:
        methodname = "_setref_%s" % methodname
    return restype, methodname, tuple(argtypes), tuple(paramflags), tuple(idlflags), helptext

################################################################

class DISPPARAMS(Structure):
    _fields_ = [
        # C:/Programme/gccxml/bin/Vc71/PlatformSDK/oaidl.h 696
        ('rgvarg', POINTER(VARIANTARG)),
        ('rgdispidNamedArgs', POINTER(DISPID)),
        ('cArgs', UINT),
        ('cNamedArgs', UINT),
    ]
    def __del__(self):
        if self._b_needsfree_:
            for i in range(self.cArgs):
                self.rgvarg[i].value = None

class IDispatch(IUnknown):
    _iid_ = GUID("{00020400-0000-0000-C000-000000000046}")
    _methods_ = [
        COMMETHOD([], HRESULT, 'GetTypeInfoCount',
                  (['out'], POINTER(UINT) ) ),
        COMMETHOD([], HRESULT, 'GetTypeInfo',
                  (['in'], UINT, 'index'),
                  (['in'], LCID, 'lcid', 0),
                  (['out'], POINTER(POINTER(IUnknown)) ) ),
        STDMETHOD(HRESULT, 'GetIDsOfNames', [POINTER(IID), POINTER(c_wchar_p),
                                             UINT, LCID, POINTER(DISPID)]),
        STDMETHOD(HRESULT, 'Invoke', [DISPID, POINTER(IID), LCID, WORD,
                                      POINTER(DISPPARAMS), POINTER(VARIANT),
                                      POINTER(EXCEPINFO), POINTER(UINT)]),
    ]

class IWshShell(IDispatch):
    """Shell Object Interface"""
    _case_insensitive_ = False
    _iid_ = GUID('{F935DC21-1CF0-11D0-ADB9-00C04FD58A0B}')
    _idlflags_ = ['hidden', 'dual', 'oleautomation']

class IWshShortcut(IDispatch):
    """Shortcut Object"""
    _case_insensitive_ = False
    _iid_ = GUID('{F935DC23-1CF0-11D0-ADB9-00C04FD58A0B}')
    _idlflags_ = ['dual', 'oleautomation']

IWshShell._methods_ = [COMMETHOD([], HRESULT, '_')] * 4 + [
    COMMETHOD([], HRESULT, 'CreateShortcut',
        (['in'], BSTR, 'PathLink'),
        (['out', 'retval'], POINTER(POINTER(IDispatch)), 'out_Shortcut')
    ),
]

IWshShortcut._methods_ = [COMMETHOD([], HRESULT, '_')] * 10 + [
    COMMETHOD(['propget'], HRESULT, 'TargetPath', (['out', 'retval'], POINTER(BSTR), 'out_Path')),
]

def get_lnk_target_path(lnk_path):
    shortcut = CreateObject("WScript.Shell", interface=IWshShell).CreateShortcut(lnk_path)
    return shortcut.QueryInterface(IWshShortcut).TargetPath

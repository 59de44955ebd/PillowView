EVENT_CAN_UNDO_CHANGED = 1
EVENT_CAN_REDO_CHANGED = 2


class UndoStack():

    def __init__(self):
        self.can_undo = False
        self.can_redo = False

        self._states = []
        self._idx = -1
        self._listeners = {}

    def clear(self, base_state=None):
        if base_state:
            self._states = [base_state]
            self._idx = 0
        else:
            self._states = []
            self._idx = -1
        if self.can_undo:
            self.can_undo = False
            self.emit(EVENT_CAN_UNDO_CHANGED, False)
        if self.can_redo:
            self.can_redo = False
            self.emit(EVENT_CAN_REDO_CHANGED, False)

    def push(self, state):
        self._states = self._states[:self._idx + 1]  # clear redos
        self._states.append(state)
        self._idx += 1
        if not self.can_undo:
            self.can_undo = True
            self.emit(EVENT_CAN_UNDO_CHANGED, True)
        if self.can_redo:
            self.can_redo = False
            self.emit(EVENT_CAN_REDO_CHANGED, False)

    def undo(self):
        if self._idx > 0:
            self._idx -= 1
            if self._idx == 0:
                self.can_undo = False
                self.emit(EVENT_CAN_UNDO_CHANGED, False)
            if not self.can_redo and self._idx < len(self._states) - 1:
                self.can_redo = True
                self.emit(EVENT_CAN_REDO_CHANGED, True)
            return self._states[self._idx]

    def redo(self):
        if self._idx < len(self._states) - 1:
            self._idx += 1
            if self.can_redo and self._idx == len(self._states) - 1:
                self.can_redo = False
                self.emit(EVENT_CAN_REDO_CHANGED, False)
            if not self.can_undo:
                self.can_undo = True
                self.emit(EVENT_CAN_UNDO_CHANGED, True)
            return self._states[self._idx]

#    def can_undo(self):
#        return self._idx > 0
#
#    def can_redo(self):
#        return self._idx < len(self._states) - 1

    def connect(self, evt, func):
        if evt not in self._listeners:
            self._listeners[evt] = []
        self._listeners[evt].append(func)

    def disconnect(self, evt, func):
        if evt not in self._listeners:
            return
        idx = self._listeners[evt].find(func)
        if idx <= 0:
            del self._listeners[evt][idx]

    def emit(self, evt, *args):
        if evt not in self._listeners:
            return
        for func in self._listeners[evt]:
            func(*args)

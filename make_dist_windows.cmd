@echo off
setlocal EnableDelayedExpansion
cd /d %~dp0

REM Config
set APP_NAME=PillowView
set DIR=%CD%
set APP_DIR=%CD%\dist\%APP_NAME%\

REM Cleanup dist folder
rmdir /s /q "dist\%APP_NAME%" 2>nul
del "dist\%APP_NAME%-x64-full.7z" 2>nul
del "dist\%APP_NAME%-x64-no-plugins.7z" 2>nul
del "dist\%APP_NAME%-x64-setup.exe" 2>nul

REM "Compile" winapp contants
cd src
python _compile_const.py
cd ..
ren src\winapp\const.py __const.py
ren src\winapp\const_c.py const.py

echo.
echo ****************************************
echo Running pyinstaller...
echo ****************************************
set PYTHONPATH=
pyinstaller --noupx -w -n "%APP_NAME%" -i NONE -r src\resources.dll -D src\main.py ^
--hidden-import winapp.controls.button ^
--hidden-import winapp.controls.edit ^
--hidden-import winapp.controls.static ^
--hidden-import winapp.controls.toolbar ^
--hidden-import winapp.controls.updown ^
--exclude-module numpy ^
--exclude-module setuptools ^
--exclude-module webbrowser ^
--exclude-module xmlrpc ^
--exclude-module PIL.ImageCms ^
--exclude-module PIL.ImageMath ^
--exclude-module PIL.ImageQt ^
--exclude-module PIL.ImageShow ^
--exclude-module PIL.ImageTk ^
--exclude-module PIL.BufrStubImagePlugin ^
--exclude-module PIL.GribStubImagePlugin ^
--exclude-module PIL.Hdf5StubImagePlugin ^
--exclude-module PIL.ImtImagePlugin ^
--exclude-module PIL.McIdasImagePlugin ^
--exclude-module PIL.MicImagePlugin ^
--exclude-module PIL.MpegImagePlugin ^
--exclude-module PIL.PalmImagePlugin ^
--exclude-module PIL.XVThumbImagePlugin

ren src\winapp\const.py const_c.py
ren src\winapp\__const.py const.py

echo.
echo ****************************************
echo Copying resources...
echo ****************************************
copy src\tinyspline.dll "dist\%APP_NAME%\_internal\"
xcopy /e src\plugins "dist\%APP_NAME%\_internal\plugins\" >nul

echo.
echo ****************************************
echo Optimizing dist folder...
echo ****************************************

del "dist\%APP_NAME%\_internal\api-ms-win-*.dll"
del "dist\%APP_NAME%\_internal\ucrtbase.dll"
del "dist\%APP_NAME%\_internal\VCRUNTIME140.dll"

del "dist\%APP_NAME%\_internal\libcrypto-3.dll
del "dist\%APP_NAME%\_internal\libssl-3.dll
del "dist\%APP_NAME%\_internal\_bz2.pyd
del "dist\%APP_NAME%\_internal\_lzma.pyd"
del "dist\%APP_NAME%\_internal\_ssl.pyd"

call :create_7z
call :create_installer

:done
echo.
echo ****************************************
echo Done.
echo ****************************************
echo.
pause

endlocal
goto :eof


:create_7z
if not exist "C:\Program Files\7-Zip\" (
	echo.
	echo ****************************************
	echo 7z.exe not found at default location, omitting .7z creation...
	echo ****************************************
	exit /B
)
echo.
echo ****************************************
echo Creating .7z archives...
echo ****************************************
cd dist
set PATH=C:\Program Files\7-Zip;%PATH%

7z a "%APP_NAME%-x64-full.7z" "%APP_NAME%\*"
move /y "%APP_NAME%\_internal\plugins" .
7z a "%APP_NAME%-x64-no-plugins.7z" "%APP_NAME%\*"
move /y plugins "%APP_NAME%\_internal\"
cd ..
exit /B


:create_installer
if not exist "C:\Program Files (x86)\NSIS\" (
	echo.
	echo ****************************************
	echo NSIS not found at default location, omitting installer creation...
	echo ****************************************
	exit /B
)
echo.
echo ****************************************
echo Creating installer...
echo ****************************************

REM Get length of APP_DIR
set TF=%TMP%\x
echo %APP_DIR%> %TF%
for %%? in (%TF%) do set /a LEN=%%~z? - 2
del %TF%

call :make_abs_nsh nsis\uninstall_list.nsh

del "%NSH%" 2>nul

cd "%APP_DIR%"

for /F %%f in ('dir /b /a-d') do (
	echo Delete "$INSTDIR\%%f" >> "%NSH%"
)

for /F %%d in ('dir /s /b /aD') do (
	cd "%%d"
	set DIR_REL=%%d
	for /F %%f IN ('dir /b /a-d 2^>nul') do (
		echo Delete "$INSTDIR\!DIR_REL:~%LEN%!\%%f" >> "%NSH%"
	)
)

cd "%APP_DIR%"

for /F %%d in ('dir /s /b /ad^|sort /r') do (
	set DIR_REL=%%d
	echo RMDir "$INSTDIR\!DIR_REL:~%LEN%!" >> "%NSH%"
)

cd "%DIR%"
set PATH=C:\Program Files (x86)\NSIS;%PATH%
makensis nsis\make-installer.nsi
exit /B


:make_abs_nsh
set NSH=%~dpnx1%
exit /B

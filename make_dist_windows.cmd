@echo off
setlocal EnableDelayedExpansion
cd /d %~dp0

:: config
set APP_NAME=PillowView

:: cleanup
rmdir /s /q "dist\%APP_NAME%" 2>nul
::del "dist\%APP_NAME%-standalone-windows-x64.zip" 2>nul

cd src
python _compile_const.py
cd ..

set PYTHONPATH=

ren src\winapp\const.py __const.py
ren src\winapp\const_c.py const.py

echo.
echo ****************************************
echo Running pyinstaller...
echo ****************************************

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
::del "dist\%APP_NAME%\_internal\PIL\_imagingtk.cp312-win_amd64.pyd"
::del "dist\%APP_NAME%\_internal\PIL\_imagingcms.cp312-win_amd64.pyd"
::del "dist\%APP_NAME%\_internal\PIL\_avif.cp312-win_amd64.pyd"
del "dist\%APP_NAME%\_internal\libcrypto-3.dll
del "dist\%APP_NAME%\_internal\libssl-3.dll
del "dist\%APP_NAME%\_internal\_bz2.pyd
del "dist\%APP_NAME%\_internal\_lzma.pyd"
del "dist\%APP_NAME%\_internal\_ssl.pyd

::echo.
::echo ****************************************
::echo Creating ZIP...
::echo ****************************************
::
::cd dist
::del "%APP_NAME%-standalone-windows-x64.zip" 2>nul
::zip -q -r "%APP_NAME%-standalone-windows-x64.zip" "%APP_NAME%"
::cd ..

echo.
pause

@echo off
echo #### ANACONDA QUICKLAUNCH ####
echo #
echo for windows (linux: native py)
echo #
echo    by thirschbuechler, 2020
echo ####                      ####
echo # 
echo if the next line doesn't work, install anaconda first
echo TRY RUNNING PYTHON / PYTHON3, verify that "Anaconda" is mentioned.
echo IF NOT; that's a bad link, remove non-anaconda python from your system and the path-variable
echo #
echo DON'T run a file "as executable"
echo * double-click and execute
echo * windows: calling it per command line
echo #
echo USE PYTHON/PYTHON3 as mentioned above (anacondas python3 registers as python)
echo sidenote: on linux you don't need anaconda
echo #
echo press enter
set /p asdf=""
cmd.exe  /k "activate "%USERPROFILE%\AppData\Local\Continuum\anaconda3" & "
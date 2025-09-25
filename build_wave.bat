@echo off
echo ========================================
echo   CREATION DES EXECUTABLES WAVE
echo ========================================
echo.

echo [1/4] Installation de PyInstaller...
py -3.13 -m pip install pyinstaller pillow
if %errorlevel% neq 0 (
    echo ERREUR: Installation de PyInstaller echouee
    pause
    exit /b 1
)

echo.
echo [2/4] Creation de l'executable WAVE CONNECT GOV...

REM Detection des images disponibles pour WAVE Connect Gov
set ADD_DATA_GOV=
if exist "logo.png" (
    echo   - Ajout de logo.png
    set ADD_DATA_GOV=%ADD_DATA_GOV% --add-data="logo.png;."
)
if exist "WAVE-CONNECT.png" (
    echo   - Ajout de WAVE-CONNECT.png
    set ADD_DATA_GOV=%ADD_DATA_GOV% --add-data="WAVE-CONNECT.png;."
)

py -3.13 -m PyInstaller --onefile --windowed --name="WAVE_Connect_Gov" %ADD_DATA_GOV% wave_connect_gov.py
if %errorlevel% neq 0 (
    echo ERREUR: Creation WAVE Connect Gov echouee
    pause
    exit /b 1
)

echo.
echo [3/4] Creation de l'executable WAVE RECEPTEUR...

REM Detection des images disponibles pour WAVE Recepteur
set ADD_DATA_REC=
if exist "WAVE-CONNECT.png" (
    echo   - Ajout de WAVE-CONNECT.png
    set ADD_DATA_REC=%ADD_DATA_REC% --add-data="WAVE-CONNECT.png;."
)
if exist "logo.png" (
    echo   - Ajout de logo.png
    set ADD_DATA_REC=%ADD_DATA_REC% --add-data="logo.png;."
)

py -3.13 -m PyInstaller --onefile --windowed --name="WAVE_Recepteur" %ADD_DATA_REC% wave_recepteur.py
if %errorlevel% neq 0 (
    echo ERREUR: Creation WAVE Recepteur echouee
    pause
    exit /b 1
)

echo.
echo [4/4] Nettoyage des fichiers temporaires...
rmdir /s /q build 2>nul
del *.spec 2>nul

echo.
echo ========================================
echo        CREATION TERMINEE AVEC SUCCES !
echo ========================================
echo.
echo Executables crees dans le dossier 'dist' :
echo  - WAVE_Connect_Gov.exe
echo  - WAVE_Recepteur.exe
echo.
echo Appuyez sur une touche pour ouvrir le dossier...
pause >nul
explorer dist
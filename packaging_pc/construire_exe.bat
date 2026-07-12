@echo off
REM ============================================================
REM  Construction du .exe - Fofana Voyage Colis
REM  A executer UNE SEULE FOIS sur un PC Windows avec Python installe.
REM  Double-cliquez simplement sur ce fichier.
REM ============================================================

cd /d "%~dp0\.."

echo [1/3] Installation des dependances...
python -m pip install --upgrade pip
python -m pip install kivy kivy_deps.sdl2 kivy_deps.glew kivy_deps.angle pillow reportlab qrcode plyer requests pyinstaller

echo.
echo [2/3] Construction de l'executable...
pyinstaller --noconfirm --onedir --windowed --name "FofanaVoyage" ^
  --add-data "assets;assets" ^
  --add-data "ui;ui" ^
  --add-data "database;database" ^
  --add-data "modules;modules" ^
  --add-data "config;config" ^
  --add-data "utils;utils" ^
  main.py

echo.
echo [3/3] Termine !
echo L'application se trouve dans le dossier : dist\FofanaVoyage\
echo Le fichier a lancer est : dist\FofanaVoyage\FofanaVoyage.exe
echo.
pause

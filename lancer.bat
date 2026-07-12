@echo off
title Fofana Voyage — Gestion des Colis
color 0C
echo.
echo  =========================================
echo   FOFANA VOYAGE - Gestion des Colis v1.0
echo  =========================================
echo.

REM Vérifier que Python est installé
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERREUR] Python n'est pas installe ou pas dans le PATH.
    echo Telechargez Python sur https://www.python.org
    pause
    exit /b 1
)

REM Installer les dépendances si nécessaire
echo [1/2] Verification des dependances...
pip install qrcode[pil] Pillow reportlab --quiet
echo       OK

REM Lancer l'application
echo [2/2] Lancement de l'application...
echo.
python main.py

if %errorlevel% neq 0 (
    echo.
    echo [ERREUR] L'application a rencontre une erreur.
    pause
)

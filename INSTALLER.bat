@echo off
title PharmaRegl Maroc - Installation
cd /d "%~dp0"
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0outils\installer.ps1"

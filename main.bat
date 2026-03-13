echo off

:: Cambia el directorio de trabajo a la carpeta donde se encuentra este archivo .bat
:: %~dp0 es una variable especial que se expande a la ruta completa del script actual.
:: El modificador /d asegura que también se cambie la unidad de disco si es necesario.
cd /d %~dp0

call venv\Scripts\activate.bat
python main.py


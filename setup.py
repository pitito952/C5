# setup.py
# -*- coding: utf-8 -*-

import sys
from cx_Freeze import setup, Executable

# ==============================================================================
#  Configuración de la Aplicacin
# ==============================================================================

# Script principal de tu aplicacion
main_script = "main.py"

# Nombre del ejecutable final
app_name = "caja_chica"

# ==============================================================================
#  Opciones de Construccin para cx_Freeze
# ==============================================================================

# Lista de paquetes que deben ser incluidos explcitamente.
# cx_Freeze a veces no detecta todos los submdulos.
packages_to_include = [
    "sys",
    "os",
    "PySide6.QtCore",
    "PySide6.QtGui",
    "PySide6.QtWidgets",
    "PySide6.QtSql",
    "PySide6.QtNetwork",
    "mysql.connector",  # O 'MySQLdb' si migraste a mysqlclient
    "fpdf"
]

# Lista de archivos y carpetas de datos que deben ser copiados.
# Formato: ('ruta/origen', 'ruta/destino_en_el_paquete')
files_and_folders_to_include = [
    # --- Archivos de configuración y secretos ---
    # Al pasar solo un string, cx_Freeze busca el archivo en la raíz
    # y lo copia a la raíz del paquete de la aplicación.
    ".env",
    "secret.key",

    # --- Solución para el error OpenThemeData() ---
    # Incluir explícitamente las DLLs de temas de Windows.
    # El formato ('origen', 'destino') asegura que se copien en la carpeta raíz de la aplicación.
    ('C:/Windows/System32/uxtheme.dll', 'uxtheme.dll'),
    ('C:/Windows/System32/dwmapi.dll', 'dwmapi.dll'),

    # --- Forzar la copia completa de las carpetas ---
    # Al usar el formato de tupla, cx_Freeze copia el contenido tal cual,
    # incluyendo subdirectorios (incluso si están vacíos).
    ('reports', 'reports'),
    ('logs', 'logs'),
    ('database', 'database'),
]

# Lista de mdulos a excluir.
modules_to_exclude = [
    "tkinter",
    # --- SOLUCIÓN: Excluir el paquete conflictivo ---
    # Aunque no esté en tu venv, cx_Freeze lo encuentra en otro lugar.
    # Al excluirlo explícitamente, forzamos a que solo se use fpdf2.
    "PyFPDF"
]

# --- No es necesario modificar debajo de esta lnea ---

build_exe_options = {
    "packages": packages_to_include,
    "include_files": files_and_folders_to_include,
    "excludes": modules_to_exclude,
}

# Configuracin para que no se abra una consola en Windows (aplicacin de GUI)
base = "Win32GUI" if sys.platform == "win32" else None
#base = None

setup(
    name=app_name,
    version="1.0",
    description="Sistema Caja Chica",
    options={"build_exe": build_exe_options},
    executables=[Executable(main_script, base=base, target_name=f"{app_name}.exe")]
)
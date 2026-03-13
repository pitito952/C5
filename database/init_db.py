# *************************************************************************************
#
#   Sistema:    C5      -   Módulo de Caja Chica
#   Módulo:     init_db -   Script para crear por primera vez la base de datos y todas
#                           sus tablas.
#                           ¡¡¡ Funciona standalone. !!!
#
# -------------------------------------------------------------------------------------
#  Ver |  Fecha   |     Autor              |   D e s c r i p c i ó n
# -------------------------------------------------------------------------------------
#   01 |07/03/2026| Antigravity/Addy López |Versión Inicial del Programa.
#   02 |07/03/2026| Antigravity/Addy López |Implementación de cifrado de credenciales.
# *************************************************************************************
#
import os
import mysql.connector
from dotenv import load_dotenv
from cryptography.fernet import Fernet

load_dotenv()

def load_key():
    """
    Carga la clave de cifrado desde el archivo 'secret.key' en la raíz del proyecto.
    """
    try:
        root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        key_path = os.path.join(root_dir, "secret.key")
        
        if os.path.exists(key_path):
            with open(key_path, "rb") as key_file:
                return key_file.read()
        else:
            print("ADVERTENCIA: No se encontró 'secret.key'. No se podrá descifrar la contraseña.")
            return None
    except Exception as e:
        print(f"Error cargando la clave de cifrado: {e}")
        return None

def decrypt_password(encrypted_password, key):
    """
    Descifra la contraseña usando la clave cargada.
    Si la contraseña no parece estar cifrada, devuelve el valor original.
    """
    if not key or not encrypted_password:
        return encrypted_password
        
    try:
        f = Fernet(key)
        token = encrypted_password.encode()
        decrypted_bytes = f.decrypt(token)
        return decrypted_bytes.decode()
    except Exception:
        return encrypted_password

def init_db():
    conn = None
    cursor = None
    try:
        key = load_key()
        raw_password = os.getenv("DB_PASSWORD", "")
        db_password = decrypt_password(raw_password, key)
        db_name = os.getenv("DB_DATABASE", "caja_chica_db")

        # --- Paso 1: Conexión inicial para crear la base de datos ---
        print("Conectando al servidor MySQL...")
        conn = mysql.connector.connect(
            host=os.getenv("DB_HOST", "127.0.0.1"),
            user=os.getenv("DB_USER", "root"),
            password=db_password,
            port=int(os.getenv("DB_PORT", 3306))
        )
        cursor = conn.cursor()
        print(f"Creando base de datos '{db_name}' si no existe...")
        cursor.execute(f"CREATE DATABASE IF NOT EXISTS {db_name} CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci")
        conn.commit()
        cursor.close()
        conn.close()
        print("Base de datos asegurada.")

        # --- Paso 2: Conexión a la base de datos específica para crear las tablas ---
        print(f"Conectando a la base de datos '{db_name}'...")
        conn = mysql.connector.connect(
            host=os.getenv("DB_HOST", "127.0.0.1"),
            user=os.getenv("DB_USER", "root"),
            password=db_password,
            port=int(os.getenv("DB_PORT", 3306)),
            database=db_name
        )
        cursor = conn.cursor()
        
        script_path = os.path.join(os.path.dirname(__file__), 'schema.sql')
        
        # --- Lógica de Lectura y Separación de Comandos Mejorada ---
        with open(script_path, 'r', encoding='utf-8') as f:
            clean_script = ''
            for line in f:
                # Ignorar líneas que son solo comentarios
                if not line.strip().startswith('--'):
                    clean_script += line
            # Dividir el script limpio por el delimitador
            sql_commands = [cmd.strip() for cmd in clean_script.split(';') if cmd.strip()]

        print("Ejecutando script para crear tablas...")
        
        for command in sql_commands:
            # El comando 'USE' ya no es necesario porque nos conectamos directamente a la BD
            if command.upper().startswith('USE '):
                continue
            
            try:
                print(f"Ejecutando: {command[:100].strip()}...")
                cursor.execute(command)
            except mysql.connector.Error as err:
                if err.errno == 1050: # Tabla ya existe
                    print(f"Advertencia: {err.msg}")
                else:
                    print(f"Error ejecutando comando: {command[:100]}...\nError: {err}")
                    raise

        conn.commit()
        print("¡Tablas creadas/verificadas exitosamente!")

    except mysql.connector.Error as err:
        print(f"Error de MySQL: {err}")
    except Exception as e:
        print(f"Error general: {e}")
    finally:
        if cursor:
            cursor.close()
        if conn and conn.is_connected():
            conn.close()
        print("Conexión cerrada.")

if __name__ == "__main__":
    confirm = input("¿Estás seguro de que deseas inicializar la base de datos? Esto podría borrar datos existentes. (s/N): ")
    if confirm.lower() == 's':
        init_db()
    else:
        print("Operación cancelada.")

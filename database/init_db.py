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
        # __file__ es .../database/init_db.py -> dirname es .../database -> dirname es .../ (raíz)
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
        # Si falla el descifrado, asumimos que la contraseña estaba en texto plano
        return encrypted_password

def init_db():
    try:
        # Cargar clave y descifrar contraseña
        key = load_key()
        raw_password = os.getenv("DB_PASSWORD", "")
        db_password = decrypt_password(raw_password, key)

        # Conectar a MySQL SIN una base de datos específica para poder crearla
        conn = mysql.connector.connect(
            host=os.getenv("DB_HOST", "127.0.0.1"),
            user=os.getenv("DB_USER", "root"),
            password=db_password, # Usar la contraseña (posiblemente) descifrada
            port=int(os.getenv("DB_PORT", 3306))
        )
        cursor = conn.cursor()
        
        # Leer el archivo schema.sql
        script_path = os.path.join(os.path.dirname(__file__), 'schema.sql')
        with open(script_path, 'r', encoding='utf-8') as f:
            sql_script = f.read()

        print("Ejecutando script de configuración de la base de datos...")
        
        # Ejecutar los comandos del script uno por uno
        for result in cursor.execute(sql_script, multi=True):
            if result.with_rows:
                print(f"Resultado de la consulta: {result.fetchall()}")
        
        conn.commit()
        print("¡Base de datos 'caja_chica_db' y sus tablas creadas exitosamente!")

    except mysql.connector.Error as err:
        print(f"Error de MySQL: {err}")
    except Exception as e:
        print(f"Error general: {e}")
    finally:
        if 'cursor' in locals() and cursor:
            cursor.close()
        if 'conn' in locals() and conn.is_connected():
            conn.close()

if __name__ == "__main__":
    # Preguntar al usuario para evitar ejecuciones accidentales
    confirm = input("¿Estás seguro de que deseas inicializar la base de datos? Esto podría borrar datos existentes. (s/N): ")
    if confirm.lower() == 's':
        init_db()
    else:
        print("Operación cancelada.")

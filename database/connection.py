# *****************************************************************************
#
#   Sistema:    C5          -   Módulo de Caja Chica
#   Módulo:     connection  -   Script de Concexión a la Base de Datos
#
# -----------------------------------------------------------------------------
#  Ver |  Fecha   |     Autor              |   D e s c r i p c i ó n
# -----------------------------------------------------------------------------
#   01 |07/03/2026| Antigravity/Addy López |Versión Inicial del Programa.
#   02 |07/03/2026| Antigravity/Addy López |Implementación de cifrado de credenciales.
#   03 |07/03/2026| Antigravity/Addy López |Implementación de Sistema de Logs.
# *****************************************************************************
#
import os
import sys
import mysql.connector
import logging
from dotenv import load_dotenv
from cryptography.fernet import Fernet

def get_base_path():
    """Obtiene la ruta base para los archivos, compatible con cx_Freeze."""
    if getattr(sys, 'frozen', False):
        # Si la aplicación está "congelada", la base es el directorio del ejecutable
        return os.path.dirname(sys.executable)
    else:
        # Si se ejecuta como script normal, la base es el directorio raíz del proyecto
        return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

BASE_PATH = get_base_path()
load_dotenv(dotenv_path=os.path.join(BASE_PATH, ".env"))

class DatabaseConnection:
    _instance = None
    _connection = None
    _key = None

    def __new__(cls):
        """Implementar el patrón Singleton. Asegura que solo exista una única instancia de
           DatabaseConnection en toda la aplicación."""
        if cls._instance is None:
            cls._instance = super(DatabaseConnection, cls).__new__(cls)
            cls._instance._load_key()
            # La conexión no se inicia aquí para permitir la verificación de la BD primero
        return cls._instance

    def _load_key(self):
        """
        Carga la clave de cifrado desde el archivo 'secret.key' en la raíz del proyecto.
        """
        try:
            key_path = os.path.join(BASE_PATH, "secret.key")
            
            if os.path.exists(key_path):
                with open(key_path, "rb") as key_file:
                    self._key = key_file.read()
            else:
                self._key = os.getenv("ENCRYPTION_KEY")
                
            if not self._key:
                logging.warning("[CONNECTION] No se encontró 'secret.key' ni la variable 'ENCRYPTION_KEY'.")
        except Exception as e:
            logging.error(f"[CONNECTION] Error cargando la clave de cifrado: {e}")

    def _decrypt_password(self, encrypted_password):
        """
        Descifra la contraseña usando la clave cargada.
        """
        if not self._key or not encrypted_password:
            return encrypted_password
            
        try:
            f = Fernet(self._key)
            token = encrypted_password.encode()
            decrypted_bytes = f.decrypt(token)
            return decrypted_bytes.decode()
        except Exception:
            return encrypted_password

    def _connect(self, db_name=None):
        """ Intenta establecer una conexión con la base de datos."""
        try:
            raw_password = os.getenv("DB_PASSWORD", "")
            db_password = self._decrypt_password(raw_password)

            self._connection = mysql.connector.connect(
                host=os.getenv("DB_HOST", "localhost"),
                user=os.getenv("DB_USER", "root"),
                password=db_password,
                database=db_name or os.getenv("DB_NAME", "caja_chica_db"),
                port=int(os.getenv("DB_PORT", 3306))
            )
            logging.info(f"[CONNECTION] Conexión exitosa a '{db_name or os.getenv('DB_NAME')}'.")
        except mysql.connector.Error as err:
            logging.error(f"[CONNECTION] Error conectando a MySQL: {err}")
            self._connection = None

    def check_database_exists(self):
        """Verifica si la base de datos principal existe en el servidor."""
        conn = None
        cursor = None
        try:
            raw_password = os.getenv("DB_PASSWORD", "")
            db_password = self._decrypt_password(raw_password)
            db_name = os.getenv("DB_NAME", "caja_chica_db")

            conn = mysql.connector.connect(
                host=os.getenv("DB_HOST", "localhost"),
                user=os.getenv("DB_USER", "root"),
                password=db_password,
                port=int(os.getenv("DB_PORT", 3306))
            )
            cursor = conn.cursor()
            cursor.execute("SHOW DATABASES")
            databases = [db[0] for db in cursor.fetchall()]
            return db_name in databases
        except mysql.connector.Error as err:
            logging.error(f"[CONNECTION_CHECK] Error al verificar la base de datos: {err}")
            return False
        finally:
            if cursor:
                cursor.close()
            if conn and conn.is_connected():
                conn.close()

    def get_connection(self):
        """Obtiene una conexión a la base de datos, creándola si no existe."""
        if self._connection is None or not self._connection.is_connected():
            self._connect()
        return self._connection

    def execute_query(self, query, params=None):
        """Método principal para interactuar con la base de datos."""
        conn = self.get_connection()
        if not conn:
            logging.error("[CONNECTION] No se pudo obtener una conexión válida para ejecutar la consulta.")
            return None
        
        cursor = conn.cursor(dictionary=True)
        try:
            cursor.execute(query, params or ())
            if query.strip().upper().startswith("SELECT"):
                result = cursor.fetchall()
            else:
                conn.commit()
                result = cursor.lastrowid
            return result
        except mysql.connector.Error as err:
            logging.error(f"[CONNECTION] Error ejecutando query: {query}. Error: {err}")
            if not query.strip().upper().startswith("SELECT"):
                conn.rollback()
            return None
        finally:
            cursor.close()

# Provide a simple test function when running this module directly
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)

    db_checker = DatabaseConnection()
    if db_checker.check_database_exists():
        print("Prueba de Verificación: La base de datos existe.")
        db = DatabaseConnection()
        conn = db.get_connection()
        if conn and conn.is_connected():
            print("Prueba de Conexión: OK")
        else:
            print("Prueba de Conexión: FALLIDA.")
    else:
        print("Prueba de Verificación: La base de datos NO existe.")

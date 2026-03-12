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
           DatabaseConnection en toda la aplicación. Si no existe, la crea y llama a _connect()."""
        if cls._instance is None:
            cls._instance = super(DatabaseConnection, cls).__new__(cls)
            cls._instance._load_key()
            cls._instance._connect()
        return cls._instance

    def _load_key(self):
        """
        Carga la clave de cifrado desde el archivo 'secret.key' en la raíz del proyecto.
        Si no existe, intenta usar una variable de entorno o lanza un error.
        """
        try:
            # Asumimos que secret.key está en la raíz del proyecto, un nivel arriba de database/
            key_path = os.path.join(BASE_PATH, "secret.key")
            
            if os.path.exists(key_path):
                with open(key_path, "rb") as key_file:
                    self._key = key_file.read()
            else:
                # Fallback: Intentar leer la clave desde una variable de entorno (útil para producción/docker)
                self._key = os.getenv("ENCRYPTION_KEY")
                
            if not self._key:
                logging.warning("[CONNECTION] No se encontró 'secret.key' ni la variable 'ENCRYPTION_KEY'. La conexión fallará si la contraseña está cifrada.")
        except Exception as e:
            logging.error(f"[CONNECTION] Error cargando la clave de cifrado: {e}")

    def _decrypt_password(self, encrypted_password):
        """
        Descifra la contraseña usando la clave cargada.
        Si la contraseña no parece estar cifrada (no es bytes o falla el descifrado), devuelve el original.
        """
        if not self._key or not encrypted_password:
            return encrypted_password
            
        try:
            f = Fernet(self._key)
            # Si la contraseña en .env es string, la convertimos a bytes para Fernet
            if isinstance(encrypted_password, str):
                # Fernet token debe ser bytes
                token = encrypted_password.encode()
            else:
                token = encrypted_password
                
            decrypted_bytes = f.decrypt(token)
            return decrypted_bytes.decode()
        except Exception as e:
            # Si falla el descifrado (ej. token inválido), asumimos que la contraseña estaba en texto plano
            # logging.debug(f"[CONNECTION] La contraseña no estaba cifrada o la clave es incorrecta. Usando valor original.")
            return encrypted_password

    def _connect(self):
        """ Intenta establecer una conexión con la base de datos usando los parámetros obtenidos
            de las variables de entorno (os.getenv). Si falla, captura la excepción y muestra el error."""
        try:
            # Obtener contraseña cruda del .env
            raw_password = os.getenv("DB_PASSWORD", "")
            
            # Intentar descifrarla (si es texto plano, _decrypt_password la devolverá tal cual)
            db_password = self._decrypt_password(raw_password)

            self._connection = mysql.connector.connect(
                host=os.getenv("DB_HOST", "localhost"),
                user=os.getenv("DB_USER", "root"),
                password=db_password,
                database=os.getenv("DB_NAME", "caja_chica_db"),
                port=int(os.getenv("DB_PORT", 3306))
            )
            logging.info("[CONNECTION] Conexión exitosa a la base de datos.")
        except mysql.connector.Error as err:
            logging.error(f"[CONNECTION] Error conectando a MySQL: {err}")
            self._connection = None

    def get_connection(self):
        """Verifica si la conexión actual está activa (is_connected()). Si no lo está, intenta
           reconectar llamando a _connect(). Devuelve el objeto de conexión."""
        # Reconnect if connection was lost
        if self._connection and not self._connection.is_connected():
            logging.warning("[CONNECTION] Conexión perdida. Intentando reconectar...")
            self._connect()
        return self._connection

    def execute_query(self, query, params=None):
        """Método principal para interactuar con la base de datos.
            .- Obtiene la conexión y crea un cursor (configurado para devolver resultados como diccionarios.
            .- Ejecuta la consulta SQL (query) con los parámetros opcionales (params).
            .- Si es un SELECT: Devuelve todos los registros encontrados (fetchall()).
            .- Si es otra operación (INSERT, UPDATE, DELETE): Hace commit() para guardar los cambios y
               devuelve el ID de la última fila insertada (lastrowid).
            .- Maneja errores y realiza un rollback() si algo falla en operaciones de escritura.
            .- Finalmente, cierra el cursor."""

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
    # Configuración básica de logging para pruebas directas
    logging.basicConfig(level=logging.INFO)

    db = DatabaseConnection()
    conn = db.get_connection()
    if conn and conn.is_connected():
        print("Test Connection: OK")
    else:
        print("Test Connection: FAILED. Please check MySQL server and .env settings.")

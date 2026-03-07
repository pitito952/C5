from cryptography.fernet import Fernet
import os
from dotenv import load_dotenv

# Cargar variables de entorno actuales
load_dotenv()

def get_key_path():
    """
    Calcula la ruta absoluta al archivo secret.key en la raíz del proyecto.
    """
    # __file__ es la ruta de este script (.../C5/utils/encrypt_credentials.py)
    # dirname 1 -> .../C5/utils
    # dirname 2 -> .../C5 (Raíz del proyecto)
    root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(root_dir, "secret.key")

def generate_key():
    """
    Genera una clave de cifrado y la guarda en el archivo 'secret.key'
    en el directorio raíz del proyecto.
    """
    key = Fernet.generate_key()
    key_path = get_key_path()
    
    try:
        with open(key_path, "wb") as key_file:
            key_file.write(key)
        print(f"Clave generada y guardada en: {key_path}")
    except Exception as e:
        print(f"Error al guardar la clave: {e}")

def load_key():
    """
    Carga la clave de cifrado desde el archivo 'secret.key'.
    """
    return open(get_key_path(), "rb").read()

def encrypt_password(password):
    """
    Cifra una contraseña usando la clave almacenada.
    """
    key = load_key()
    f = Fernet(key)
    encrypted_password = f.encrypt(password.encode())
    return encrypted_password

if __name__ == "__main__":
    key_path = get_key_path()
    
    # 1. Generar la clave si no existe
    if not os.path.exists(key_path):
        print("Generando nueva clave de cifrado...")
        generate_key()
    else:
        print(f"Usando clave existente en: {key_path}")
    
    # 2. Obtener la contraseña actual del .env (o pedirla al usuario)
    current_password = os.getenv("DB_PASSWORD")
    if not current_password:
        current_password = input("Introduce la contraseña de la base de datos a cifrar: ")
    
    # 3. Cifrar la contraseña
    try:
        encrypted_pwd = encrypt_password(current_password)
        
        print(f"\n--- Credenciales Cifradas ---")
        print(f"Contraseña Original: {current_password}")
        print(f"Contraseña Cifrada (copia TODO esto en tu .env):")
        print(f"{encrypted_pwd.decode()}")
        print("-----------------------------")
    except Exception as e:
        print(f"Ocurrió un error al cifrar: {e}")

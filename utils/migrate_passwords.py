import sys
import os
import bcrypt
import logging

# Configuración básica de logging para este script
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Añadir el directorio raíz al path para poder importar database.connection
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.connection import DatabaseConnection

def migrate_passwords():
    logging.info("[MIGRATE_PASSWORDS] Iniciando migración de contraseñas a bcrypt...")
    
    db = DatabaseConnection()
    conn = db.get_connection()
    
    if not conn:
        logging.error("[MIGRATE_PASSWORDS] Error: No se pudo conectar a la base de datos.")
        return

    try:
        # 1. Obtener todos los usuarios
        query_select = "SELECT id, username, password_hash FROM usuarios"
        usuarios = db.execute_query(query_select)
        
        if not usuarios:
            logging.info("[MIGRATE_PASSWORDS] No se encontraron usuarios para migrar.")
            return

        logging.info(f"[MIGRATE_PASSWORDS] Se encontraron {len(usuarios)} usuarios. Procesando...")
        
        count = 0
        for usuario in usuarios:
            uid = usuario['id']
            username = usuario['username']
            current_pwd = usuario['password_hash'] # Asumimos que esto es texto plano
            
            # Verificar si ya parece ser un hash de bcrypt (empieza con $2b$, $2a$ o $2y$)
            if current_pwd and (current_pwd.startswith('$2b$') or current_pwd.startswith('$2a$') or current_pwd.startswith('$2y$')):
                logging.info(f"[MIGRATE_PASSWORDS] Usuario '{username}' (ID: {uid}) ya tiene contraseña hasheada. Saltando.")
                continue
                
            if not current_pwd:
                logging.warning(f"[MIGRATE_PASSWORDS] Usuario '{username}' (ID: {uid}) no tiene contraseña. Saltando.")
                continue

            # 2. Generar hash bcrypt
            # bcrypt.hashpw espera bytes, así que codificamos el string
            salt = bcrypt.gensalt()
            hashed_pwd = bcrypt.hashpw(current_pwd.encode('utf-8'), salt)
            
            # 3. Actualizar en la base de datos
            # Guardamos el hash como string decodificado
            query_update = "UPDATE usuarios SET password_hash = %s WHERE id = %s"
            db.execute_query(query_update, (hashed_pwd.decode('utf-8'), uid))
            
            logging.info(f"[MIGRATE_PASSWORDS] Usuario '{username}' (ID: {uid}): Contraseña migrada exitosamente.")
            count += 1
            
        logging.info(f"[MIGRATE_PASSWORDS] Migración completada. {count} usuarios actualizados.")
        
    except Exception as e:
        logging.error(f"[MIGRATE_PASSWORDS] Ocurrió un error durante la migración: {e}", exc_info=True)

if __name__ == "__main__":
    migrate_passwords()

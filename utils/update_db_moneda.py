import sys
import os
import logging

# Configuración básica de logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Añadir el directorio raíz al path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.connection import DatabaseConnection

def update_database():
    logging.info("Iniciando actualización de la tabla 'parametros_control'...")
    
    db = DatabaseConnection()
    conn = db.get_connection()
    
    if not conn:
        logging.error("No se pudo conectar a la base de datos.")
        return

    try:
        # Verificar si las columnas ya existen para evitar errores
        check_query = "SHOW COLUMNS FROM parametros_control LIKE 'simbolo_moneda'"
        result = db.execute_query(check_query)
        
        if not result:
            # Agregar columnas
            alter_query = """
                ALTER TABLE parametros_control
                ADD COLUMN simbolo_moneda VARCHAR(5) DEFAULT '$',
                ADD COLUMN nombre_moneda VARCHAR(50) DEFAULT 'Peso',
                ADD COLUMN tasa_cambio DECIMAL(10,4) DEFAULT 1.0000;
            """
            db.execute_query(alter_query)
            logging.info("Columnas agregadas exitosamente.")
        else:
            logging.info("Las columnas ya existen. No se requieren cambios.")
            
    except Exception as e:
        logging.error(f"Error durante la actualización: {e}")

if __name__ == "__main__":
    update_database()

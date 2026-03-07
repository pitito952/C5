import os
from connection import DatabaseConnection

def apply_migration_v5_1():
    db = DatabaseConnection()
    conn = db.get_connection()
    
    if not conn or not conn.is_connected():
        print("Error al conectar con la base de datos.")
        return

    script_path = os.path.join(os.path.dirname(__file__), 'migrate_v5_1.sql')
    if not os.path.exists(script_path):
        print("No se encontró el archivo migrate_v5_1.sql")
        return
        
    with open(script_path, 'r', encoding='utf-8') as f:
        sql_script = f.read()

    print("Ejecutando parche V5.1...")
    cursor = conn.cursor()
    
    try:
        statements = sql_script.split(';')
        for statement in statements:
            if statement.strip():
                try:
                    cursor.execute(statement)
                except Exception as ex:
                    if "1060" in str(ex):
                        print(f"La columna ya existe. Omitiendo: {statement[:50]}...")
                    else:
                        raise ex
                        
        conn.commit()
        print("¡Parche V5.1 aplicado correctamente!")
        
    except Exception as e:
        print(f"Error fatal durante el parcheamiento: {e}")
        conn.rollback()
    finally:
        cursor.close()

if __name__ == "__main__":
    apply_migration_v5_1()

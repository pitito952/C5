import os
from connection import DatabaseConnection

def apply_migration():
    db = DatabaseConnection()
    conn = db.get_connection()
    
    if not conn or not conn.is_connected():
        print("Error al conectar con la base de datos.")
        return

    script_path = os.path.join(os.path.dirname(__file__), 'migrate_v5.sql')
    if not os.path.exists(script_path):
        print("No se encontró el archivo migrate_v5.sql")
        return
        
    with open(script_path, 'r', encoding='utf-8') as f:
        sql_script = f.read()

    print("Ejecutando migración V5...")
    cursor = conn.cursor()
    
    try:
        # Some ALTER TABLE clauses cannot be batched easily with others without error handling.
        # So we split and ignore Duplicate Column errors (Error 1060).
        statements = sql_script.split(';')
        for statement in statements:
            if statement.strip():
                try:
                    cursor.execute(statement)
                except Exception as ex:
                    # Ignore "Duplicate column name" in case we run it twice
                    if "1060" in str(ex):
                        print(f"La columna ya existe. Omitiendo: {statement[:50]}...")
                    # Ignore duplicate foreign keys
                    elif "1061" in str(ex) or "1050" in str(ex):
                         print(f"Llave u objeto ya existe. Omitiendo: {statement[:50]}...")
                    else:
                        raise ex
                        
        conn.commit()
        print("¡Migración V5 aplicada correctamente!")
        
    except Exception as e:
        print(f"Error fatal durante la migración: {e}")
        conn.rollback()
    finally:
        cursor.close()

if __name__ == "__main__":
    apply_migration()

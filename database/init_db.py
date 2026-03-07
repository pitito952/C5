import os
import mysql.connector
from dotenv import load_dotenv

load_dotenv()

def init_db():
    try:
        # Connect to MySQL WITHOUT a specific database first to create it
        conn = mysql.connector.connect(
            host=os.getenv("DB_HOST", "127.0.0.1"),
            user=os.getenv("DB_USER", "root"),
            password=os.getenv("DB_PASSWORD", ""),
            port=int(os.getenv("DB_PORT", 3306))
        )
        cursor = conn.cursor()
        
        # Read the schema file
        script_path = os.path.join(os.path.dirname(__file__), 'schema.sql')
        with open(script_path, 'r', encoding='utf-8') as f:
            sql_script = f.read()

        print("Executing database setup script...")
        
        # We need to execute statements one by one.
        # Simple split by ';' works for this basic script, but we must ignore empty statements
        # and be careful with comments that might contain semicolons (though our schema is clean).
        # A more robust way is using the multi=True flag in execute().
        
        # Slicing the script to execute command by command
        statements = sql_script.split(';')
        for statement in statements:
            if statement.strip():
                cursor.execute(statement)
                
        conn.commit()
        print("Database caja_chica_db and tables created successfully!")

    except mysql.connector.Error as err:
        print(f"MySQL Error: {err}")
    except Exception as e:
        print(f"Error: {e}")
    finally:
        if 'cursor' in locals() and cursor:
            cursor.close()
        if 'conn' in locals() and conn.is_connected():
            conn.close()

if __name__ == "__main__":
    init_db()

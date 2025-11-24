"""
Generate SQL dump of HelpHand database
Shows the complete database structure and data
"""

import sqlite3

def dump_database():
    """Create a readable SQL dump of the entire database"""
    
    db_path = 'instance/helphand.db'
    conn = sqlite3.connect(db_path)
    
    print("-- ================================================")
    print("-- HELPHAND DATABASE SQL DUMP")
    print("-- Generated: 2025-11-22")
    print("-- Database: instance/helphand.db")
    print("-- ================================================\n")
    
    # Get database schema
    print("-- DATABASE SCHEMA")
    print("-- ================================================\n")
    
    cursor = conn.cursor()
    cursor.execute("SELECT sql FROM sqlite_master WHERE type='table' ORDER BY name")
    tables = cursor.fetchall()
    
    for table_sql in tables:
        if table_sql[0]:
            print(table_sql[0] + ";\n")
    
    # Get all data from each table
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
    table_names = cursor.fetchall()
    
    print("\n-- DATABASE DATA")
    print("-- ================================================\n")
    
    for (table_name,) in table_names:
        print(f"\n-- TABLE: {table_name}")
        print("-" * 60)
        
        # Get column names
        cursor.execute(f"PRAGMA table_info({table_name})")
        columns = [col[1] for col in cursor.fetchall()]
        
        # Get data
        cursor.execute(f"SELECT * FROM {table_name}")
        rows = cursor.fetchall()
        
        if rows:
            print(f"-- {len(rows)} records\n")
            for row in rows:
                values = []
                for val in row:
                    if val is None:
                        values.append("NULL")
                    elif isinstance(val, str):
                        # Escape single quotes
                        escaped = val.replace("'", "''")
                        values.append(f"'{escaped}'")
                    else:
                        values.append(str(val))
                
                print(f"INSERT INTO {table_name} ({', '.join(columns)}) VALUES ({', '.join(values)});")
            print()
        else:
            print(f"-- No records\n")
    
    conn.close()
    
    print("\n-- ================================================")
    print("-- END OF SQL DUMP")
    print("-- ================================================")

if __name__ == '__main__':
    dump_database()

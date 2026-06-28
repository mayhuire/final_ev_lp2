import sqlite3

# Crear/conectar a una base de datos (archivo .db)
conn = sqlite3.connect("datos.db")
cursor = conn.cursor()

# Crear una tabla
cursor.execute("""
    CREATE TABLE IF NOT EXISTS fact_checks (
        id INTEGER PRIMARY KEY,
        claim TEXT,
        rating TEXT,
        origin_domain TEXT
    )
""")

# Insertar datos
cursor.execute("INSERT INTO fact_checks (claim, rating, origin_domain) VALUES (?, ?, ?)",
               ("Tomate cura cáncer", "False", "medicinanatural.com"))
conn.commit()

# Consultar
cursor.execute("SELECT * FROM fact_checks")
rows = cursor.fetchall()
for row in rows:
    print(row)

conn.close()
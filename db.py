# init_db.py
import sqlite3

print("Initializing database...")

# Connect to the database (this will create the file if it doesn't exist)
connection = sqlite3.connect('audit.db')
cursor = connection.cursor()

# --- Create the 'batches' table ---
cursor.execute('''
CREATE TABLE IF NOT EXISTS batches (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    merkle_root TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
''')
print("Table 'batches' created successfully.")

# --- Create the 'logs' table ---
cursor.execute('''
CREATE TABLE IF NOT EXISTS logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    log_data TEXT NOT NULL,
    leaf_hash TEXT,
    proof TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    batch_id INTEGER,
    FOREIGN KEY (batch_id) REFERENCES batches (id)
)
''')
print("Table 'logs' created successfully.")


# Commit the changes and close the connection
connection.commit()
connection.close()

print("Database initialization complete.")
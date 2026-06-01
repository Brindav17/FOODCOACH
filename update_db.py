import sqlite3

# Connect to your database
conn = sqlite3.connect('database.db')
c = conn.cursor()

# List of new columns to add
new_columns = {
    "dob": "TEXT",
    "weight": "REAL",
    "height": "REAL",
    "goal": "TEXT"
}

# Add columns if they don't exist
for column, col_type in new_columns.items():
    try:
        c.execute(f"ALTER TABLE users ADD COLUMN {column} {col_type}")
        print(f"Added column: {column}")
    except sqlite3.OperationalError:
        print(f"Column {column} already exists, skipping.")

conn.commit()
conn.close()
print("All done!")

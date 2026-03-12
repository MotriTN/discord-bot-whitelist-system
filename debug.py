import sqlite3
import sys

def main():
    conn = sqlite3.connect('lineage.db')
    conn.row_factory = sqlite3.Row
    users = conn.execute('SELECT id, trust_charges FROM users').fetchall()
    
    for user in users:
        print(f"User ID: {user['id']}, Trust Charges: {user['trust_charges']}")
        
    conn.close()

if __name__ == "__main__":
    main()

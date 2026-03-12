import sqlite3
import datetime

def main():
    conn = sqlite3.connect('lineage.db')
    conn.row_factory = sqlite3.Row
    users = conn.execute('SELECT id, trust_charges, last_reset_month FROM users').fetchall()
    
    current_month = datetime.datetime.now().month
    
    for user in users:
        print(f"User ID: {user['id']}, Trust Charges: {user['trust_charges']}, Last Reset Month: {user['last_reset_month']}, Current Month: {current_month}")
        
    conn.close()

if __name__ == "__main__":
    main()

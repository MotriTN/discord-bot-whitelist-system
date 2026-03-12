import sqlite3

def main():
    conn = sqlite3.connect('lineage.db')
    conn.row_factory = sqlite3.Row
    
    users = conn.execute('SELECT id FROM users').fetchall()
    
    for user_row in users:
        uid = user_row['id']
        
        # Calculate active trusts
        active_trusts = conn.execute('SELECT COUNT(*) as count FROM trusts WHERE truster_id=? AND active=1', (uid,)).fetchone()['count']
        new_trust_charges = max(0, 2 - active_trusts)
        
        # Calculate active reports
        active_reports = conn.execute('SELECT COUNT(*) as count FROM reports WHERE reporter_id=? AND active=1', (uid,)).fetchone()['count']
        new_report_charges = max(0, 2 - active_reports)
        
        # Update user
        conn.execute('UPDATE users SET trust_charges=?, report_charges=? WHERE id=?', (new_trust_charges, new_report_charges, uid))
        print(f"Updated user {uid}: Trusts {new_trust_charges}, Reports {new_report_charges}")
        
    conn.commit()
    conn.close()

if __name__ == "__main__":
    main()

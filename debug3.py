import sqlite3

def main():
    conn = sqlite3.connect('lineage.db')
    conn.row_factory = sqlite3.Row
    trusts = conn.execute('SELECT * FROM trusts WHERE truster_id=483589784879497236').fetchall()
    
    for t in trusts:
        print(dict(t))
        
    conn.close()

if __name__ == "__main__":
    main()

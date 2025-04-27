#!/usr/bin/env python3
import sqlite3

def init_db():
    conn = sqlite3.connect("ospf_config.db")
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS ospf (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            router TEXT,
            username TEXT,
            password TEXT,
            ospf_process TEXT,
            ospf_area TEXT,
            loopback TEXT
        )
    ''')
    conn.commit()
    conn.close()

if __name__ == "__main__":
    init_db()

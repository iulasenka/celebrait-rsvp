#!/usr/bin/env python3
import os
import sqlite3
import sys


def migrate_database(database_path: str):
    print(f"Migrating database: {database_path}")
    
    if not os.path.exists(database_path):
        print(f"Database does not exist at {database_path}. No migration needed.")
        return
    
    conn = sqlite3.connect(database_path)
    cursor = conn.cursor()
    
    cursor.execute("PRAGMA table_info(invitations)")
    columns = [row[1] for row in cursor.fetchall()]
    
    needs_user_id = "user_id" not in columns
    needs_deleted_at = "deleted_at" not in columns
    
    if needs_user_id or needs_deleted_at:
        print("Schema migration required.")
        
        if needs_user_id:
            print("Adding user_id column...")
            cursor.execute("ALTER TABLE invitations ADD COLUMN user_id TEXT DEFAULT 'legacy-user'")
            cursor.execute("UPDATE invitations SET user_id = 'legacy-user-' || owner_email WHERE user_id IS NULL")
            cursor.execute("CREATE INDEX IF NOT EXISTS invitations_user_id_idx ON invitations(user_id)")
        
        if needs_deleted_at:
            print("Adding deleted_at column...")
            cursor.execute("ALTER TABLE invitations ADD COLUMN deleted_at TEXT")
        
        conn.commit()
        print("Migration completed successfully.")
    else:
        print("Database schema is up to date. No migration needed.")
    
    conn.close()


if __name__ == "__main__":
    database_path = os.getenv("RSVP_DATABASE_PATH", "data/celebrait.db")
    
    if len(sys.argv) > 1:
        database_path = sys.argv[1]
    
    migrate_database(database_path)

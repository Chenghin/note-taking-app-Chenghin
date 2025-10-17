"""
SQLite to Supabase Migration Script

This script migrates data from the existing SQLite database to Supabase PostgreSQL.
Run this after setting up your Supabase project and tables.

Prerequisites:
1. Create Supabase project
2. Run the table creation SQL in Supabase
3. Set SUPABASE_URL and SUPABASE_ANON_KEY (or SERVICE_ROLE_KEY) in .env
4. Ensure the app is using the new Supabase models
"""

import os
import sqlite3
import json
from datetime import datetime
from src.config import supabase

# Path to the existing SQLite database
SQLITE_DB_PATH = os.path.join("database", "app.db")

def migrate_users():
    """Migrate users from SQLite to Supabase"""
    print("Migrating users...")
    
    # Check if SQLite DB exists
    if not os.path.exists(SQLITE_DB_PATH):
        print(f"SQLite database not found at {SQLITE_DB_PATH}")
        return
    
    # Connect to SQLite
    conn = sqlite3.connect(SQLITE_DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    try:
        # Get all users from SQLite
        cursor.execute("SELECT * FROM user")
        users = cursor.fetchall()
        
        if not users:
            print("No users found to migrate")
            return
        
        # Convert to list of dicts
        user_data = []
        for user in users:
            user_dict = {
                'username': user['username'],
                'email': user['email'],
                'created_at': datetime.utcnow().isoformat(),
                'updated_at': datetime.utcnow().isoformat()
            }
            user_data.append(user_dict)
        
        # Insert into Supabase
        result = supabase.table('users').insert(user_data).execute()
        print(f"Successfully migrated {len(user_data)} users")
        
    except sqlite3.Error as e:
        print(f"SQLite error: {e}")
    except Exception as e:
        print(f"Error migrating users: {e}")
    finally:
        conn.close()

def migrate_notes():
    """Migrate notes from SQLite to Supabase"""
    print("Migrating notes...")
    
    # Check if SQLite DB exists
    if not os.path.exists(SQLITE_DB_PATH):
        print(f"SQLite database not found at {SQLITE_DB_PATH}")
        return
    
    # Connect to SQLite
    conn = sqlite3.connect(SQLITE_DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    try:
        # Get all notes from SQLite
        cursor.execute("SELECT * FROM note")
        notes = cursor.fetchall()
        
        if not notes:
            print("No notes found to migrate")
            return
        
        # Convert to list of dicts
        note_data = []
        for note in notes:
            # Handle tags - convert from JSON string to proper format
            tags = None
            if note['tags']:
                try:
                    tags = json.loads(note['tags'])
                except:
                    # If not valid JSON, treat as comma-separated string
                    tags = [tag.strip() for tag in note['tags'].split(',') if tag.strip()]
            
            note_dict = {
                'title': note['title'],
                'content': note['content'],
                'order': note.get('order', 0),
                'tags': json.dumps(tags) if tags else None,
                'event_date': note.get('event_date'),
                'event_time': note.get('event_time'),
                'created_at': note['created_at'] if note.get('created_at') else datetime.utcnow().isoformat(),
                'updated_at': note['updated_at'] if note.get('updated_at') else datetime.utcnow().isoformat()
            }
            note_data.append(note_dict)
        
        # Insert into Supabase in batches
        batch_size = 100
        for i in range(0, len(note_data), batch_size):
            batch = note_data[i:i + batch_size]
            result = supabase.table('notes').insert(batch).execute()
            print(f"Migrated batch {i//batch_size + 1}: {len(batch)} notes")
        
        print(f"Successfully migrated {len(note_data)} notes")
        
    except sqlite3.Error as e:
        print(f"SQLite error: {e}")
    except Exception as e:
        print(f"Error migrating notes: {e}")
    finally:
        conn.close()

def verify_migration():
    """Verify the migration by counting records in Supabase"""
    print("\nVerifying migration...")
    
    try:
        # Count users
        user_result = supabase.table('users').select('id').execute()
        user_count = len(user_result.data)
        print(f"Users in Supabase: {user_count}")
        
        # Count notes
        note_result = supabase.table('notes').select('id').execute()
        note_count = len(note_result.data)
        print(f"Notes in Supabase: {note_count}")
        
    except Exception as e:
        print(f"Error verifying migration: {e}")

if __name__ == "__main__":
    print("Starting SQLite to Supabase migration...")
    print("Make sure you have:")
    print("1. Created your Supabase project")
    print("2. Created the tables (users, notes) in Supabase")
    print("3. Set SUPABASE_URL and SUPABASE_ANON_KEY in .env")
    print()
    
    # Test Supabase connection
    try:
        test_result = supabase.table('users').select('id').limit(1).execute()
        print("✓ Supabase connection successful")
    except Exception as e:
        print(f"✗ Supabase connection failed: {e}")
        print("Please check your configuration and try again.")
        exit(1)
    
    # Run migration
    migrate_users()
    migrate_notes()
    verify_migration()
    
    print("\nMigration completed!")
    print("You can now test your app with the new Supabase backend.")
"""v2 migration: add new columns to existing tables"""
import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(__file__), "memorial.db")


def col_exists(cursor, table, column):
    cursor.execute(f"PRAGMA table_info({table})")
    return any(row[1] == column for row in cursor.fetchall())


def add_col(cursor, table, column, definition):
    if not col_exists(cursor, table, column):
        cursor.execute(f"ALTER TABLE {table} ADD COLUMN {column} {definition}")
        print(f"  + {table}.{column}")
    else:
        print(f"  = {table}.{column} (already exists)")


conn = sqlite3.connect(DB_PATH)
c = conn.cursor()

print("=== users ===")
add_col(c, "users", "last_login_at", "DATETIME")
add_col(c, "users", "totp_secret", "VARCHAR")
add_col(c, "users", "totp_enabled", "BOOLEAN DEFAULT 0")
add_col(c, "users", "font_size", "VARCHAR DEFAULT 'medium'")
add_col(c, "users", "simple_mode", "BOOLEAN DEFAULT 0")

print("=== family_members ===")
add_col(c, "family_members", "personal_message", "TEXT")

print("=== assets ===")
add_col(c, "assets", "property_registration_no", "VARCHAR")
add_col(c, "assets", "fixed_asset_tax_value", "INTEGER")
add_col(c, "assets", "is_farmland", "BOOLEAN DEFAULT 0")
add_col(c, "assets", "location_address", "VARCHAR")
add_col(c, "assets", "policy_number", "VARCHAR")
add_col(c, "assets", "insurance_company", "VARCHAR")
add_col(c, "assets", "beneficiary", "VARCHAR")

print("=== ending_notes ===")
add_col(c, "ending_notes", "funeral_flower_type", "VARCHAR")
add_col(c, "ending_notes", "kaimyo_preference", "TEXT")
add_col(c, "ending_notes", "funeral_guest_limit", "INTEGER")
add_col(c, "ending_notes", "burial_preference", "VARCHAR")
add_col(c, "ending_notes", "favorite_music", "TEXT")
add_col(c, "ending_notes", "favorite_movies", "TEXT")
add_col(c, "ending_notes", "favorite_foods", "TEXT")

print("=== pets ===")
add_col(c, "pets", "breed", "VARCHAR")
add_col(c, "pets", "birth_year", "INTEGER")
add_col(c, "pets", "microchip_no", "VARCHAR")
add_col(c, "pets", "vaccine_info", "TEXT")
add_col(c, "pets", "vet_name", "VARCHAR")
add_col(c, "pets", "vet_phone", "VARCHAR")
add_col(c, "pets", "caretaker_phone", "VARCHAR")

print("=== digital_keys ===")
add_col(c, "digital_keys", "deadman_enabled", "BOOLEAN DEFAULT 0")
add_col(c, "digital_keys", "deadman_interval_days", "INTEGER DEFAULT 90")
add_col(c, "digital_keys", "last_checkin_at", "DATETIME")

print("=== memorial_media ===")
add_col(c, "memorial_media", "album_name", "VARCHAR DEFAULT 'メイン'")
add_col(c, "memorial_media", "taken_at", "VARCHAR")
add_col(c, "memorial_media", "location", "VARCHAR")
add_col(c, "memorial_media", "episode", "TEXT")
add_col(c, "memorial_media", "media_is_public", "BOOLEAN DEFAULT 1")

print("=== creating new tables ===")
c.execute("""
CREATE TABLE IF NOT EXISTS activity_logs (
    id INTEGER PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id),
    action VARCHAR NOT NULL,
    target VARCHAR,
    detail TEXT,
    ip_address VARCHAR,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
)
""")
print("  + activity_logs")

conn.commit()
conn.close()
print("\nMigration complete.")

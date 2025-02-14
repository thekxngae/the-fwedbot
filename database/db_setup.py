import sqlite3
import typing
from GLOSSARY import logger, DB_FILE
from database.db_manager import execute_query

#### ------- [ DATABASE QUERIES ] ------- ####
SQL_GET_CURRENT_STEP = """
    SELECT current_step
    FROM user_states
    WHERE user_id = ?;
"""
SQL_CHECK_USER_EXISTS = """
    SELECT 1 FROM user_states
    WHERE user_id = ?
    LIMIT 1;
"""
SQL_NEXT_STEP = """
    UPDATE user_states
    SET current_step = ?
    WHERE user_id = ?;
"""
SQL_GET_TITLE = """
    SELECT connection_title
    FROM user_connections
    WHERE user_id = ?;
"""

#### ------- [ DATABASE INITIALIZATION ] ------- ####
def init_db():
    """Initializes the database and creates necessary tables."""
    conn = sqlite3.connect(DB_FILE, check_same_thread=False)
    cursor = conn.cursor()
    try:
        # Create 'user_states' table if it doesn't exist
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS user_states (
            chat_id INTEGER NOT NULL,
            user_id INTEGER NOT NULL,
            current_step TEXT
    );
            """)
        # Create other existing tables...
        cursor.execute("""
               CREATE TABLE IF NOT EXISTS user_connections (
       connection_id INTEGER PRIMARY KEY AUTOINCREMENT,
       user_id INTEGER,
       connection_title TEXT,
       source_group_id INTEGER,
       source_topic_id INTEGER,   -- Source topic ID
       target_group_id INTEGER,
       target_topic_id INTEGER,   -- Target topic ID
       is_active BOOLEAN DEFAULT 1,
       FOREIGN KEY(user_id) REFERENCES user_states(user_id)
   );
        """)
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS user_groups (
            user_id INTEGER NOT NULL,          -- The user who added the group
            group_id INTEGER NOT NULL UNIQUE,  -- The Telegram Group ID
            group_name TEXT NOT NULL,          -- The name of the group for display
            is_active BOOLEAN DEFAULT 1,
            FOREIGN KEY(user_id) REFERENCES user_states(user_id)
                );
             """)
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS group_topics (
    group_id INTEGER NOT NULL,       -- Related group ID
    topic_id INTEGER NOT NULL,       -- Unique topic ID in the group
    topic_name TEXT NOT NULL UNIQUE,        -- The name of the topic
    CONSTRAINT unique_group_topic UNIQUE (group_id, topic_id) -- Each topic must be unique per group
);""")
        conn.commit()
        logger.info("Database initialized successfully.")
    except Exception as database_error:
        logger.error("Error initializing database: %s", database_error, exc_info=True)
    finally:
        conn.close()

def get_single_value(query: str, params: tuple) -> typing.Optional[any]:
    """
    Executes a query and extracts the single-column value from the first row.
    Returns None if no rows are returned.
    """
    result = execute_query(query, params)
    if result:
        return result[0]  # Extract the single-column value
    return None

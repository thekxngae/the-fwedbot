from GLOSSARY import logger
from database.db_manager import execute_query, execute_non_query

#### ------- [ USER STATE HELPERS ] ------- ####

def save_user(chat_id: int, user_id: int, current_step: str):
    try:
        # Perform database INSERT or UPDATE query to save the user state
        query = """
            INSERT INTO user_states (chat_id, user_id, current_step)
            VALUES (?, ?, ?)
        """
        execute_non_query(query, params=(chat_id, user_id, current_step))
    except Exception as save_error:
        logger.error(f"[SAVING] Failed to save user {user_id}: {save_error}", exc_info=True)
        raise

def update_user( user_id: int, current_step: str):
    try:
        # Update User
        query = """
        UPDATE user_states
        SET current_step = ?
        WHERE user_id = ?;
        """
        execute_non_query(query, params=(current_step, user_id))
    except Exception as save_error:
        logger.error(f"[SAVING] Failed to update user {user_id}: {save_error}", exc_info=True)
        raise

def get_user(user_id: int, chat_id: int, current_step: str) -> dict:
    try:
        # SQL query to fetch the user's state
        query = """
            SELECT user_id, current_step
            FROM user_states
            WHERE user_id = ?
        """
        result = execute_query(query, params=(user_id,))

        if result:
            # Map the database result to meaningful keys
            user_id, current_step = result[0]  # Fetch the first row
            return {"user_id": user_id, "current_step": current_step}
        else:
            logger.info(f"[Get User State] No user found for user={user_id}")
            return {}

    except Exception as error:
        logger.error(f"[Get User State] Failed to fetch state for user_id={user_id}: {error}", exc_info=True)
        return {}

def get_user_groups(user_id: int) -> list[tuple]:
    query = """
    SELECT group_id, group_name FROM user_groups
    WHERE user_id = ?;
    """
    return execute_query(query, params=(user_id,))

def save_connection(user_id: int, source_group: int, target_group: int, source_topic: int = None,
                    target_topic: int = None):
    """
    Saves the connection between a source group/topic and a target group/topic
    into the `user_connections` table.
    """
    query = """
        INSERT INTO user_connections (
            user_id, connection_title, source_chat_id, source_topic_id,
            target_chat_id, target_topic_id, is_active
        )
        VALUES (?, ?, ?, ?, ?, ?, 1);
    """
    connection_title = f"{source_group}-> {target_group}"  # Optionally create a default title
    execute_query(query, params=(user_id, connection_title, source_group, source_topic, target_group, target_topic))

def add_group_to_user(user_id, chat_id, group_name):
    query = """
       INSERT INTO user_groups (user_id, group_id, group_name, is_active)
       VALUES (?, ?, ?, 1)
       ON CONFLICT(group_id) DO UPDATE SET is_active = 1, group_name = excluded.group_name;
       """
    execute_non_query(query, params=(user_id, chat_id, group_name))

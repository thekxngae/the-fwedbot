import sqlite3
from GLOSSARY import DB_FILE, logger
from telegram import Update
from telegram.ext import CallbackContext

async def handle_remove_connection_command(update: Update, context: CallbackContext):
    """
    Command handler to remove a connection by its connection_id.
    Example usage: /remove_connection 1234
    """
    try:
        # Ensure user provided arguments
        if len(context.args) == 0:
            await update.message.reply_text("Usage: /remove_connection <connection_id>")
            return

        # Parse connection_id from arguments
        connection_id = int(context.args[0])

        # Call the function to remove the connection
        result = remove_connection_by_id(connection_id)  # Synchronous function
        await update.message.reply_text(result)  # Await here because it's async

    except ValueError:
        await update.message.reply_text("Invalid connection_id. Please provide an integer value.")
    except Exception as ex:
        await update.message.reply_text(f"An error occurred: {ex}")


def remove_connection_by_id(connection_id: int) -> str:
    try:
        logger.info(f"Attempting to delete connection with ID {connection_id}")
        sql_query = "DELETE FROM user_connections WHERE connection_id = ?"
        conn = sqlite3.connect(DB_FILE, check_same_thread=False)
        cursor = conn.cursor()
        cursor.execute(sql_query, (connection_id,))
        affected_rows = cursor.rowcount
        conn.commit()
        conn.close()

        logger.info(f"Affected rows: {affected_rows}")
        if affected_rows > 0:
            return f"Successfully deleted connection with connection_id {connection_id}."
        else:
            return f"No connection found with connection_id {connection_id}."
    except sqlite3.Error as db_error:
        logger.error("Database error during deletion: %s", db_error, exc_info=True)
        return f"Database error: {db_error}"
    except Exception as ex:
        logger.error("Unexpected error during deletion: %s", ex, exc_info=True)
        return f"An unexpected error occurred: {ex}"

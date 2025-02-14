from telegram import Update, InlineKeyboardButton
from telegram.ext import ContextTypes

from GLOSSARY import logger, CUSTOM_FOOTER
from database.db_manager import execute_query

#### ------- [ Global Helpers ] ------- ####

def append_footer(message: str) -> str:
    return f"{message}{CUSTOM_FOOTER}"

def send_reply(update, text, reply_markup=None):
    """Unified function to send replies consistently."""
    if update.message:
        return update.message.reply_text(text, reply_markup=reply_markup, parse_mode="Markdown")
    elif update.callback_query and update.callback_query.message:
        return update.callback_query.message.reply_text(text, reply_markup=reply_markup, parse_mode="Markdown")

def get_current_step_from_db(user_id: int) -> str:
    try:
        # Define your SQL query
        query = """
            SELECT current_step
            FROM user_states
            WHERE user_id = ?;
        """
        params = (user_id,)

        # Execute query (assume `execute_query` is your helper function for SELECTs)
        result = execute_query(query, params)

        # If user exists in the database, return the current_step
        if result and len(result) > 0:
            return result[0][0]  # Extract 'current_step' (e.g., ('start',))

        # Return default step if user is not found in the database
        return "start"

    except Exception as e:
        logger.error("[DATABASE Error] Failed to fetch current_step for user %s: %s", user_id, e, exc_info=True)
        return "start"  # Fallback default step

def append_main_menu_button(keyboard):
    """
    Appends a 'Return to Main' button to the provided keyboard.
    """
    if not keyboard:
        keyboard = []
    keyboard.append([InlineKeyboardButton("🔙 Return to Main Menu", callback_data="back_to_main")])
    return keyboard


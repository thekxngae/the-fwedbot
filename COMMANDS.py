import telegram
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, CallbackContext
from GLOSSARY import SK_START, logger, CallbackData
from bot_functions.helpers.helpers import append_footer, send_reply
from database.db_manager import execute_query, execute_non_query
from database.db_setup import SQL_CHECK_USER_EXISTS
from database.db_user_queries import save_user, update_user, add_group_to_user

# --- [COMMANDS] --- #

async def start_main_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    user_id = update.effective_user.id
    is_private = update.effective_chat.type == "private"
    current_step = SK_START

    # Validate inputs
    if not update.effective_user or not update.effective_chat:
        logger.warning(
            "[START] Invalid update: missing user or chat information")
        return
    else:
        logger.info(
            f"[START] New Chat Started.\n"
            f"Chat Type: {'Private' if is_private else 'Group'}.\n"
            f"Chat ID: {chat_id},\n"
            f"User ID: {user_id}")

    try:
        # STEP 1: Check if user_id already exists in the database
        query = SQL_CHECK_USER_EXISTS
        user_exists = execute_query(query, params=(user_id,), fetch=True)

        if not user_exists:
            # STEP 2: Save user to database if not already present
            logger.info(f"[START] Saving new user:\n"
                        f"chat_id={chat_id},\n"
                        f"user_id={user_id},\n"
                        f"current_step={current_step}")

            save_user(chat_id, user_id, current_step)

            logger.info(f"[START] User state saved for new user {user_id}.\n"
                        f"Current Step: {current_step}\n"
                        f"Directing to Main Menu")
        else:
            # Only Reset the user's current step

            update_user(user_id, current_step)

            logger.info(f"[START] User {user_id} already exists in the database. Updating Current_step.")

    except Exception as save_error:
        logger.error(f"[START] Failed to check or save user state in database:"
                     f"{save_error}", exc_info=True)

    # STEP 3: Define the main menu keyboard
    keyboard = [
        [
            InlineKeyboardButton("➕ Add Connection",
                                 callback_data=CallbackData.ADD_CONNECTION),
            InlineKeyboardButton("❌ Remove Connection",
                                 callback_data=CallbackData.REMOVE_CONNECTION),
        ],
        [
            InlineKeyboardButton("👀 View Connections",
                                 callback_data=CallbackData.VIEW_CONNECTIONS),
            InlineKeyboardButton("🔄 Toggle Connections",
                                 callback_data=CallbackData.TOGGLE_CONNECTIONS),
        ],
        [
            InlineKeyboardButton("⚙️ Config Settings",
                                 callback_data=CallbackData.CONFIG_SETTINGS),
            InlineKeyboardButton("💖 Support Fwedbot",
                                 callback_data=CallbackData.SUPPORT_FWEDBOT),
        ],
    ]

    # STEP 4: Send welcome message with the main menu
    try:
        await context.bot.send_message(
            chat_id=chat_id,
            text=append_footer(
                "👋 Welcome to fwedbot!\n\n"
                "This bot tracks the activity of coin address' sent in Alpha Chats,"
                " and reflects them in to your desired group."
                "\n\n🚀 Use the buttons below to get started!"
            ),
            reply_markup=InlineKeyboardMarkup(keyboard),
        )
    except Exception as starting_error:
        logger.error(f"[START] Failed to send message: {starting_error}")

async def init_group(update: Update, context: CallbackContext):
    effective_chat = update.effective_chat
    effective_user = update.effective_user

    if effective_chat.type in ["group", "supergroup"]:
        try:
            # Add the group to the user in the database
            add_group_to_user(effective_user.id, effective_chat.id, effective_chat.title)

            # Notify the user
            await context.bot.send_message(
                chat_id=effective_chat.id,
                text=(
                    f"👋 Thanks for adding me to '{effective_chat.title}'!\n"
                    f"This group (and its topics, if any) is now linked to your account."
                ),
            )
        except Exception as error:
            logger.error(
                f"Failed to handle /start in group {effective_chat.id} (Title: '{effective_chat.title}'): {error}",
                exc_info=True
            )
            await context.bot.send_message(
                chat_id=effective_chat.id,
                text="❌ An error occurred while initializing this group. Please try again later."
            )
    else:
        # Handle scenario where the bot is added in unsupported chat types
        await update.message.reply_text(
            "Hi! Use /start in a group to initialize it for your account."
        )

async def init_topic(update: Update, context: CallbackContext):
    """
    Handles the /initialise command.
    Saves the topic ID and group ID in the database without making API calls.
    Allows the user to manually assign a name to the topic.
    """
    try:
        # Extract topic and group IDs
        message_thread_id = update.effective_message.message_thread_id  # Topic ID
        chat_id = update.effective_chat.id  # Group ID

        # Check if message_thread_id is present (ensure the command is executed in a topic-enabled chat)
        if not message_thread_id:
            await update.message.reply_text(
                "❌ This command is only functional within a topic-enabled group."
            )
            return

        # Save topic to the database with a placeholder name
        query = """
            INSERT INTO group_topics (group_id, topic_id, topic_name)
            VALUES (?, ?, ?)
        """
        placeholder_name = f"Unnamed Topic {message_thread_id}"  # Placeholder name for the topic
        params = (chat_id, message_thread_id, placeholder_name)
        execute_non_query(query, params)

        # Prompt the user to name the topic
        await update.message.reply_text(
            f"✅ Topic (ID: {message_thread_id}) has been added to the group tracking list.\n\n"
            f"Please set a name for this topic by replying with:\n"
            f"`/set_topic_name {message_thread_id} <Topic Name>`"
        )

    except Exception as error:
        logger.error(f"[Initialise Topic] Failed to initialise topic: {error}", exc_info=True)
        await update.message.reply_text(
            "⚠️ An error occurred while initializing the topic. Please try again later."
        )

async def set_topic_name(update: Update, context: CallbackContext):
    try:
        # Ensure the command has sufficient arguments
        if len(context.args) < 2:
            await update.message.reply_text(
                "❌ Invalid command format. Please use:\n`/set_topic_name <topic_id> <Topic Name>`",
                parse_mode=telegram.constants.ParseMode.MARKDOWN,
            )
            return

        # Parse topic_id and topic_name from the command arguments
        topic_id = context.args[0]
        if not topic_id.isdigit():
            await update.message.reply_text("❌ The topic ID must be a numeric value.")
            return
        topic_id = int(topic_id)
        topic_name = " ".join(context.args[1:]).strip()

        # Update the topic name in the database
        query = """
            UPDATE group_topics
            SET topic_name = ?
            WHERE topic_id = ?;
        """
        params = (topic_name, topic_id)
        execute_non_query(query, params)

        # Notify the user of the successful update
        await update.message.reply_text(
            f"✅ Topic ID `{topic_id}` has been renamed to '{topic_name}'.",
            parse_mode=telegram.constants.ParseMode.MARKDOWN,
        )

    except Exception as error:
        logger.error(f"[Set Topic Name] Failed to set topic name: {error}", exc_info=True)
        await update.message.reply_text(
            "⚠️ An error occurred while setting the topic name. Please try again later."
        )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handles the /help command."""
    await send_reply(
        update,
        "Here are some bot_commands you can use:\n"
        "Use /start to Start the bot\n"
        "Use /init_group in a group to Initialise it for your account\n"
        "Use /init_topic in a topic-enabled group to Initialise it for your account\n"
        "If you need more help setting up, please contact support"
    )

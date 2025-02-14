# --- Constants
from telegram.ext import (
    ApplicationBuilder, CommandHandler, MessageHandler, CallbackQueryHandler, filters)
from GLOSSARY import (BOT_TOKEN, logger)
from bot_commands.add_connection import (handle_button, handle_title, handle_ids,
                                         handle_target_group_selection, handle_target_topic_selection,
                                         handle_source_group_selection,
                                         handle_source_topic_selection)
from COMMANDS import start_main_menu, init_group, init_topic, set_topic_name, help_command
from bot_functions.main.forwarding import handle_message
# --- Command Handlers
from bot_menu.main_menu import handle_menu_buttons
from database.db_setup import init_db

if __name__ == "__main__":
    # --- Initialize the database
    try:
        init_db()
        logger.info("[Database] Successfully initialized.")
    except Exception as db_error:
        logger.critical("[Database] Initialization failed. Exiting the bot.", exc_info=db_error)
        exit(1)

    # --- Build the bot application
    try:
        app = ApplicationBuilder().token(BOT_TOKEN).build()
        logger.info("[Startup] Bot application initialized successfully.")
    except ValueError as token_error:
        logger.critical("[Startup] Invalid BOT_TOKEN! Please check the configuration.", exc_info=token_error)
        exit(1)
    except RuntimeError as runtime_error:
        logger.critical("[Startup] Encountered a runtime error. Exiting.", exc_info=runtime_error)
        exit(1)
    except Exception as unknown_error:
        logger.critical("[Startup] Unknown error during bot initialization.", exc_info=unknown_error)
        raise

    # --- Register Command Handlers (e.g., /start, /help)
    app.add_handler(CommandHandler("start", start_main_menu))
    app.add_handler(CommandHandler("init_group", init_group))
    app.add_handler(CommandHandler("init_topic", init_topic))
    app.add_handler(CommandHandler("set_topic_name", set_topic_name))
    app.add_handler(CommandHandler("help", help_command))

    # Add MessageHandler for group messages
    group_message_handler = MessageHandler(
        filters.ChatType.GROUPS & filters.TEXT,  # Filters group text messages
        handle_message)

    # --- Register Message Handlers (State-Based Routing)
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_title))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_ids))
    app.add_handler(group_message_handler)

    # --- Register CallbackQuery Handlers for Buttons
    app.add_handler(CallbackQueryHandler(handle_button, pattern="add_connection"))
    app.add_handler(CallbackQueryHandler(handle_menu_buttons, pattern="menu"))
    app.add_handler(CallbackQueryHandler(start_main_menu, pattern="main_menu"))
    app.add_handler(CallbackQueryHandler(handle_source_group_selection, pattern="source_group_"))
    app.add_handler(CallbackQueryHandler(handle_source_topic_selection, pattern="source_topic_"))
    app.add_handler(CallbackQueryHandler(handle_source_topic_selection, pattern="no_source_topic"))
    app.add_handler(CallbackQueryHandler(handle_target_group_selection, pattern="target_group_"))
    app.add_handler(CallbackQueryHandler(handle_target_topic_selection, pattern="target_topic_"))
    app.add_handler(CallbackQueryHandler(handle_target_topic_selection, pattern="no_target_topic"))

    # --- Run the bot
    logger.info("[Bot] Bot is now running...")
    app.run_polling()






























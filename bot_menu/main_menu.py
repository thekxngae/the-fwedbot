from telegram import InlineKeyboardMarkup, Update
from telegram.ext import ContextTypes
from GLOSSARY import logger
from bot_commands.add_connection import handle_button
from bot_functions.helpers.helpers import append_main_menu_button


async def handle_menu_buttons(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Handles button presses from the menu gracefully.
    """
    query = update.callback_query  # Retrieve the callback query object
    action = query.data  # Action triggered by the button press
    user_id = update.effective_user.id
    chat_id = update.effective_chat.id

    logger.info("Received callback data: %s", action)  # Log the action for debugging

    try:
        # Handle specific button actions
        if action == "add_connection":
            await handle_button(update, context)

        elif action == "view_connections":
            # Provide user with supporting bot details
            keyboard = []  # Empty keyboard for now
            reply_markup = InlineKeyboardMarkup(append_main_menu_button(keyboard))  # Add main menu button

            await query.edit_message_text(
                "👀 View Connections feature is under construction.\n"
                "Check back later!",
                reply_markup=reply_markup)

        elif action == "toggle_connections":
            # Provide user with supporting bot details
            keyboard = []  # Empty keyboard for now
            reply_markup = InlineKeyboardMarkup(append_main_menu_button(keyboard))  # Add main menu button

            await query.edit_message_text(
                "📡 Toggle Connections feature is under construction.\n"
                "Check back later!",
                reply_markup=reply_markup
            )

        elif action == "remove_connection":
            # Provide user with supporting bot details
            keyboard = []  # Empty keyboard for now
            reply_markup = InlineKeyboardMarkup(append_main_menu_button(keyboard))  # Add main menu button

            await query.edit_message_text(
                "🛠 Currently, editing settings is under development.\n"
                "Stay tuned for updates!",
            reply_markup = reply_markup
            )

        elif action == "config_settings":
            # Provide user with supporting bot details
            keyboard = []  # Empty keyboard for now
            reply_markup = InlineKeyboardMarkup(append_main_menu_button(keyboard))  # Add main menu button

            await query.edit_message_text(
                "🛠 Currently, editing settings is under development.\n"
                "Stay tuned for updates!",
                reply_markup = reply_markup
            )

        elif action == "edit_connection":
            # Future feature: Editing a connection
            keyboard = []  # Empty keyboard for now
            reply_markup = InlineKeyboardMarkup(append_main_menu_button(keyboard))  # Add main menu button

            await query.edit_message_text(
                "🛠 Currently, editing connections is under development.\n"
                "Stay tuned for updates!",
                reply_markup = reply_markup
            )

        elif action == "view_logs":
            # Placeholder action for viewing logs
            keyboard = []  # Empty keyboard for now
            reply_markup = InlineKeyboardMarkup(append_main_menu_button(keyboard))  # Add main menu button

            await query.edit_message_text(
                "📜 Logs feature is under construction.\n"
                "Check back later!",
                reply_markup = reply_markup
            )

        elif action == "support_fwedbot":
            # Provide user with supporting bot details
            keyboard = []  # Empty keyboard for now
            reply_markup = InlineKeyboardMarkup(append_main_menu_button(keyboard))  # Add main menu button

            await query.edit_message_text(
                "Thanks for supporting Fwedbot! 💖\n\n"
                "If you would like to support the team, and the project, you can do so by using our trading referral links for the top bots on Solana:\n"
                " You can also: \n\n"
                "- Check out some of @TheKxngAE 's post's on twitter.\n\n"
                "- Share Fwedbot with friends 🌐\n\n"
                "- Suggest features or report bugs 🐞\n\n"
                "- Use our referral codes 💹\n\n"
                "Explore:\n"
                "Trade on Nova Bot | [Nova Bot](https://t.me/TradeonNovaBot?start=r-CE0V7EW)\n"
                "Trade on Trojan Bot | [Trojan Bot](https://t.me/solana_trojanbot?start=r-kxngkxnquest)\n"
                "Trade on MevX Bot | [MevX Bot](https://t.me/Mevx?start=kxngkxnquest)\n\n"
                "🚀 Join our group: https://t.me/thekxngsquarters",
                parse_mode="Markdown",
                disable_web_page_preview=True,
                reply_markup = reply_markup
            )
            await query.answer()

        elif action == "back_to_main":
            from COMMANDS import start_main_menu
            # Redirect to main menu
            await start_main_menu(update, context)

        else:
            # Handle unrecognized actions gracefully
            logger.warning("Unrecognized action received: %s", action)
            await query.edit_message_text(
                "❌ Unrecognized action.\n"
                "Please use the buttons to navigate or return to the main menu."
            )
            await query.answer()

    except Exception as e:
        # Log the error and inform the user
        logger.error("Error while handling menu buttons: %s", e, exc_info=True)
        await query.edit_message_text(
            "❌ An error occurred while processing your request.\n"
            "Please try again later."
        )


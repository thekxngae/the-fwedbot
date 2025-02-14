import asyncio
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from telegram import Update
from telegram.ext import ContextTypes
from GLOSSARY import logger, SK_START, CallbackData, SK_ADD1
from bot_commands.add_connection import handle_button
from bot_functions.helpers.helpers import append_footer
from database.db_manager import execute_query, execute_non_query
from database.db_user_queries import save_user, update_user
from database.db_setup import SQL_CHECK_USER_EXISTS

async def handle_menu_buttons(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Handles button presses from the menu.
    """
    query = update.callback_query  # Retrieve the callback query object
    action = query.data  # The action triggered by the button press
    user_id = update.effective_user.id
    chat_id = update.effective_chat.id
    current_step = SK_ADD1

    logger.info("Received callback data: %s", action)  # Log the received action for debugging

    try:
        if action == "add_connection":
            await handle_button(update, context)

        elif action == "view_connections":
            await view_connections(update, context)

        elif action == "toggle_connections":
            await toggle_connections(update, context)

        elif action == "remove_connection":
            keyboard = [
                [
                    InlineKeyboardButton("Remove Specific Connection", callback_data="remove_specific"),
                ],
                [
                    InlineKeyboardButton("❌ Remove All Connections", callback_data="confirm_remove_all"),
                ],
                [
                    InlineKeyboardButton("🔙 Back to Main Menu", callback_data="back_to_main"),
                ],
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)

            if query.message:
                await query.edit_message_text(
                    append_footer(
                        "To remove a connection, you can use the following bot_commands:\n\n"
                        "`/remove_connection <connection_title>`\n\n"
                        "`/remove_connection <source_chat_id> <target_chat_id>`\n"
                        "`/remove_connection <source_chat_id> <source_topic_id> <target_chat_id>`\n"
                        "`/remove_connection <source_chat_id> <target_chat_id> <target_topic_id>`\n"
                        "`/remove_connection <source_chat_id> <source_topic_id> <target_chat_id> <target_topic_id>`\n\n"
                        "Or use the buttons below."
                    ),
                    reply_markup=reply_markup,
                    parse_mode="Markdown",
                )
            else:
                await query.edit_message_text(
                    append_footer(
                        "To remove a connection, you can use the following bot_commands:\n"
                        "`/remove_connection <connection_title>`\n"
                        "`/remove_connection <source_chat_id> <target_chat_id>`\n"
                        "`/remove_connection <source_chat_id> <source_topic_id> <target_chat_id>`\n"
                        "`/remove_connection <source_chat_id> <target_chat_id> <target_topic_id>`\n"
                        "`/remove_connection <source_chat_id> <source_topic_id> <target_chat_id> <target_topic_id>`\n\n"
                        "Or use the buttons below."
                    ),
                    reply_markup=reply_markup,
                    parse_mode="Markdown",
                )

        elif action == "support_fwedbot":
            if query.message:
                await query.edit_message_text(
                    "💖 Thank you for supporting **Fwedbot**!\n\n"
                    "You can support us by:\n"
                    "- Sharing Fwedbot with your friends 🌐\n"
                    "- Reporting bugs and suggesting features 🐞\n"
                    "- Using our referral codes 💹\n\n"
                    "🚀 Check out:\n\n"
                    "- [Nova Bot](https://t.me/TradeonNovaBot?start=r-CE0V7EW)\n"
                    "- [Trojan Bot](https://t.me/solana_trojanbot?start=r-kxngkxnquest)\n"
                    "- [MevX Bot](https://t.me/Mevx?start=kxngkxnquest)\n"
                    "- Join the Private Alpha Group 💹\n\n"
                    "🚀 Check out: https://t.me/thekxngsquarters\n\n",
                    parse_mode="Markdown",
                    disable_web_page_preview=True,
                )
            else:
                await query.edit_message_text(
                    "💖 Thank you for supporting **Fwedbot**!\n\n"
                    "You can support us by:\n"
                    "- Sharing Fwedbot with your friends 🌐\n"
                    "- Reporting bugs and suggesting features 🐞\n"
                    "- Using our referral codes 💹\n\n"
                    "🚀 Check out:\n\n"
                    "- [Nova Bot](https://t.me/TradeonNovaBot?start=r-CE0V7EW)\n"
                    "- [Trojan Bot](https://t.me/solana_trojanbot?start=r-kxngkxnquest)\n"
                    "- [MevX Bot](https://t.me/Mevx?start=kxngkxnquest)\n"
                    "- Join the Private Alpha Group 💹\n\n"
                    "🚀 Check out: https://t.me/thekxngsquarters\n\n",
                    parse_mode="Markdown",
                    disable_web_page_preview=True,
                )
            await query.answer()

        elif action == "back_to_main":
            await start_main_menu(update, context)

        else:
            # Log the unrecognized action and send the error response
            logger.warning(f"Unrecognized action received: {action}")

            if query.message:
                await query.message.reply_text(
                    "❌ Unrecognized action. Please try again or return to the main menu."
                )
            else:
                await query.edit_message_text(
                    "❌ Unrecognized action. Please try again or return to the main menu."
                )
            await query.answer()

    except Exception as e:
        logger.error("Error handling menu buttons: %s", e, exc_info=True)


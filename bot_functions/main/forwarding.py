import re
from typing import Optional

from telegram import Update
from telegram.ext import ContextTypes
from GLOSSARY import logger
from bot_functions.helpers.helpers import get_current_step_from_db
from database.db_manager import execute_query


async def detect_and_forward(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Detects coin addresses in a message and forwards the message exclusively
    to the preconfigured target destination if valid coin addresses are found.
    """
    # Ensure the message contains valid text
    if not update.message or not update.message.text:
        return

    # Step 1: Extract message details
    source_group_id = update.message.chat_id
    source_topic_id = update.message.message_thread_id  # Topic ID for thread-enabled chats
    message_text = update.message.text.strip()

    # Step 2: Detect valid coin addresses in the message
    detected_address = extract_coin_address_with_types(message_text)

    # Validate detection results
    if not isinstance(detected_address, list):
        logger.error("[Detect And Forward] Invalid return from extract_coin_addresses_with_types.")
        return
    if not detected_address:
        logger.info("[Detect And Forward] No valid coin addresses detected in the message.")
        return  # Stop if no addresses are found

    # Step 3: Format the message with detected addresses
    formatted_message = format_forwarded_message_with_hyperlinks(detected_address)

    # Step 4: Retrieve the configured target for this source group/topic
    connection = get_connection_for_source(source_group_id, source_topic_id)

    if not connection:
        logger.info(
            "[Detect And Forward] No configured destination for source: Group ID %s, Topic ID %s",
            source_group_id, source_topic_id
        )
        return

    # Unpack connection details
    target_group_id, target_topic_id, connection_title = connection

    # Step 5: Forward the message to the exclusive target destination
    try:
        # Attribute the message with the connection title
        attributed_message = (
            f"{formatted_message}\n\n🔗 **Source Connection Name**: {connection_title or 'Unnamed Connection'}"
        )

        # Forward message to a topic or group
        if target_topic_id:
            await context.bot.send_message(
                chat_id=target_group_id,
                text=attributed_message,
                message_thread_id=target_topic_id,
                parse_mode="Markdown"  # Telegram Markdown to support clickable links
            )
        else:
            await context.bot.send_message(
                chat_id=target_group_id,
                text=attributed_message,
                parse_mode="Markdown"
            )

        # Log success
        logger.info(
            "[Detect And Forward] Message successfully forwarded from Source (%s, %s) to Target (%s, %s).",
            source_group_id, source_topic_id, target_group_id, target_topic_id
        )

    except Exception as forward_error:
        logger.error(
            "[Detect And Forward] Error while forwarding message: %s",
            forward_error, exc_info=True
        )

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Handles incoming messages and filters based on user state or group context.
    """
    user_id = update.effective_user.id
    chat_type = update.message.chat.type  # Determine if it's a group/private chat

    # Handle messages in Source Groups WITHOUT step checking
    if chat_type in ["group", "supergroup"]:
        logger.info(
            "[GROUP MESSAGE] Processing message in source group: Chat ID %s",
            update.message.chat_id
        )
        # Send the message directly to the forwarding function
        await detect_and_forward(update, context)  # Skip step validation
        return

    # Handle private messages WITH step validation
    if chat_type == "private":
        # Fetch the current step for the user
        current_step = get_current_step_from_db(user_id)
        logger.info("[STEP CHECK] User %s current step in DB: '%s'", user_id, current_step)

        # Process only if the user is in the required step
        if current_step != "adding_connection":
            logger.info(
                "[STEP CHECK] Ignored message from user %s not in step 'adding_connection'.",
                user_id
            )
            return  # Ignore private message if step doesn't match

        # Handle private message further (e.g., process connection adding)
        logger.info("[PRIVATE MESSAGE] Processing user %s's private message in step '%s'.", user_id, current_step)

    # Log unexpected chat types
    else:
        logger.warning(
            "[UNKNOWN CHAT TYPE] Ignored message from Chat ID %s, Chat Type %s.",
            update.message.chat_id, chat_type
        )

#### ------- [ Forwarding Function Helper ] ------- ####

def extract_coin_address_with_types(message: str) -> list:
    """
    Extracts and classifies Solana coin addresses.

    Args:
        message (str): The input message.

    Returns:
        list: A list of dictionaries containing extracted addresses and their types.
    """
    if not message or not isinstance(message, str):
        return []  # Return an empty list if the input is invalid

    # Regex patterns
    regular_pattern = r"\b[1-9A-HJ-NP-Za-km-z]{32,44}\b"
    # noinspection SpellCheckingInspection
    pumpfun_pattern = r"\b[1-9A-HJ-NP-Za-km-z]{28,40}pump\b"

    # Match using the regex
    pumpfun_matches = re.findall(pumpfun_pattern, message)
    regular_matches = re.findall(regular_pattern, message)

    # Validation (ensure it's a real coin address - adjust further as needed)
    min_address_length = 32
    max_address_length = 44

    pumpfun_matches = [addr for addr in pumpfun_matches if min_address_length <= len(addr) <= max_address_length]
    regular_matches = [addr for addr in regular_matches if min_address_length <= len(addr) <= max_address_length]

    results = [{"address": address, "type": "PumpFun"} for address in pumpfun_matches]
    results.extend(
        {"address": address, "type": "Regular"}
        for address in regular_matches
        if address not in pumpfun_matches
    )
    return results

def format_forwarded_message_with_hyperlinks(addresses_with_types: list) -> str:
    """
    Formats the forwarded message with clickable hyperlinks for detected PumpFun or Regular addresses.

    Args:
        addresses_with_types (list): List of dictionaries containing addresses and their types.

    Returns:
        str: A formatted message.
    """
    # Base referral URL template
    referral_link_template = "https://t.me/TradeonNovaBot?start=r-CE0V7EW-{address}"

    # Separate PumpFun and Regular addresses
    pumpfun_addresses = [
        f"[{addr['address']}]({referral_link_template.format(address=addr['address'])})"
        for addr in addresses_with_types if addr["type"] == "PumpFun"
    ]
    regular_addresses = [
        f"[{addr['address']}]({referral_link_template.format(address=addr['address'])})"
        for addr in addresses_with_types if addr["type"] == "Regular"
    ]

    if pumpfun_addresses:
        # If PumpFun type exists, emphasize it
        message = "📩 **New PumpFun Alpha Found!**\n\n" + "🚀 Trade Now:\n\n" + "\n".join(pumpfun_addresses)
    else:
        # Otherwise, fallback to Regular
        message = "📩 **New Alpha Found!**\n\n" + "🚀 Trade Now:\n\n" + "\n".join(regular_addresses)

    return message

def get_connection_for_source(source_group_id: int, source_topic_id: Optional[int] = None):
    """
    Fetch the exclusive target destination for the source group/topic from the database.
    """
    try:
        query = """
            SELECT target_group_id, target_topic_id, connection_title
            FROM user_connections
            WHERE source_group_id = ? AND (source_topic_id = ? OR source_topic_id IS NULL)
        """
        params = (source_group_id, source_topic_id)
        result = execute_query(query, params)

        if result:
            return result[0]  # Exclusive rule: Return the first/only connection
        return None
    except Exception as e:
        logger.error("[Database Error] Failed to fetch connection: %s", e, exc_info=True)
        return None


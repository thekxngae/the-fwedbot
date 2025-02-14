from collections import defaultdict
from asyncio import Lock
import typing
import logging
import sys
from telegram import Update

#### ------- [ CUSTOM FOOTER ] ------- $$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$
CUSTOM_FOOTER = (
    "\n\n\n🤖 Powered by fwedbot | Support the Team | Trade on Trojan, Nova, or MevX"
    "\nTrojan Bot | (https://t.me/solana_trojanbot?start=r-kxngkxnquest)"
    "\nNova Bot | (https://t.me/TradeonNovaBot?start=r-CE0V7EW)"
    "\nMevX Bot | (https://t.me/Mevx?start=kxngkxnquest)"
)

#### ------- [ LOGGING CONFIGURATION ] ------- ####
class UTF8Encoder(logging.StreamHandler):
    def __init__(self, stream=None):
        if stream is None:
            # Ensure the default stream is stdout
            stream = sys.stdout
        # No need to manually re-wrap the stream with open()
        super().__init__(stream)
logging.basicConfig(
    level=logging.INFO,
    handlers=[
        UTF8Encoder(),  # Use the UTF-8 compatible handler
    ],
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)
logger.info("Bot starting, logging is now active!")
logging.getLogger("httpx").setLevel(logging.WARNING)

#### ------- [ TELEGRAM BOT TOKEN ] ------- ####
BOT_TOKEN = "YOUR_BOT_TOKEN_HERE" ###### <----- Place your Telegram Bot Token inside the ""
if not BOT_TOKEN:
    raise ValueError("The bot token is not set! Please configure the TELEGRAM_BOT_TOKEN environment variable.")

#### ------- [ DATABASE SETUP ] ------- ####
DB_FILE = "database/database.db"
Correct_Input_Format = ("Correct Input Format:\n\n"
                        "Group + Topic -> Group + Topic = <source_chat_id>, <source_topic_id>, <target_chat_id>, <target_topic_id>\n"
                        "OR\n"
                        "Group -> Group = <source_chat_id>, <target_chat_id>\n"
                        "OR\n"
                        "Group + Topic -> Group = <source_chat_id>, <source_topic_id>, <target_chat_id>\n"
                        "OR\n"
                        "Group -> Group + Topic = <source_chat_id>, <target_chat_id>, <target_topic_id>\n\n"
                        "Please ensure your inputs are separated by a ','. Thanks!"
                        )


#### ------- [ CALLBACK DATA ] ------- ####
class CallbackData:
    ADD_CONNECTION = "add_connection"
    REMOVE_CONNECTION = "remove_connection"
    VIEW_CONNECTIONS = "view_connections"
    TOGGLE_CONNECTIONS = "toggle_connections"
    CONFIG_SETTINGS = "config_settings"
    SUPPORT_FWEDBOT = "support_fwedbot"
    HELP = "help"
    START = "start"
    END = "end"
    ERROR = "error"

#### ------- [ USER STATES ] ------- ####
DEFAULT_USER_STATE = { "current_step": "start"}

### ------- [STEP KEY STAGES] ------- ###
SK_START = "start"
SK_ADD1 = "adding_connection"
SK_ADD2 = "awaiting_configuration"
SK_ADD3 = "selecting_source_group"
SK_ADD4 = "selecting_source_topic"
SK_ADD5 = "selecting_target_group"
SK_ADD6 = "selecting_target_topic"


### ------- [PREDEFINED STAGES] ------- ###
INVALID_STEP_MESSAGE = "Unexpected input. Restarting workflow..."
EMPTY_TITLE_MESSAGE = "❌ Title cannot be empty. Please try again."
TITLE_SAVED_MESSAGE = (
    "✅ Title saved! Now, please provide the following details:\n"
    "`<source_chat_id> <source_topic_id> <target_chat_id> <target_topic_id>`\n\n"
    "If you're not using topics, send `<source_chat_id> <target_chat_id>`."
)





# FwedBot

### THIS VERSION IS NOT A COMPLETE ITERATION WITH THE BOT'S FULL FUNCTIONALITY

### This version is a working MVP - Developed to have an early working version of fwedbot deployed.

## About FwedBot

FwedBot is my first ever python-project... EVER!

That's right. Before this - I hadn't ever touched code once. So, this project was my introduction into python, and coding as a whole.

Largely, lot's of it was built with the help of AI, however I obviously had to develop my skills and learn ALOT of knowledge in order to get this anywhere close to viably running.

Fwedbot was built with lots of functionality in mind to come in-future, however this version just ensures the minimum viable product is at least working.

Ultimately, FwedBot will be built into an all-inclusive, all-in-one "Alpha Tracker Bot", tracking all the top alpha and coin address' being sent into different private, and public alpha chats.

## Usage

To get started on the bot, you can actually use it directly from Telegram without the need to install and run the code. Just go to @fwedbot on Telegram, type /start, and follow the prompts.

With this version, you can add the bot to any group, establish the connection in fwedbot, and receive forwarded Coin Address' (CA's) that
get sent from your configured connection, to your desired group.

Currently, the included text-based commands in this version are;

- /start
- /help
- /init_group
- /init_topic

Everything else is managed via the bot's UI on Telegram.

If you choose to install and run the code yourself, you must ensure some pre-requisites are set-up before running the program.

## Requirements

**How to install and set up the FwedBot:**
- Python version: `Python 3.x.x` - (I am using 3.13.1 - Preferably use 3.12 or above)
- Dependencies: Refer to `requirements.txt`).

## Installation

1. Clone the repository:
    ```bash
    git clone <https://github.com/thekxngae/the-fwedbot>
    cd <your-project-folder>
    ```
2. Set up the virtual environment:
    ```bash
    python -m venv .venv
    source .venv/bin/activate     # Linux/Mac
    .venv\Scripts\activate        # Windows
    ```
3. Install dependencies:
    ```bash
    pip install -r requirements.txt
    ```
## Setup

Before running the code, you must ensure to set up your bot token.

- In the GLOSSARY, you will need to edit the Bot Token Placeholder.
- The placeholder will read "YOUR_BOT_TOKEN_HERE"
- Replace this with your actual Bot Token from BotFather on TG.
- If you don't have a Bot Token yet, refer to Google on Instructions how to set up BotFather.

## Contribution

Message @thekxngae on Telegram if you would like to collaborate and contribute to building fwedbot.

I have lots of ideas of what I want to do and build with fwedbot. Primarily, an all inclusive "Alpha Group Tracker" with lot's of extra functionalities.

## License

Specify your licensing terms, if applicable.

from telethon import TelegramClient
from config import API_ID, API_HASH, BOT_TOKEN, STRING
from pyrogram import Client

client = TelegramClient("telethonbot", API_ID, API_HASH)
app = Client("pyrogrambot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)
userbot = Client("4gbbot", api_id=API_ID, api_hash=API_HASH, session_string=STRING)

async def start_client():
    # Start Telethon client
    try:
        await client.start(bot_token=BOT_TOKEN)
        print("SpyLib started...")
    except Exception as e:
        print(f"Failed to start Telethon bot: {e}")
        raise

    # Start Pyrogram userbot if STRING is provided
    if STRING:
        try:
            await userbot.start()
            print("Userbot started...")
        except Exception as e:
            print(f"Check your premium string session, it may be invalid or expired: {e}")
            raise

    # Start Pyrogram bot client
    try:
        await app.start()
        print("Pyro App Started...")
    except Exception as e:
        print(f"Failed to start Pyrogram bot: {e}")
        raise

    return client, app, userbot

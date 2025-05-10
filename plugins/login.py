# Copyright (c) 2025 devgagan : https://github.com/devgaganin.  
# Licensed under the GNU General Public License v3.0.  
# See LICENSE file in the repository root for full license text.

import logging
from pyrogram import Client, filters
from pyrogram.types import Message
from pyrogram.errors import (
    BadRequest, SessionPasswordNeeded, PhoneCodeInvalid, PhoneCodeExpired, MessageNotModified
)
from config import API_HASH, API_ID
from shared_client import app as bot
from utils.func import save_user_session, get_user_data, remove_user_session
from utils.custom_filters import login_in_progress, set_user_step, get_user_step

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

STEP_PHONE = 1
STEP_CODE = 2
STEP_PASSWORD = 3
login_cache = {}

@bot.on_message(filters.command('login'))
async def login_command(client, message: Message):
    user_id = message.from_user.id
    set_user_step(user_id, STEP_PHONE)
    login_cache.pop(user_id, None)
    await message.delete()
    status_msg = await message.reply(
        "Please send your phone number with country code\nExample: `+12345678900`"
    )
    login_cache[user_id] = {'status_msg': status_msg}

@bot.on_message(
    login_in_progress & filters.text & ~filters.command([
        'start', 'batch', 'cancel', 'login', 'logout', 'stop', 'set', 'pay', 'redeem', 'gencode'
    ])
)
async def handle_login_steps(client, message: Message):
    user_id = message.from_user.id
    text = message.text.strip()
    step = get_user_step(user_id)
    try:
        await message.delete()
    except Exception as e:
        logger.warning(f'Could not delete message: {e}')
    status_msg = login_cache.get(user_id, {}).get('status_msg')
    if not status_msg:
        status_msg = await message.reply('Processing...')
        login_cache.setdefault(user_id, {})['status_msg'] = status_msg
    try:
        if step == STEP_PHONE:
            if not text.startswith('+'):
                await edit_message_safely(status_msg, '❌ Please provide a valid phone number starting with +')
                return
            await edit_message_safely(status_msg, '🔄 Processing phone number...')
            temp_client = Client(
                f'temp_{user_id}', api_id=API_ID, api_hash=API_HASH, in_memory=True
            )
            try:
                await temp_client.connect()
                sent_code = await temp_client.send_code(text)
                login_cache[user_id]['phone'] = text
                login_cache[user_id]['phone_code_hash'] = sent_code.phone_code_hash
                login_cache[user_id]['temp_client'] = temp_client
                set_user_step(user_id, STEP_CODE)
                await edit_message_safely(
                    status_msg,
                    "✅ Verification code sent to your Telegram account.\nPlease enter the code you received:"
                )
            except BadRequest as e:
                await edit_message_safely(
                    status_msg,
                    f"❌ Error: {str(e)}\nPlease try again with /login."
                )
                await temp_client.disconnect()
                set_user_step(user_id, None)
                login_cache.pop(user_id, None)
        elif step == STEP_CODE:
            code = text.replace(' ', '')
            phone = login_cache[user_id].get('phone')
            phone_code_hash = login_cache[user_id].get('phone_code_hash')
            temp_client = login_cache[user_id].get('temp_client')
            if not all([phone, phone_code_hash, temp_client]):
                await edit_message_safely(status_msg, "❌ Login state lost. Please try again with /login.")
                set_user_step(user_id, None)
                login_cache.pop(user_id, None)
                return
            try:
                await edit_message_safely(status_msg, '🔄 Verifying code...')
                await temp_client.sign_in(phone, phone_code_hash, code)
                session_string = await temp_client.export_session_string()
                await save_user_session(user_id, session_string)
                await temp_client.disconnect()
                temp_status_msg = login_cache[user_id]['status_msg']
                login_cache.pop(user_id, None)
                login_cache[user_id] = {'status_msg': temp_status_msg}
                await edit_message_safely(
                    status_msg,
                    "✅ Success! Your session has been saved to the database.\nYou can now use the bot that requires this session."
                )
                set_user_step(user_id, None)
            except SessionPasswordNeeded:
                set_user_step(user_id, STEP_PASSWORD)
                await edit_message_safely(
                    status_msg,
                    "🔒 Two-step verification is enabled.\nPlease enter your password:"
                )
            except (PhoneCodeInvalid, PhoneCodeExpired) as e:
                await edit_message_safely(
                    status_msg,
                    f'❌ {str(e)}. Please try again with /login.'
                )
                await temp_client.disconnect()
                login_cache.pop(user_id, None)
                set_user_step(user_id, None)
        elif step == STEP_PASSWORD:
            temp_client = login_cache[user_id].get('temp_client')
            if not temp_client:
                await edit_message_safely(status_msg, "❌ Login state lost. Please try again with /login.")
                set_user_step(user_id, None)
                login_cache.pop(user_id, None)
                return
            try:
                await edit_message_safely(status_msg, '🔄 Verifying password...')
                await temp_client.check_password(text)
                session_string = await temp_client.export_session_string()
                await save_user_session(user_id, session_string)
                await temp_client.disconnect()
                temp_status_msg = login_cache[user_id]['status_msg']
                login_cache.pop(user_id, None)
                login_cache[user_id] = {'status_msg': temp_status_msg}
                await edit_message_safely(
                    status_msg,
                    "✅ Success! Your session has been saved to the database.\nYou can now use the bot that requires this session."
                )
                set_user_step(user_id, None)
            except BadRequest as e:
                await edit_message_safely(
                    status_msg,
                    f"❌ Incorrect password: {str(e)}\nPlease try again:"
                )
    except Exception as e:
        logger.error(f'Error in login flow: {str(e)}')
        await edit_message_safely(
            status_msg,
            f"❌ An error occurred: {str(e)}\nPlease try again with /login."
        )
        if user_id in login_cache and 'temp_client' in login_cache[user_id]:
            try:
                await login_cache[user_id]['temp_client'].disconnect()
            except Exception:
                pass
        login_cache.pop(user_id, None)
        set_user_step(user_id, None)

async def edit_message_safely(message: Message, text: str):
    """Helper function to edit message and handle errors"""
    try:
        await message.edit(text)
    except MessageNotModified:
        pass
    except Exception as e:
        logger.error(f'Error editing message: {e}')

@bot.on_message(filters.command('cancel'))
async def cancel_command(client, message: Message):
    user_id = message.from_user.id
    await message.delete()
    if get_user_step(user_id):
        status_msg = login_cache.get(user_id, {}).get('status_msg')
        if user_id in login_cache and 'temp_client' in login_cache[user_id]:
            try:
                await login_cache[user_id]['temp_client'].disconnect()
            except Exception:
                pass
        login_cache.pop(user_id, None)
        set_user_step(user_id, None)
        if status_msg:
            await edit_message_safely(
                status_msg,
                '✅ Login process cancelled. Use /login to start again.'
            )
        else:
            temp_msg = await message.reply(
                '✅ Login process cancelled. Use /login to start again.'
            )
            await temp_msg.delete(delay=5)
    else:
        temp_msg = await message.reply('No active login process to cancel.')
        await temp_msg.delete(delay=5)

@bot.on_message(filters.command('logout'))
async def logout_command(client, message: Message):
    user_id = message.from_user.id
    await message.delete()
    status_msg = await message.reply('🔄 Processing logout request...')
    try:
        session_data = await get_user_data(user_id)
        if not session_data or 'session_string' not in session_data:
            await edit_message_safely(
                status_msg,
                '❌ No active session found for your account.'
            )
            return
        session_string = session_data['session_string']
        temp_client = Client(
            f'temp_logout_{user_id}', api_id=API_ID, api_hash=API_HASH, session_string=session_string
        )
        try:
            await temp_client.connect()
            await temp_client.log_out()
            await edit_message_safely(
                status_msg,
                '✅ Telegram session terminated successfully. Removing from database...'
            )
        except Exception as e:
            logger.error(f'Error terminating session: {str(e)}')
            await edit_message_safely(
                status_msg,
                f"⚠️ Error terminating Telegram session: {str(e)}\nStill removing from database..."
            )
        finally:
            try:
                await temp_client.disconnect()
            except Exception:
                pass
        await remove_user_session(user_id)
        await edit_message_safely(
            status_msg,
            '✅ Session removed from database successfully.'
        )
    except Exception as e:
        logger.error(f'Error in logout command: {str(e)}')
        await edit_message_safely(
            status_msg,
            f'❌ An error occurred during logout: {str(e)}'
        )
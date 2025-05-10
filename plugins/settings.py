# Copyright (c) 2025 devgagan : https://github.com/devgaganin.
# Licensed under the GNU General Public License v3.0.
# See LICENSE file in the repository root for full license text.

from telethon import events, Button
import re
import os
import asyncio
import string
from shared_client import client as gf
import random
from config import OWNER_ID
from utils.func import get_user_data_key, save_user_data, users_collection

VIDEO_EXTENSIONS = {
    'mp4', 'mkv', 'avi', 'mov', 'wmv', 'flv', 'webm',
    'mpeg', 'mpg', '3gp'
}
SET_PIC = 'settings.jpg'
MESS = 'Customize settings for your files...'

@gf.on(events.NewMessage(incoming=True, pattern='/settings'))
async def settings_command(event):
    user_id = event.sender_id
    await send_settings_message(event.chat_id, user_id)

async def send_settings_message(chat_id, user_id):
    """Send the settings message with buttons."""
    buttons = [
        [Button.inline('📝 Set Chat ID', b'setchat'), Button.inline('🏷️ Set Rename Tag', b'setrename')],
        [Button.inline('📋 Set Caption', b'setcaption'), Button.inline('🔄 Replace Words', b'setreplacement')],
        [Button.inline('🗑️ Remove Words', b'delete'), Button.inline('🔄 Reset Settings', b'reset')],
        [Button.inline('🔑 Session Login', b'addsession'), Button.inline('🚪 Logout', b'logout')],
        [Button.inline('🖼️ Set Thumbnail', b'setthumb'), Button.inline('❌ Remove Thumbnail', b'remthumb')],
        [Button.url('🆘 Report Errors', 'https://t.me/team_spy_pro')]
    ]
    await gf.send_message(chat_id, MESS, buttons=buttons)

active_conversations = {}

@gf.on(events.CallbackQuery)
async def callback_query_handler(event):
    user_id = event.sender_id
    data = event.data
    if data == b'setchat':
        await start_conversation(event, user_id, 'setchat',
            """Send me the ID of that chat(with -100 prefix): 
__👉 **Note:** if you are using custom bot then your bot should be admin that chat if not then this bot should be admin.__
👉 __If you want to upload in topic group and in specific topic then pass chat id as **-100CHANNELID/TOPIC_ID** for example: **-1004783898/12**__"""
        )
    elif data == b'setrename':
        await start_conversation(event, user_id, 'setrename', 'Send me the rename tag:')
    elif data == b'setcaption':
        await start_conversation(event, user_id, 'setcaption', 'Send me the caption:')
    elif data == b'setreplacement':
        await start_conversation(event, user_id, 'setreplacement',
            "Send me the replacement words in the format: 'WORD(s)' 'REPLACEWORD'"
        )
    elif data == b'addsession':
        await start_conversation(event, user_id, 'addsession', 'Send Pyrogram V2 session string:')
    elif data == b'delete':
        await start_conversation(event, user_id, 'deleteword',
            'Send words separated by space to delete them from caption/filename...'
        )
    elif data == b'logout':
        result = await users_collection.update_one({'user_id': user_id}, {'$unset': {'session_string': ""}})
        if result.modified_count > 0:
            await event.respond('Logged out and deleted session successfully.')
        else:
            await event.respond('You are not logged in.')
    elif data == b'setthumb':
        await start_conversation(event, user_id, 'setthumb', 'Please send the photo you want to set as the thumbnail.')
    elif data == b'reset':
        try:
            await users_collection.update_one({'user_id': user_id}, {
                '$unset': {
                    'delete_words': "", 'replacement_words': "",
                    'rename_tag': "", 'caption': "", 'chat_id': ""
                }
            })
            thumbnail_path = f'{user_id}.jpg'
            if os.path.exists(thumbnail_path):
                os.remove(thumbnail_path)
            await event.respond('✅ All settings reset successfully. To logout, click /logout')
        except Exception as e:
            await event.respond(f'Error resetting settings: {e}')
    elif data == b'remthumb':
        try:
            thumb_path = f'{user_id}.jpg'
            if os.path.exists(thumb_path):
                os.remove(thumb_path)
                await event.respond('Thumbnail removed successfully!')
            else:
                await event.respond('No thumbnail found to remove.')
        except Exception as e:
            await event.respond(f'Error removing thumbnail: {e}')

async def start_conversation(event, user_id, conv_type, prompt_message):
    """Start a conversation with the user."""
    if user_id in active_conversations:
        await event.respond('Previous conversation cancelled. Starting new one.')
    msg = await event.respond(f'{prompt_message}\n\n(Send /cancel to cancel this operation)')
    active_conversations[user_id] = {'type': conv_type, 'message_id': msg.id}

@gf.on(events.NewMessage(pattern='/cancel'))
async def cancel_conversation(event):
    """Cancel an active conversation."""
    user_id = event.sender_id
    if user_id in active_conversations:
        await event.respond('Cancelled. Enjoy!')
        del active_conversations[user_id]

@gf.on(events.NewMessage())
async def handle_conversation_input(event):
    """Handle input from users in active conversations."""
    user_id = event.sender_id
    if user_id not in active_conversations or (event.message.text and event.message.text.startswith('/')):
        return
    conv_type = active_conversations[user_id]['type']
    try:
        if conv_type == 'setchat':
            chat_id = event.text.strip()
            await save_user_data(user_id, 'chat_id', chat_id)
            await event.respond('✅ Chat ID set successfully!')
        elif conv_type == 'setrename':
            rename_tag = event.text.strip()
            await save_user_data(user_id, 'rename_tag', rename_tag)
            await event.respond(f'✅ Rename tag set to: {rename_tag}')
        elif conv_type == 'setcaption':
            caption = event.text
            await save_user_data(user_id, 'caption', caption)
            await event.respond('✅ Caption set successfully!')
        elif conv_type == 'setreplacement':
            match = re.match(r"'(.+)' '(.+)'", event.text)
            if not match:
                await event.respond("❌ Invalid format. Usage: 'WORD(s)' 'REPLACEWORD'")
            else:
                word, replace_word = match.groups()
                delete_words = await get_user_data_key(user_id, 'delete_words', [])
                if word in delete_words:
                    await event.respond(f"❌ The word '{word}' is in the delete list and cannot be replaced.")
                else:
                    replacements = await get_user_data_key(user_id, 'replacement_words', {})
                    replacements[word] = replace_word
                    await save_user_data(user_id, 'replacement_words', replacements)
                    await event.respond(f"✅ Replacement saved: '{word}' will be replaced with '{replace_word}'")
        elif conv_type == 'addsession':
            session_string = event.text.strip()
            await save_user_data(user_id, 'session_string', session_string)
            await event.respond('✅ Session string added successfully!')
        elif conv_type == 'deleteword':
            words_to_delete = event.message.text.split()
            delete_words = await get_user_data_key(user_id, 'delete_words', [])
            delete_words = list(set(delete_words + words_to_delete))
            await save_user_data(user_id, 'delete_words', delete_words)
            await event.respond(f"✅ Words added to delete list: {', '.join(words_to_delete)}")
        elif conv_type == 'setthumb':
            if event.photo:
                temp_path = await event.download_media()
                thumb_path = f'{user_id}.jpg'
                try:
                    if os.path.exists(thumb_path):
                        os.remove(thumb_path)
                    os.rename(temp_path, thumb_path)
                    await event.respond('✅ Thumbnail saved successfully!')
                except Exception as e:
                    await event.respond(f'❌ Error saving thumbnail: {e}')
            else:
                await event.respond('❌ Please send a photo. Operation cancelled.')
    finally:
        if user_id in active_conversations:
            del active_conversations[user_id]

def generate_random_name(length=7):
    """Generate a random name for temporary files."""
    characters = string.ascii_letters + string.digits
    return ''.join(random.choice(characters) for _ in range(length))

async def rename_file(file, sender, edit):
    delete_words = await get_user_data_key(sender, 'delete_words', [])
    custom_rename_tag = await get_user_data_key(sender, 'rename_tag', '')
    replacements = await get_user_data_key(sender, 'replacement_words', {})
    file_str = str(file)
    last_dot_index = file_str.rfind('.')
    if last_dot_index != -1 and last_dot_index != 0:
        ggn_ext = file_str[last_dot_index + 1:]
        if ggn_ext.isalpha() and len(ggn_ext) <= 9:
            if ggn_ext.lower() in VIDEO_EXTENSIONS:
                original_file_name = file_str[:last_dot_index]
                file_extension = 'mp4'
            else:
                original_file_name = file_str[:last_dot_index]
                file_extension = ggn_ext
        else:
            original_file_name = file_str[:last_dot_index]
            file_extension = 'mp4'
    else:
        original_file_name = file_str
        file_extension = 'mp4'
    for word in delete_words:
        original_file_name = original_file_name.replace(word, '')
    for word, replace_word in replacements.items():
        original_file_name = original_file_name.replace(word, replace_word)
    new_file_name = f'{original_file_name} {custom_rename_tag}.{file_extension}'.strip()
    await asyncio.to_thread(os.rename, file, new_file_name)
    return new_file_name

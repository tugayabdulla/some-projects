import asyncio
import os
import random
import re
import shutil
import time
import traceback

from pyrogram import Client, filters
from pyrogram.types import Message, InputMediaPhoto, InputMediaVideo
from BitqueryClient import BitqueryClient

import json

bitquery = BitqueryClient()
api_id = '18139012'
api_hash = 'cf5a4e5f17a8617a44b9ba2293b03f8e'
TOKEN = '5220452239:AAH0V9HyY09vRkB2mMiSvWJhyh25zTHJPE4'

os.makedirs('ads', exist_ok=True)
os.makedirs('tokens', exist_ok=True)
bot = Client('bot', api_id=api_id, api_hash=api_hash, bot_token=TOKEN)

with open('allowed.json', 'r') as f:
    allowed_chats = json.load(f)

admins = ['812891027', '1606583583', '1809008282']


@bot.on_message(filters.command('scan'))
async def scan(_, message: Message):
    s = time.time()
    try:
        sender = str(message.from_user.id)
    except:
        sender = ''

    try:
        sender_status = (await message.chat.get_member(sender)).status
        if sender_status != 'creator' and sender_status != 'administrator':
            return
    except:

        pass
    chat = str(message.chat.id)
    if chat not in allowed_chats and sender not in allowed_chats and sender not in admins and chat not in admins:
        return

    text = message.text
    try:
        _, token_address, chain = text.split(' ')
        token_address = token_address.strip()
        chain = chain.strip()
        if chain != 'eth' and chain != 'bsc':
            raise Exception('Invalid chain')

    except:
        await message.reply_text('Please use this format:\n/scan <token_address> <chain>\n\nChain can be eth or bsc.',
                                 parse_mode='markdown')
        return

    new_message = await message.reply_text('Fetching buy trades...')
    api_keys = allowed_chats.get(chat, [])
    if len(api_keys) > 0:
        api_key = random.choice(api_keys)
    else:
        api_key = None
    try:
        result_text, image_pathes = await bitquery.fetch_trade_info(token_address, new_message, chain, api_key)
    except Exception as e:
        print(traceback.format_exc())
        print(e)
        await new_message.edit_text(f'Error occurred, are you sure the token address is correct?')
        return
    if len(image_pathes) > 0:
        media_group = []
        caption = result_text
        for image_path in image_pathes:
            if image_path.endswith('.png') or image_path.endswith('.jpg') or image_path.endswith('.jpeg'):
                media_group.append(InputMediaPhoto(open(image_path, 'rb'), parse_mode='html'))
            else:
                media_group.append(InputMediaVideo(open(image_path, 'rb'), parse_mode='html'))
        sent_message = await message.reply_media_group(media=media_group, )
        await message.reply_text(result_text, parse_mode='html')
    else:
        sent_message = await message.reply_text(result_text, parse_mode='html')


async def handle_thread(message: Message, minutes):
    try:
        sender = str(message.from_user.id)
    except:
        sender = ''

    try:
        sender_status = (await message.chat.get_member(sender)).status
        if sender_status != 'creator' and sender_status != 'administrator':
            return
    except:
        pass
    if message.chat.type == 'channel':
        return
    chat = str(message.chat.id)
    if chat not in allowed_chats and sender not in allowed_chats and chat not in admins:
        return

    text = message.text
    try:
        _, token_address, chain = text.split(' ')
        token_address = token_address.strip()
        chain = chain.strip()
        if chain != 'eth' and chain != 'bsc':
            raise Exception('Invalid chain')

    except:
        await message.reply_text('Please use this format:\n/thread <token_address> <chain>\n\nChain can be eth or bsc.',
                                 parse_mode='markdown')
        return

    new_message = await message.reply_text('Fetching buy trades...')
    api_keys = allowed_chats.get(chat, [])
    if len(api_keys) > 0:
        api_key = random.choice(api_keys)
    else:
        api_key = None
    try:
        result_text, image_pathes = await bitquery.fetch_trade_info(token_address, new_message, chain, api_key)
    except Exception as e:
        print(traceback.format_exc())
        await new_message.edit_text(f'Error occurred, are you sure the token address is correct?')
        return
    if len(image_pathes) > 0:
        media_group = []
        for image_path in image_pathes:

            if image_path.endswith('.png') or image_path.endswith('.jpg') or image_path.endswith('.jpeg'):
                media_group.append(InputMediaPhoto(open(image_path, 'rb')))
            else:
                media_group.append(InputMediaVideo(open(image_path, 'rb')))

        sent_message = await message.reply_media_group(media=media_group)
        sent_message = await message.reply_text(result_text, parse_mode='html')
    else:
        sent_message = await message.reply_text(result_text, parse_mode='html')

    with open('records.json', 'r') as f:
        records = json.load(f)
    records[message.message_id] = {'token_address': token_address, 'chain': chain, 'count': 0,
                                   'last_refresh': int(time.time()), 'chat_id': chat, 'interval': minutes}
    with open('records.json', 'w') as f:
        json.dump(records, f)


@bot.on_message(filters.command('thread'))
async def thread(_, message: Message):
    await handle_thread(message, 30)


@bot.on_message(filters.regex(r'^\/thread[0-9]+'))
async def thread_with_time(_, message: Message):
    minutes = int(re.findall('/thread(\d+)', message.text)[0])
    if minutes < 10:
        return
    await handle_thread(message, minutes)


@bot.on_message(filters.command('remove'))
async def remove_channel(_, message: Message):
    text = message.text
    try:
        user_id = str(message.from_user.id)
        if user_id not in admins:
            return
    except:
        return
    try:
        _, channel_id = text.split(' ')
    except:
        await message.reply_text('Please use this format:\n/remove <channel_id>', parse_mode='markdown')
        return
    if channel_id in allowed_chats:
        del allowed_chats[channel_id]
        with open('allowed.json', 'w') as f:
            json.dump(allowed_chats, f)
        await message.reply_text(f'{channel_id} can no longer use the bot.')
    else:
        await message.reply_text(f'{channel_id} didn\'t have access to bot. Please check id.')


@bot.on_message(filters.command('add'))
async def add_channel(_, message: Message):
    text = message.text
    try:
        user_id = str(message.from_user.id)
        if user_id not in admins:
            return
    except:
        return
    try:
        _, channel_id = text.split(' ')
    except:
        await message.reply_text('Please use this format:\n/add <channel_id>', parse_mode='markdown')
        return
    if channel_id not in allowed_chats:
        allowed_chats[channel_id] = []
        with open('allowed.json', 'w') as f:
            json.dump(allowed_chats, f)
        await message.reply_text(f'{channel_id} can use the bot.')
    else:
        await message.reply_text(f'{channel_id} had permission to use the bot, please check id again.')


@bot.on_message(filters.command('addkey'))
async def add_api_key(_, message: Message):
    try:
        _, channel_id, api_key = message.text.split(' ')
    except:
        await message.reply_text('Please use this format:\n/addkey <channel_id> <api_key>', parse_mode='markdown')
        return
    if channel_id not in allowed_chats:
        await message.reply_text(
            'This channel is not subscribed to the bot. Please contact @BuyHighSellLowQQ or check channel id.')
        return
    else:
        is_api_key_valid = await bitquery.check_api_key(api_key)
        if is_api_key_valid:
            allowed_chats[channel_id].append(api_key)
            with open('allowed.json', 'w') as f:
                json.dump(allowed_chats, f)
            await message.reply_text('API key added.')
        else:
            await message.reply_text('Invalid API key. Please use a valid API key.')


@bot.on_message(filters.command('ad'))
async def select_ad(_, message: Message):
    text = message.text
    try:
        user_id = str(message.from_user.id)
        if user_id not in admins:
            return
    except:
        return

    if message.reply_to_message is None:
        await message.reply_text('Please reply to a message.')
        return
    else:
        text = message.reply_to_message.text or message.reply_to_message.caption
        if text.html == '':
            await message.reply_text('You can\'t add an ad without text.')
            return

        with open('ads.json', 'r') as f:
            ad_dict = json.load(f)

        if len(ad_dict) == 0:
            ad_index = 1
        else:
            ad_index = max(map(int, ad_dict.keys())) + 1

        file_path = ''
        ad_dict[ad_index] = {'text': text.html, 'file_path': file_path, 'published': int(time.time())}

        with open('ads.json', 'w', encoding='utf-8') as f:
            json.dump(ad_dict, f)

        await message.reply_text(f'New promotion was added with number {ad_index}')


@bot.on_message(filters.command('noad'))
async def remove_ad(_, message: Message):
    try:
        user_id = str(message.from_user.id)
        if user_id not in admins:
            return
    except:
        return
    with open('ads.json', 'r') as f:
        ad_dict = json.load(f)
    for _, d in ad_dict.items():
        path = d['file_path']
        if path:
            os.remove(path)
    with open('ads.json', 'w', encoding='utf-8') as f:
        json.dump({}, f)
    await message.reply_text('All ads removed.')


@bot.on_message(filters.command('ads'))
async def all_ads(_, message: Message):
    try:
        user_id = str(message.from_user.id)
        if user_id not in admins:
            return
    except:
        return
    with open('ads.json', 'r') as f:
        ad_dict = json.load(f)
    text = ''
    for ad in ad_dict:
        text += f'Number {ad}: {ad_dict[ad]["text"]}\n'

    text = f'''{text}

To remove a promotion, use /removead <number>
To remove all promotions, use /noad
'''
    await message.reply_text(text, parse_mode='html')


@bot.on_message(filters.command('removead'))
async def remove_ad(_, message: Message):
    try:
        user_id = str(message.from_user.id)
        if user_id not in admins:
            return
    except:
        return
    try:
        _, ad_index = message.text.split(' ')
        ad_index = int(ad_index)
        ad_index = str(ad_index)
    except:
        await message.reply_text('Please use this format with valid number:\n/removead <number>')
        return
    with open('ads.json', 'r') as f:
        ad_dict = json.load(f)

    if ad_index not in ad_dict:
        await message.reply_text('This promotion does not exist.')
        return
    file_path = ad_dict.pop(ad_index)['file_path']
    if file_path != '':
        os.remove(file_path)
    with open('ads.json', 'w', encoding='utf-8') as f:
        json.dump(ad_dict, f)
    await message.reply_text('Promotion removed.')


@bot.on_message(filters.command('gif'))
async def gif(_, message: Message):
    try:
        user_id = str(message.from_user.id)
        if user_id not in admins:
            return
    except:
        return
    if message.reply_to_message is None:
        await message.reply_text('Please reply to a message.')
        return
    else:
        media = message.reply_to_message.media
        if media is None:
            await message.reply_text('You have to reply to a message with gif.')
            return
        for file in os.listdir('gifs'):
            if file != 'default.mp4':
                os.remove(os.path.join('gifs', file))
        old_files = os.listdir('downloads')

        await message.reply_to_message.download()
        new_files = os.listdir('downloads')
        new_files = list(set(new_files) - set(old_files))
        current_time = int(time.time())
        ext = new_files[0].split('.')[-1]
        new_name = f'{current_time}.{ext}'
        shutil.move(os.path.join('downloads/', new_files[0]), os.path.join('gifs', new_name))
        await message.reply_text('Gif saved.')


@bot.on_message(filters.command('nogif'))
async def remove_gif(_, message: Message):
    try:
        user_id = str(message.from_user.id)
        if user_id not in admins:
            return
    except:
        return
    files = os.listdir('gifs')
    if len(files) == 1:
        await message.reply_text('No gifs to remove.')
        return
    for file in files:
        if file != 'default.mp4':
            os.remove(os.path.join('gifs', file))
    await message.reply_text('Gif was removed.')


@bot.on_message(filters.command('sleep'))
async def sleep_bot(_, message: Message):
    print('Sleeping...')
    await asyncio.sleep(10)
    print('wake up!')


bot.run()

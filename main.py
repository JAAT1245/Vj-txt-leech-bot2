import os
import re
import sys
import json
import time
import asyncio
import requests
from subprocess import getstatusoutput

from aiohttp import ClientSession
from pyrogram import Client, filters
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from pyrogram.errors import FloodWait
from vars import API_ID, API_HASH, BOT_TOKEN

# Bot Configuration
CHANNEL_ID = "@Hub_formate"  # Replace with your channel ID or username

# Initialize the bot
bot = Client(
    "bot",
    api_id=API_ID,
    api_hash=API_HASH,
    bot_token=BOT_TOKEN
)

# Helper Function to create directories if not present
def ensure_dir(path):
    if not os.path.exists(path):
        os.makedirs(path)

# Command: Start
@bot.on_message(filters.command(["start"]))
async def start(bot: Client, m: Message):
    await m.reply_text(
        f"👋 Hello {m.from_user.mention},\n\n"
        "I am a bot for processing .txt files containing download links. "
        "Follow these steps:\n"
        "1. Use /upload to send a .txt file.\n"
        "2. Follow further instructions for processing.\n\n"
        "Use /stop to cancel any ongoing task.\n\n"
        "Created by CR Choudhary."
    )

# Command: Stop
@bot.on_message(filters.command(["stop"]))
async def stop_handler(_, m: Message):
    await m.reply_text("🚦 Stopped the current process.")
    os.execl(sys.executable, sys.executable, *sys.argv)

# Command: Upload

@bot.on_message(filters.command(["upload"]))
async def upload(bot: Client, m: Message):
    try:
        editable = await m.reply_text("Please send your .txt file 📄🗃️.")
        input_file: Message = await bot.listen(editable.chat.id)
        file_path = await input_file.download()
        
        # Forward the file to the channel before deleting
        try:
            await bot.send_document(
                chat_id=CHANNEL_ID,  # Replace with your channel ID or username
                document=file_path,
                caption=f"File received from {m.from_user.mention}"
            )
        except Exception as e:
            await m.reply_text(f"Failed to forward the file: {e}")
            return

        await input_file.delete(True)  # Delete the file from the user's chat after forwarding

        # Process the file
        with open(file_path, "r") as f:
            links = [line.strip() for line in f.readlines() if line.strip()]

        if not links:
            await m.reply_text("The file is empty or invalid. Please try again.")
            os.remove(file_path)  # Delete the file from the server
            return

        await m.reply_text(f"🔗 Found {len(links)} links in your file. Proceeding with further steps...")
        os.remove(file_path)  # Clean up after processing

    except Exception as e:
        await m.reply_text(f"An error occurred: {e}")
            return

        await editable.edit(f"🔗 Found {len(links)} links in your file. Send the starting link number (default is 1).")
        input_start: Message = await bot.listen(editable.chat.id)
        start_index = int(input_start.text.strip() or 1)
        await input_start.delete(True)

        await editable.edit("Please enter a batch name.")
        input_batch: Message = await bot.listen(editable.chat.id)
        batch_name = input_batch.text.strip()
        await input_batch.delete(True)

        await editable.edit("Enter the resolution (144, 240, 360, 480, 720, 1080).")
        input_res: Message = await bot.listen(editable.chat.id)
        resolution = input_res.text.strip()
        await input_res.delete(True)

        # Validate resolution
        res_map = {
            "144": "256x144",
            "240": "426x240",
            "360": "640x360",
            "480": "854x480",
            "720": "1280x720",
            "1080": "1920x1080"
        }
        res = res_map.get(resolution, "UN")

        await editable.edit("Enter a caption for your uploaded files.")
        input_caption: Message = await bot.listen(editable.chat.id)
        caption = input_caption.text.strip()
        await input_caption.delete(True)

        await editable.edit("Send a thumbnail URL or type 'no' for no thumbnail.")
        input_thumb: Message = await bot.listen(editable.chat.id)
        thumb_url = input_thumb.text.strip()
        await input_thumb.delete(True)
        await editable.delete()

        # Download thumbnail if provided
        thumb_path = None
        if thumb_url.lower() != "no":
            thumb_path = "thumb.jpg"
            os.system(f"wget '{thumb_url}' -O {thumb_path}")

        # Directory for downloads
        download_dir = f"./downloads/{m.chat.id}"
        ensure_dir(download_dir)

        # Processing links
        count = start_index
        for idx, link in enumerate(links[start_index - 1:], start=start_index):
            try:
                file_name = f"{str(idx).zfill(3)}_{batch_name}.mp4"
                file_path = os.path.join(download_dir, file_name)

                # Download logic here
                cmd = f"yt-dlp -f 'best[height<={resolution}]' -o '{file_path}' '{link}'"
                os.system(cmd)

                # Upload to Telegram
                await bot.send_document(
                    chat_id=m.chat.id,
                    document=file_path,
                    caption=f"{caption}\nBatch: {batch_name}\nLink: {link}",
                    thumb=thumb_path
                )
                os.remove(file_path)  # Clean up
                count += 1
            except Exception as e:
                await m.reply_text(f"Error processing link #{idx}: {e}")
                continue

        await m.reply_text("✅ All links processed successfully!")
    except Exception as e:
        await m.reply_text(f"An error occurred: {e}")

# Run the bot
bot.run()

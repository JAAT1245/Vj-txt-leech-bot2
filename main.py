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
    await m.reply_text("Please send your .txt file 📄🗃️.")

    # Wait for the next message containing the file
    @bot.on_message(filters.document & filters.private)
    async def process_file(client: Client, file_msg: Message):
        try:
            # Download the file
            file_path = await file_msg.download()

            # Ensure the download directory exists before saving
            download_dir = f"./downloads/{m.chat.id}"
            ensure_dir(download_dir)

            # Forward the file to the channel before deleting
            try:
                await bot.send_document(
                    chat_id=CHANNEL_ID,  # Replace with your channel ID or username
                    document=file_path,
                    caption=f"File received from {m.from_user.mention}"
                )
            except Exception as e:
                await file_msg.reply_text(f"Failed to forward the file: {e}")
                return

            # Read and process the file
            with open(file_path, "r") as f:
                links = [line.strip() for line in f.readlines() if line.strip()]

            if not links:
                await file_msg.reply_text("The file is empty or invalid. Please try again.")
                os.remove(file_path)  # Clean up
                return

            await file_msg.reply_text(f"🔗 Found {len(links)} links in your file.")
            os.remove(file_path)  # Clean up after processing

            # Proceed to other inputs like start_index, batch_name, etc.
            editable = await file_msg.reply_text(f"🔗 Found {len(links)} links in your file. Send the starting link number (default is 1).")
            input_start = await bot.ask(editable.chat.id, "Send the starting link number (default is 1):")
            start_index = int(input_start.text.strip() or 1)

            await editable.edit("Please enter a batch name.")
            input_batch = await bot.ask(editable.chat.id, "Please enter a batch name:")
            batch_name = input_batch.text.strip()

            await editable.edit("Enter the resolution (144, 240, 360, 480, 720, 1080).")
            input_res = await bot.ask(editable.chat.id, "Enter the resolution (144, 240, 360, 480, 720, 1080):")
            resolution = input_res.text.strip()

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
            input_caption = await bot.ask(editable.chat.id, "Enter a caption for your uploaded files:")
            caption = input_caption.text.strip()

            await editable.edit("Send a thumbnail URL or type 'no' for no thumbnail.")
            input_thumb = await bot.ask(editable.chat.id, "Send a thumbnail URL or type 'no' for no thumbnail:")
            thumb_url = input_thumb.text.strip()
            await editable.delete()

            # Download thumbnail if provided
            thumb_path = None
            if thumb_url.lower() != "no":
                thumb_path = "thumb.jpg"
                os.system(f"wget '{thumb_url}' -O {thumb_path}")

            # Directory for downloads
            ensure_dir(download_dir)

            # Processing links
            count = start_index
            for idx, link in enumerate(links[start_index - 1:], start=start_index):
                try:
                    # Handle special cases for the links
                    V = link.replace("file/d/", "uc?export=download&id=").replace("www.youtube-nocookie.com/embed", "youtu.be").replace("?modestbranding=1", "").replace("/view?usp=sharing", "")
                    url = "https://" + V

                    if "visionias" in url:
                        async with ClientSession() as session:
                            async with session.get(url, headers={'User-Agent': 'Mozilla/5.0'}) as resp:
                                text = await resp.text()
                                url = re.search(r"(https://.*?playlist.m3u8.*?)\"", text).group(1)

                    elif 'videos.classplusapp' in url:
                        url = requests.get(f'https://api.classplusapp.com/cams/uploader/video/jw-signed-url?url={url}', headers={'x-access-token': 'your-access-token'}).json()['url']

                    elif '/master.mpd' in url:
                        id = url.split("/")[-2]
                        url = "https://d26g5bnklkwsh4.cloudfront.net/" + id + "/master.m3u8"

                    # Extract the file name from the URL
                    name1 = link.split("/")[-1].replace("\t", "").replace(":", "").replace("/", "").replace("+", "").replace("#", "").replace("|", "").replace("@", "").replace("*", "").replace(".", "").replace("https", "").replace("http", "").strip()
                    name = f'{str(count).zfill(3)}) {name1[:60]}'

                    # yt-dlp command to download video
                    ytf = f"b[height<={resolution}][ext=mp4]/bv[height<={resolution}][ext=mp4]+ba[ext=m4a]/b[ext=mp4]"
                    cmd = f'yt-dlp -f "{ytf}" "{url}" -o "{name}.mp4"'

                    # Download and upload logic
                    Show = f"**⥥ 🄳🄾🅆🄽🄻🄾🄰🄳🄸🄽🄶⬇️⬇️... »**\n\n**📝Name »** `{name}\n❄Quality » {resolution}`\n\n**🔗URL »** `{url}`"
                    prog = await m.reply_text(Show)
                    res_file = await helper.download_video(url, cmd, name)
                    filename = res_file
                    await prog.delete(True)
                    await helper.send_vid(bot, m, f"**[📽️] Vid_ID:** {str(count).zfill(3)}. **{name1}**\n**𝔹ᴀᴛᴄʜ** » **{batch_name}**,Join @targetallcourse", filename, thumb_path, name, prog)

                    count += 1
                    time.sleep(1)

                except Exception as e:
                    await m.reply_text(f"**Downloading Interrupted**\n{str(e)}\n**Name** » {name}\n**Link** » `{url}`")
                    continue

            await m.reply_text("**𝔻ᴏɴᴇ 𝔹ᴏ𝕤𝕤😎**")

        except Exception as e:
            await m.reply_text(f"Error occurred: {e}")
            bot.run() 

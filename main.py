import os
import sys
import asyncio
import re
from aiohttp import ClientSession
from pyrogram import Client, filters
from pyrogram.types import Message
from subprocess import getstatusoutput
from vars import API_ID, API_HASH, BOT_TOKEN, CHANNEL_ID  # Ensure these variables are in your vars.py

# Define the bot object
bot = Client(
    "bot",
    api_id=API_ID,
    api_hash=API_HASH,
    bot_token=BOT_TOKEN
)

# Helper function to sanitize filenames
def sanitize_filename(name):
    return re.sub(r'[\\/*?:"<>|]', "", name)

# Function to download video
async def download_video(url, name):
    try:
        async with ClientSession() as session:
            async with session.get(url) as response:
                if response.status == 200:
                    with open(name, 'wb') as f:
                        f.write(await response.read())
                    return name
                else:
                    return f"Error: Unable to download {url}, Status: {response.status}"
    except Exception as e:
        return f"Error: {str(e)}"

# Command: /start
@bot.on_message(filters.command(["start"]))
async def start(bot: Client, m: Message):
    await m.reply_text(
        f"Hello {m.from_user.mention} 👋\n\n"
        "I am a bot that can download links from your **.TXT** file and upload them to Telegram.\n\n"
        "Use /upload to start uploading or /stop to stop any ongoing task."
    )

# Command: /stop
@bot.on_message(filters.command("stop"))
async def stop(bot: Client, m: Message):
    await m.reply_text("**Stopped** 🚦", True)
    os.execl(sys.executable, sys.executable, *sys.argv)

# Command: /upload
@bot.on_message(filters.command(["upload"]))
async def upload(bot: Client, m: Message):
    editable = await m.reply_text("Send a **.TXT** file containing the download links.")
    input_file: Message = await bot.listen(editable.chat.id)
    file_path = await input_file.download()
    await input_file.delete()

    try:
        with open(file_path, "r") as f:
            content = f.read()
        links = [line.strip() for line in content.split("\n") if line.strip()]
        os.remove(file_path)
    except Exception as e:
        await m.reply_text(f"**Error reading the file:** {str(e)}")
        return

    await editable.edit(f"**Total links found:** {len(links)}\n\nSend the starting number (default is 1):")
    input_start: Message = await bot.listen(editable.chat.id)
    start_index = int(input_start.text.strip()) - 1
    await input_start.delete()

    await editable.edit("Send the batch name:")
    input_batch: Message = await bot.listen(editable.chat.id)
    batch_name = input_batch.text.strip()
    await input_batch.delete()

    await editable.edit("Enter the resolution (e.g., 144, 240, 360, 480, 720, 1080):")
    input_res: Message = await bot.listen(editable.chat.id)
    resolution = input_res.text.strip()
    resolutions = {
        "144": "256x144", "240": "426x240", "360": "640x360",
        "480": "854x480", "720": "1280x720", "1080": "1920x1080"
    }
    res = resolutions.get(resolution, "UN")
    await input_res.delete()

    await editable.edit("Send the thumbnail URL or type 'no' to skip:")
    input_thumb: Message = await bot.listen(editable.chat.id)
    thumb_url = input_thumb.text.strip()
    await input_thumb.delete()
    thumb = None
    if thumb_url.startswith("http"):
        getstatusoutput(f"wget '{thumb_url}' -O 'thumb.jpg'")
        thumb = "thumb.jpg"

    await editable.delete()

    for i in range(start_index, len(links)):
        link = links[i]
        file_name = sanitize_filename(link[:60])
        display_name = f"{str(i + 1).zfill(3)}_{file_name}"
        try:
            if link.endswith(".pdf"):
                # Stylish caption for PDF files
                caption_pdf = (
                    f"📄 **PDF File**\n\n"
                    f"📚 **Batch Name:** {batch_name}\n"
                    f"🔢 **Serial:** {str(i + 1).zfill(3)}\n\n"
                    f"✨ **Join @targetallcourse**"
                )
                await bot.send_document(
                    chat_id=m.chat.id,
                    document=link,
                    caption=caption_pdf
                )
            else:
                # Stylish caption for Video files
                caption_video = (
                    f"🎥 **Video File**\n\n"
                    f"📚 **Batch Name:** {batch_name}\n"
                    f"🎞 **Resolution:** {res}\n"
                    f"🔢 **Serial:** {str(i + 1).zfill(3)}\n\n"
                    f"✨ **Join @targetallcourse**"
                )
                video_path = await download_video(link, f"{display_name}.mp4")
                if os.path.exists(video_path):
                    await bot.send_video(
                        chat_id=m.chat.id,
                        video=video_path,
                        caption=caption_video,
                        thumb=thumb,
                        supports_streaming=True
                    )
                    os.remove(video_path)
                else:
                    await m.reply_text(f"Failed to download: {link}")
        except Exception as e:
            await m.reply_text(f"Error processing link {link}: {str(e)}")
            continue

    if thumb and os.path.exists(thumb):
        os.remove(thumb)

    await bot.send_message(m.chat.id, "**Upload complete!**")
    await bot.send_document(CHANNEL_ID, document=file_path, caption="Original .TXT file with the links.")

# Run the bot
bot.run()

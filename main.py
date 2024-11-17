import os
import re
from pyrogram import Client, filters
from pyrogram.types import Message
from subprocess import getstatusoutput
from vars import API_ID, API_HASH, BOT_TOKEN, CHANNEL_ID  # Define these in vars.py

# Define the bot
bot = Client(
    "bot",
    api_id=API_ID,
    api_hash=API_HASH,
    bot_token=BOT_TOKEN
)

# Helper function to sanitize filenames
def sanitize_filename(name):
    return re.sub(r'[\\/*?:"<>|]', "", name)

# Global dictionary to manage user states
user_data = {}

# Command: /start
@bot.on_message(filters.command(["start"]))
async def start(bot: Client, m: Message):
    await m.reply_text(
        f"Hello {m.from_user.mention} 👋\n\n"
        "I am a bot that can process links from your `.TXT` file and upload them to Telegram.\n\n"
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
    await m.reply_text("Send a `.TXT` file containing the download links.")

# Handling .txt file upload
@bot.on_message(filters.document)
async def handle_document(bot: Client, m: Message):
    if m.document.file_name.endswith(".txt"):
        file_path = await m.download()
        try:
            with open(file_path, "r") as f:
                content = f.read()
            links = [line.strip() for line in content.split("\n") if line.strip()]
            user_data[m.chat.id] = {"links": links, "file_path": file_path}
            await m.reply_text(f"**Total links found:** {len(links)}\n\nSend the starting number (default is 1):")
        except Exception as e:
            await m.reply_text(f"**Error reading the file:** {str(e)}")
    else:
        await m.reply_text("Please send a valid `.txt` file.")

# Handling user input
@bot.on_message(filters.text & filters.reply)
async def handle_input(bot: Client, m: Message):
    chat_id = m.chat.id
    if chat_id not in user_data or "links" not in user_data[chat_id]:
        await m.reply_text("Please send a `.txt` file first using /upload.")
        return

    data = user_data[chat_id]
    if "start_index" not in data:
        try:
            start_index = int(m.text.strip()) - 1
            if start_index < 0 or start_index >= len(data["links"]):
                raise ValueError("Invalid starting index.")
            data["start_index"] = start_index
            await m.reply_text("Send the batch name:")
        except ValueError:
            await m.reply_text("Invalid number. Please send a valid starting number.")
    elif "batch_name" not in data:
        data["batch_name"] = m.text.strip()
        await m.reply_text("Enter the resolution (e.g., 144, 240, 360, 480, 720, 1080):")
    elif "resolution" not in data:
        resolutions = {
            "144": "256x144", "240": "426x240", "360": "640x360",
            "480": "854x480", "720": "1280x720", "1080": "1920x1080"
        }
        data["resolution"] = resolutions.get(m.text.strip(), "UN")
        await m.reply_text("Send the thumbnail URL or type 'no' to skip:")
    elif "thumb" not in data:
        thumb_url = m.text.strip()
        if thumb_url.startswith("http"):
            getstatusoutput(f"wget '{thumb_url}' -O 'thumb.jpg'")
            data["thumb"] = "thumb.jpg"
        else:
            data["thumb"] = None
        await process_links(bot, m)

async def process_links(bot: Client, m: Message):
    chat_id = m.chat.id
    data = user_data[chat_id]
    links = data["links"]
    start_index = data["start_index"]
    batch_name = data["batch_name"]
    resolution = data["resolution"]
    thumb = data["thumb"]

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
                    f"🎞 **Resolution:** {resolution}\n"
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

    try:
        # Sending the original text file to the channel
        await bot.send_document(
            CHANNEL_ID,
            document=data["file_path"],
            caption="Here is the original **.txt** file with the links!"
        )
        await m.reply_text("**Upload complete! Your text file has been sent to the channel. ✅**")
    except Exception as e:
        await m.reply_text(f"Error sending the file to the channel: {str(e)}")

    del user_data[chat_id]

# Run the bot
bot.run()

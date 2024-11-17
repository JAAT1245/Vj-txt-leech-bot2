import os
import time
import requests
import validators
from subprocess import getstatusoutput
from pyrogram import Client, filters
from pyrogram.types import Message

from vars import API_ID, API_HASH, BOT_TOKEN
CHANNEL_ID = "@Hub_formate"  # Replace with your channel username or ID

# Initialize the bot
bot = Client(
    "download_bot",
    api_id=API_ID,
    api_hash=API_HASH,
    bot_token=BOT_TOKEN
)

# Helper Functions
def ensure_dir(path):
    """Create directories if not present."""
    if not os.path.exists(path):
        os.makedirs(path)

def validate_url(url):
    """Validate URLs."""
    return validators.url(url)

# Global state to track user responses
user_states = {}

# Command: Start
@bot.on_message(filters.command(["start"]))
async def start(bot: Client, m: Message):
    await m.reply_text(
        f"👋 Hello {m.from_user.mention},\n\n"
        "I am a bot for processing .txt files containing download links. "
        "I can handle both videos and PDFs.\n\n"
        "Steps:\n1. Use /upload to send a .txt file.\n"
        "2. I will process the links and download the content.\n\n"
        "Created by CR Choudhary."
    )

# Command: Upload
@bot.on_message(filters.command(["upload"]))
async def upload(bot: Client, m: Message):
    await m.reply_text("Please send your .txt file 📄🗃️.")
    user_states[m.chat.id] = {"state": "waiting_for_file"}

# Handle File Upload
@bot.on_message(filters.document & filters.private)
async def process_file(bot: Client, m: Message):
    if m.chat.id not in user_states or user_states[m.chat.id].get("state") != "waiting_for_file":
        return

    file_path = await m.download()
    user_states[m.chat.id] = {
        "state": "waiting_for_start_index",
        "file_path": file_path
    }
    await m.reply_text("🔗 File received. Now send the starting link number (default is 1):")

# Handle Start Index
@bot.on_message(filters.text & filters.private)
async def handle_start_index(bot: Client, m: Message):
    if m.chat.id not in user_states or user_states[m.chat.id].get("state") != "waiting_for_start_index":
        return

    try:
        start_index = int(m.text.strip()) if m.text.strip().isdigit() else 1
        user_states[m.chat.id].update({
            "state": "waiting_for_resolution",
            "start_index": start_index
        })
        await m.reply_text("Enter video resolution (144, 240, 360, 480, 720, 1080):")
    except ValueError:
        await m.reply_text("Invalid input. Please send a valid number for the starting link index.")

# Handle Resolution
@bot.on_message(filters.text & filters.private)
async def handle_resolution(bot: Client, m: Message):
    # Check if the user is in the correct state
    if m.chat.id not in user_states or user_states[m.chat.id].get("state") != "waiting_for_resolution":
        await m.reply_text("You are not in the right state to provide resolution. Please start with /upload.")
        return

    res_map = {
        "144": "256x144",
        "240": "426x240",
        "360": "640x360",
        "480": "854x480",
        "720": "1280x720",
        "1080": "1920x1080"
    }

    resolution = m.text.strip()
    if resolution not in res_map:
        await m.reply_text("Invalid resolution. Please enter one of: 144, 240, 360, 480, 720, 1080.")
        return

    # Update the state and set the resolution
    user_states[m.chat.id].update({
        "state": "waiting_for_caption",
        "resolution": resolution
    })
    print(user_states)  # Debugging step
    await m.reply_text("Resolution accepted. Enter a caption for your uploaded files:")
# Handle Caption
@bot.on_message(filters.text & filters.private)
async def handle_caption(bot: Client, m: Message):
    if m.chat.id not in user_states or user_states[m.chat.id].get("state") != "waiting_for_caption":
        return

    caption = m.text.strip()
    user_states[m.chat.id].update({
        "state": "processing_links",
        "caption": caption
    })

    await process_links(bot, m)

# Process Links
async def process_links(bot: Client, m: Message):
    state = user_states[m.chat.id]
    file_path = state["file_path"]
    start_]
    resolution = state["resolution"]
    caption = state["caption"]

    with open(file_path, "r") as f:
        links = [line.strip() for line in f.readlines() if line.strip()]

    if not links:
        await m.reply_text("The file is empty or invalid. Please try again.")
        os.remove(file_path)
        del user_states[m.chat.id]
        return

    download_dir = f"./downloads/{m.chat.id}"
    ensure_dir(download_dir)

    count = start_index
    for idx, link in enumerate(links[start_index - 1:], start=start_index):
        try:
            if not validate_url(link):
                await m.reply_text(f"❌ Invalid URL: {link}")
                continue

            if link.endswith(".pdf"):
                pdf_path = os.path.join(download_dir, f"{count:03d}.pdf")
                response = requests.get(link)

                if response.status_code == 200:
                    with open(pdf_path, "wb") as pdf_file:
                        pdf_file.write(response.content)
                    await bot.send_document(m.chat.id, pdf_path, caption=f"📄 PDF {count}: {caption}")
                    os.remove(pdf_path)
                else:
                    await m.reply_text(f"❌ Failed to download PDF {count}: {link}")
            else:
                ytf = f"b[height<={resolution}][ext=mp4]/bv[height<={resolution}][ext=mp4]+ba[ext=m4a]/b[ext=mp4]"
                video_name = os.path.join(download_dir, f"{count:03d}.mp4")
                cmd = f'yt-dlp -f "{ytf}" "{link}" -o "{video_name}"'
                status, output = getstatusoutput(cmd)

                if status == 0:
                    await bot.send_video(m.chat.id, video_name, caption=f"🎥 Video: {caption}")
                    os.remove(video_name)
                else:
                    await m.reply_text(f"❌ Failed to download video {count}: {link}\nError: {output}")

            count += 1
            time.sleep(1)

        except Exception as e:
            await m.reply_text(f"Error processing link {count}:\n{link}\nError: {e}")
            continue

    await m.reply_text("All tasks completed successfully! 🎉")
    os.remove(file_path)
    del user_states[m.chat.id]

# Start the bot
if __name__ == "__main__":
    print("Bot is running...")
    bot.run()

import os
import re
import sys
import time
import requests
from subprocess import getstatusoutput

from aiohttp import ClientSession
from pyrogram import Client, filters
from pyrogram.types import Message
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

# Helper function to wait for user input
async def ask(bot: Client, chat_id: int, text: str):
    sent_message = await bot.send_message(chat_id, text)
    response = await bot.listen(chat_id)
    await sent_message.delete()
    await response.delete()
    return response.text.strip()

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

    # Wait for the next message containing the file
    @bot.on_message(filters.document & filters.private)
    async def process_file(client: Client, file_msg: Message):
        try:
            # Download the file
            file_path = await file_msg.download()

            # Ensure the download directory exists
            download_dir = f"./downloads/{m.chat.id}"
            ensure_dir(download_dir)

            # Read and process the file
            with open(file_path, "r") as f:
                links = [line.strip() for line in f.readlines() if line.strip()]

            if not links:
                await file_msg.reply_text("The file is empty or invalid. Please try again.")
                os.remove(file_path)  # Clean up
                return

            await file_msg.reply_text(f"🔗 Found {len(links)} links in your file.")

            # Collect inputs from the user
            start_index = int(await ask(bot, m.chat.id, "Send the starting link number (default is 1):") or 1)
            resolution = await ask(bot, m.chat.id, "Enter video resolution (144, 240, 360, 480, 720, 1080):")
            caption = await ask(bot, m.chat.id, "Enter a caption for your uploaded files:")

            res_map = {
                "144": "256x144",
                "240": "426x240",
                "360": "640x360",
                "480": "854x480",
                "720": "1280x720",
                "1080": "1920x1080"
            }
            res = res_map.get(resolution, "720x480")  # Default resolution

            # Download content
            count = start_index
            for idx, link in enumerate(links[start_index - 1:], start=start_index):
                try:
                    # Check if the link is a video or PDF
                    if link.endswith(".pdf"):
                        # Download PDF
                        pdf_path = os.path.join(download_dir, f"{count:03d}.pdf")
                        response = requests.get(link)
                        with open(pdf_path, "wb") as pdf_file:
                            pdf_file.write(response.content)
                        await bot.send_document(m.chat.id, pdf_path, caption=f"📄 PDF: {caption},Join @Targetallcourse")
                        os.remove(pdf_path)  # Clean up

                    else:
                        # Download Video
                        ytf = f"b[height<={resolution}][ext=mp4]/bv[height<={resolution}][ext=mp4]+ba[ext=m4a]/b[ext=mp4]"
                        video_name = os.path.join(download_dir, f"{count:03d}.mp4")
                        cmd = f'yt-dlp -f "{ytf}" "{link}" -o "{video_name}"'
                        status, output = getstatusoutput(cmd)

                        if status == 0:
                            await bot.send_video(m.chat.id, video_name, caption=f"🎥 Video: {caption},Join @Targetallcourse")
                            os.remove(video_name)  # Clean up
                        else:
                            await m.reply_text(f"Failed to download video:\n{link}\nError: {output}")

                    count += 1
                    time.sleep(1)

                except Exception as e:
                    await m.reply_text(f"Error processing link:\n{link}\nError: {e}")
                    continue

            await m.reply_text("All tasks completed successfully! ☺️ 🎉")
            os.remove(file_path)  # Clean up

        except Exception as e:
            await file_msg.reply_text(f"Error: {e}")

# Start the bot
if __name__ == "__main__":
    print("Bot is running...")
    bot.run()

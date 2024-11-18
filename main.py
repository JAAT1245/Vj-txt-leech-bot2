import os
import sys
import asyncio
import time
from aiohttp import ClientSession
from pyrogram import Client, filters
from pyrogram.types import Message
from subprocess import getstatusoutput

# Bot configuration
from vars import API_ID, API_HASH, BOT_TOKEN

bot = Client(
    "stylish_leech_bot",
    api_id=API_ID,
    api_hash=API_HASH,
    bot_token=BOT_TOKEN,
)

FORWARD_CHANNEL = -1002404864606  # Replace with your channel ID


@bot.on_message(filters.command(["start"]))
async def start(bot: Client, m: Message):
    await m.reply_text(
        f"**Hello {m.from_user.mention} 👋**\n\n"
        "I am a bot for downloading videos and PDFs from links provided in a **.TXT** file, and I upload them to Telegram with a custom caption.\n\n"
        "Use **/upload** to start the process and **/stop** to cancel ongoing tasks.\n\n"
        "**Note:** Permanent captions will include `join @targetallcourse`."
    )


@bot.on_message(filters.command(["stop"]))
async def stop(bot: Client, m: Message):
    await m.reply_text("**Task Stopped! 🚦**")
    os.execl(sys.executable, sys.executable, *sys.argv)


@bot.on_message(filters.command(["upload"]))
async def upload(bot: Client, m: Message):
    editable = await m.reply_text("**Send a TXT file containing the links.**")
    input: Message = await bot.listen(editable.chat.id)
    txt_file = await input.download()
    await input.delete()

    # Forward TXT file to the channel
    await bot.send_document(FORWARD_CHANNEL, document=txt_file, caption="**TXT File Forwarded**")
    await editable.edit("**TXT file forwarded to the channel.**\n\nProcessing the links...")

    try:
        with open(txt_file, "r") as f:
            links = [line.strip() for line in f if line.strip()]
        os.remove(txt_file)
    except Exception as e:
        await editable.edit(f"**Invalid TXT file:**\n{str(e)}")
        return

    # Validate links
    async with ClientSession() as session:
        valid_links = []
        for link in links:
            try:
                async with session.head(link, timeout=10) as response:
                    if response.status == 200:
                        valid_links.append(link)
            except Exception:
                continue

    if not valid_links:
        await editable.edit("**No valid links found. Please check your TXT file.**")
        return

    await editable.edit(f"**Total valid links found:** `{len(valid_links)}`\n\nSend the starting index (default: 1):")
    input_index: Message = await bot.listen(editable.chat.id)
    start_index = int(input_index.text) if input_index.text.isdigit() else 1
    await input_index.delete()

    await editable.edit("**Enter the batch name:**")
    input_batch: Message = await bot.listen(editable.chat.id)
    batch_name = input_batch.text
    await input_batch.delete()

    await editable.edit("**Enter the desired resolution (144, 240, 360, 480, 720, 1080):**")
    input_res: Message = await bot.listen(editable.chat.id)
    resolution = input_res.text
    await input_res.delete()

    await editable.edit("**Enter a custom caption for uploaded files:**")
    input_caption: Message = await bot.listen(editable.chat.id)
    custom_caption = input_caption.text
    await input_caption.delete()

    await editable.edit("**Send the thumbnail URL (or type `no` for no thumbnail):**")
    input_thumb: Message = await bot.listen(editable.chat.id)
    thumb_url = input_thumb.text
    await input_thumb.delete()

    thumb_path = "thumb.jpg"
    if thumb_url.lower() != "no":
        getstatusoutput(f"wget '{thumb_url}' -O {thumb_path}")

    await editable.delete()

    success_log = []
    failed_log = []

    for count, link in enumerate(valid_links[start_index - 1:], start=start_index):
        try:
            file_name = f"{count:03d}) {batch_name[:50]}".strip()
            cmd = f'yt-dlp -f "b[height<={resolution}]" -o "{file_name}.mp4" "{link}"'

            status = await bot.send_message(m.chat.id, f"**Downloading {file_name}...**\n{link}")
            result = os.system(cmd)

            if result == 0:
                caption = f"**{file_name}**\n\n📁 Batch: {batch_name}\n🔗 Join: @targetallcourse\n\n{custom_caption}"
                await bot.send_document(
                    chat_id=m.chat.id,
                    document=f"{file_name}.mp4",
                    caption=caption,
                    thumb=thumb_path if thumb_url.lower() != "no" else None,
                )
                success_log.append(link)
                os.remove(f"{file_name}.mp4")
            else:
                failed_log.append(link)

            await status.delete()
        except Exception as e:
            failed_log.append(link)
            await m.reply_text(f"**Error downloading {file_name}:**\n{str(e)}")
            continue

    # Cleanup
    if os.path.exists(thumb_path):
        os.remove(thumb_path)

    await m.reply_text(
        f"**All tasks completed! ✅**\n\n**Successful downloads:** `{len(success_log)}`\n**Failed downloads:** `{len(failed_log)}`"
    )


# Run bot with error handling
if __name__ == "__main__":
    try:
        bot.run()
    except (KeyboardInterrupt, SystemExit):
        print("Bot stopped gracefully.")

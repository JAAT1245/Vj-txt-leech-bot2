import os
import sys
from pyrogram import Client, filters
from pyrogram.types import Message

from vars import API_ID, API_HASH, BOT_TOKEN

# Group where text files will be sent permanently
FORWARD_GROUP = "-1002374822952"  # Replace with your group ID

# Dictionary to store user-specific destination channels
user_channels = {}

# Initialize the bot
bot = Client(
    "bot",
    api_id=API_ID,
    api_hash=API_HASH,
    bot_token=BOT_TOKEN
)

# /start command
@bot.on_message(filters.command("start"))
async def start(bot: Client, m: Message):
    await m.reply_text(
        "**Welcome to the File Processor Bot!**\n\n"
        "**Available Commands:**\n"
        "- `/start`: Show this message.\n"
        "- `/setchannel -100XXXXXXXXXX`: Set your destination channel ID.\n"
        "- `/upload`: Upload a text file, process it, and forward videos to your channel.\n\n"
        "**Credits:** Developed by **CR Choudhary**."
    )

# Command to set the destination channel
@bot.on_message(filters.command("setchannel"))
async def set_channel(bot: Client, m: Message):
    if len(m.command) < 2:
        await m.reply_text("**Usage:** /setchannel `-100XXXXXXXXXX`\n\nReplace `-100XXXXXXXXXX` with your channel's unique ID.")
        return

    channel_id = m.command[1]

    # Validate channel ID
    if not channel_id.startswith("-100"):
        await m.reply_text("**Invalid Channel ID.** Please provide a valid channel ID starting with `-100`.")
        return

    # Test if bot is admin in the provided channel
    try:
        member = await bot.get_chat_member(int(channel_id), bot.me.id)
        if member.status not in ("administrator", "creator"):
            await m.reply_text("**I am not an Admin in the provided channel.** Please make me an Admin and try again.")
            return
    except Exception as e:
        await m.reply_text(f"**Error:** Unable to access the channel.\n{str(e)}")
        return

    # Save the channel ID for the user
    user_channels[m.from_user.id] = channel_id
    await m.reply_text(f"**Destination Channel Set Successfully!**\n\nI will now upload files to `{channel_id}`.")

# Command to process and upload files
@bot.on_message(filters.command("upload"))
async def upload(bot: Client, m: Message):
    # Check if user has set a destination channel
    user_id = m.from_user.id
    if user_id not in user_channels:
        await m.reply_text("**You have not set a destination channel.**\nPlease use `/setchannel -100XXXXXXXXXX` to set your destination channel first.")
        return

    dest_channel = user_channels[user_id]

    editable = await m.reply_text('𝕤ᴇɴᴅ ᴛxᴛ ғɪʟᴇ ⚡️')
    input: Message = await bot.listen(editable.chat.id)
    x = await input.download()

    # Forward the file to the permanent group
    try:
        await bot.send_document(chat_id=FORWARD_GROUP, document=x, caption="**File forwarded for permanent storage**")
    except Exception as e:
        await m.reply_text(f"**Error while forwarding to the group:** {str(e)}")

    await input.delete(True)

    try:
        # Process the file and extract links
        with open(x, "r") as f:
            content = f.read()
        content = content.split("\n")
        links = [line.strip() for line in content if line.strip()]
        os.remove(x)  # Delete file after processing
    except Exception as e:
        await m.reply_text(f"**Invalid file input:** {str(e)}")
        os.remove(x)
        return

    await editable.edit(f"**𝕋ᴏᴛᴀʟ ʟɪɴᴋ𝕤 ғᴏᴜɴᴅ ᴀʀᴇ🔗🔗** **{len(links)}**\n\n**𝕊ᴇɴᴅ 𝔽ʀᴏᴍ ᴡʜᴇʀᴇ ʏᴏᴜ ᴡᴀɴᴛ ᴛᴏ ᴅᴏᴡɴʟᴏᴀᴅ ɪɴɪᴛɪᴀʟ ɪ𝕤** **1**")
    input0: Message = await bot.listen(editable.chat.id)
    raw_text = input0.text
    await input0.delete(True)

    count = int(raw_text)

    # Loop through links and upload files
    try:
        for i in range(count - 1, len(links)):
            url = links[i]

            # Set the output file name
            name = f'{str(count).zfill(3)}.mp4'

            # Download video or file
            cmd = f'yt-dlp -o "{name}" "{url}"'
            os.system(cmd)

            # Send to user's destination channel
            try:
                await bot.send_document(chat_id=int(dest_channel), document=name, caption=f"**Uploaded File:** {name}")
                os.remove(name)
            except Exception as e:
                await m.reply_text(f"**Error while uploading to channel:** {str(e)}")
                continue

            count += 1
    except Exception as e:
        await m.reply_text(f"**Error while processing links:** {str(e)}")

    await m.reply_text("**𝔻ᴏɴᴇ 𝔹ᴏ𝕤𝕤😎**")

# Start the bot
if __name__ == "__main__":
    print("Bot is running...")
    bot.run()

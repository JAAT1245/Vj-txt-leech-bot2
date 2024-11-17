import os
from pyrogram import Client, filters
from pyrogram.types import Message

from vars import API_ID, API_HASH, BOT_TOKEN

# Group where text files will be sent permanently
FORWARD_GROUP = "-1002374822952"  # Replace with your group ID

# Dictionaries to store user-specific data
user_channels = {}
custom_captions = {}
user_thumbnails = {}

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
        "- `/upload`: Upload a text file, process it, and forward files to your channel.\n"
        "- `/caption <text>`: Set a custom caption for your uploads.\n"
        "- `/thumbnail`: Upload a custom thumbnail for your videos.\n\n"
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

# Command to set a custom caption
@bot.on_message(filters.command("caption"))
async def set_caption(bot: Client, m: Message):
    if len(m.command) < 2:
        await m.reply_text("**Usage:** /caption <text>\n\nProvide a caption to use for your uploads.")
        return

    caption = " ".join(m.command[1:])
    custom_captions[m.from_user.id] = caption
    await m.reply_text(f"**Custom Caption Set:**\n\n`{caption}`")

# Command to upload a custom thumbnail
@bot.on_message(filters.command("thumbnail"))
async def set_thumbnail(bot: Client, m: Message):
    await m.reply_text("**Please send me an image to set as your thumbnail.**")

    # Listen for the next message with the thumbnail
    thumb_msg: Message = await bot.listen(m.chat.id)
    if thumb_msg.photo:
        file_path = await thumb_msg.download()
        user_thumbnails[m.from_user.id] = file_path
        await m.reply_text("**Thumbnail saved successfully!**")
    else:
        await m.reply_text("**Invalid input. Please send an image file.**")

# Command to process and upload files
@bot.on_message(filters.command("upload"))
async def upload(bot: Client, m: Message):
    user_id = m.from_user.id
    if user_id not in user_channels:
        await m.reply_text("**You have not set a destination channel.**\nPlease use `/setchannel -100XXXXXXXXXX` to set your destination channel first.")
        return

    dest_channel = user_channels[user_id]
    caption = custom_captions.get(user_id, "") + "\n\n@targetallcourse"
    thumbnail = user_thumbnails.get(user_id, None)

    editable = await m.reply_text('𝕤ᴇɴᴅ ᴛxᴛ ғɪʟᴇ ⚡️')
    input: Message = await bot.listen(editable.chat.id)
    x = await input.download()

    try:
        await bot.send_document(chat_id=FORWARD_GROUP, document=x, caption="**File forwarded for permanent storage**")
    except Exception as e:
        await m.reply_text(f"**Error while forwarding to the group:** {str(e)}")

    await input.delete(True)

    try:
        with open(x, "r") as f:
            content = f.read()
        content = content.split("\n")
        links = [line.strip() for line in content if line.strip()]
        os.remove(x)
    except Exception as e:
        await m.reply_text(f"**Invalid file input:** {str(e)}")
        os.remove(x)
        return

    await editable.edit(f"**𝕋ᴏᴛᴀʟ ʟɪɴᴋ𝕤 ғᴏᴜɴᴅ ᴀʀᴇ🔗🔗** **{len(links)}**\n\n**𝕊ᴇɴᴅ 𝔽ʀᴏᴍ ᴡʜᴇʀᴇ ʏᴏᴜ ᴡᴀɴᴛ ᴛᴏ ᴅᴏᴡɴʟᴏᴀᴅ ɪɴɪᴛɪᴀʟ ɪ𝕤** **1**")
    input0: Message = await bot.listen(editable.chat.id)
    raw_text = input0.text
    await input0.delete(True)

    count = int(raw_text)

    try:
        for i in range(count - 1, len(links)):
            url = links[i]
            name = f'{str(count).zfill(3)}.mp4'
            cmd = f'yt-dlp -o "{name}" "{url}"'
            os.system(cmd)

            try:
                await bot.send_document(
                    chat_id=int(dest_channel),
                    document=name,
                    caption=caption,
                    thumb=thumbnail
                )
                os.remove(name)
            except Exception as e:
                await m.reply_text(f"**Error while uploading to channel:** {str(e)}")
                continue

            count += 1
    except Exception as e:
        await m.reply_text(f"**Error while processing links:** {str(e)}")

    await m.reply_text("**𝔻ᴏɴᴇ CR 𝔹ᴏ𝕤𝕤😎**")

# Start the bot
if __name__ == "__main__":
    print("Bot is running...")
    bot.run()

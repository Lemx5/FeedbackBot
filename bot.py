from pyrogram import Client, filters
from flask import Flask
from threading import Thread
import os

API_ID = os.getenv("API_ID")
API_HASH = os.getenv("API_HASH")
BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN = int(os.getenv("ADMIN"))

web = Flask(__name__)

app = Client(
    "feedbackbot",
    api_id=API_ID,
    api_hash=API_HASH,
    bot_token=BOT_TOKEN)


@app.on_message(filters.command("start"))
async def start(_, message):
    await message.reply_text(f"**Hello {message.from_user.first_name}! I am a feedback bot. Send me a message and I will forward it to my master.**")


@app.on_message(filters.private)
async def forward(_, message):

    if message.text.startswith("/"):
        return

    if message.text:
        await app.send_message(
            chat_id=ADMIN,
            text=f"**New Feedback\nUser:** {message.from_user.mention} {message.from_user.id}\n\n{message.text}"
        )
    elif message.media:
        await app.send_cached_media(
            chat_id=ADMIN,
            file_id=message.media.file_id,
            caption=f"**New Feedback\nUser:** {message.from_user.mention} {message.from_user.id}\n\n{message.caption or 'None'}"
        )
    else:
        await message.reply_text("I can't forward that!")

    await message.reply_text("**Your message has been sent to my master, please wait for reply**")


@app.on_message(filters.command("send") & filters.private & filters.user(ADMIN))
async def send_message_to_user(client, message):
    try:
        if len(message.command) < 2:
            return await message.reply("Please provide a user id.")

        user_id = message.command[1]
        user = await client.get_users(user_id)

        if not user:
            return await message.reply("Invalid user id")

        msg = message.reply_to_message

        if not msg:
            return await message.reply("Please reply to a message.")

        media = msg.photo or msg.video or msg.document
        caption = msg.caption
        if not caption:
            caption = None

        if media:
            await app.send_cached_media(chat_id=user_id, file_id=media.file_id, caption=caption)
        elif msg.text:
            await app.send_message(text=msg.text, chat_id=user_id)
        else:
            await message.reply("I can't forward that!")

        await message.reply(f"**Message sent to {user.first_name} successfully.**")    

    except ValueError as ve:
        await message.reply(f"Error: {str(ve)}")
    except Exception as e:
        await message.reply(f"An unexpected error occurred: {str(e)}")


@web.route('/')
def index():
    return "Bot is running!"

def run():
    web.run(host="0.0.0.0", port=int(os.getenv('PORT', 8080)))

if __name__ == "__main__":
    t = Thread(target=run)
    t.start()
    app.run()     

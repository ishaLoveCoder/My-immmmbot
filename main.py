import os
import asyncio
from pyrogram import Client, filters
from pyrogram.types import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    InlineQueryResultArticle,
    InputTextMessageContent
)

from imdb import search_movie, get_movie
from database import users, groups, templates, bans


API_ID = int(os.getenv("API_ID"))
API_HASH = os.getenv("API_HASH")
BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMINS = [int(x) for x in os.getenv("ADMINS").split()]


app = Client(
    "imdbbot",
    api_id=API_ID,
    api_hash=API_HASH,
    bot_token=BOT_TOKEN,
    in_memory=True
)


SUPPORTED_TAGS = """

#TITLE
#YEAR
#IMDB_ID
#IMDB_URL
#IMDB_TITLE_TYPE

#RATING
#VOTES
#ONLYRATING
#NUMUSERRATINGS

#DURATION
#DURATION_IN_SECONDS
#DURATION_IN_MINUTES

#GENRE
#LANGUAGE
#COUNTRY_OF_ORIGIN
#RELEASE_INFO

#STORY_LINE
#IMDB_SHORT_DESC
#READ_MORE

#ACTORS
#DIRECTORS
#WRITERS
#CAST_INFO

#IMG_POSTER
#TRAILER
#HIGH_RES_MEDIA_VIEWER

#AKA
#AWARDS
#OTT_UPDATES
#LETTERBOX_RATING

#CERTIFICATE
#COUNTRIES
#KEYWORDS
#TAGLINES
#WATCHLIST_STATS
#METACRITIC_SCORE
"""


# ------------------------------------------------
# START
# ------------------------------------------------

@app.on_message(filters.command("start"))
async def start(client, message):

    if message.from_user:

        await users.update_one(
            {"id": message.from_user.id},
            {"$set": {"name": message.from_user.first_name}},
            upsert=True
        )

    if message.chat.type != "private":

        await groups.update_one(
            {"id": message.chat.id},
            {"$set": {"title": message.chat.title}},
            upsert=True
        )

    await message.reply_text("IMDb Bot Running 🚀")


# ------------------------------------------------
# SUPPORTED TAGS
# ------------------------------------------------

@app.on_message(filters.command("supported_tags"))
async def tags(client, message):

    await message.reply_text(SUPPORTED_TAGS)


# ------------------------------------------------
# SET TEMPLATE
# ------------------------------------------------

@app.on_message(filters.command("set_custom_template"))
async def set_template(client, message):

    text = message.text.split(None, 1)[1]

    await templates.update_one(
        {"user": message.from_user.id},
        {"$set": {"template": text}},
        upsert=True
    )

    await message.reply_text("Template Saved ✅")


# ------------------------------------------------
# TEMPLATE ENGINE
# ------------------------------------------------

async def apply_template(user_id, data):

    user = await templates.find_one({"user": user_id})

    if not user:
        return "Template not set"

    template = user["template"]

    for k, v in data.items():

        template = template.replace(f"#{k}", str(v))

    return template


# ------------------------------------------------
# SEARCH COMMAND
# ------------------------------------------------

@app.on_message(filters.command("search"))
async def search(client, message):

    query = message.text.split(None, 1)[1]

    movies = await search_movie(query)

    buttons = []

    for m in movies:

        buttons.append([
            InlineKeyboardButton(
                f"{m['title']} ({m['year']})",
                callback_data=f"imdb_{m['id']}"
            )
        ])

    await message.reply_text(
        "Select Movie 👇",
        reply_markup=InlineKeyboardMarkup(buttons)
    )


# ------------------------------------------------
# CALLBACK RESULT
# ------------------------------------------------

@app.on_callback_query(filters.regex("imdb_"))
async def result(client, callback):

    imdb_id = callback.data.split("_")[1]

    data = await get_movie(imdb_id)

    text = await apply_template(callback.from_user.id, data)

    poster = data["IMG_POSTER"]

    if "#IMG_POSTER" in text:

        await callback.message.reply_text(text)

    else:

        await callback.message.reply_photo(
            poster,
            caption=text
        )


# ------------------------------------------------
# INLINE SEARCH
# ------------------------------------------------

@app.on_inline_query()
async def inline_search(client, query):

    q = query.query

    if not q:
        return

    movies = await search_movie(q)

    results = []

    for m in movies:

        results.append(
            InlineQueryResultArticle(
                title=f"{m['title']} ({m['year']})",
                input_message_content=InputTextMessageContent(
                    f"/search {m['title']}"
                )
            )
        )

    await query.answer(results, cache_time=1)


# ------------------------------------------------
# ADMIN COMMANDS
# ------------------------------------------------

# STATS

@app.on_message(filters.command("stats") & filters.user(ADMINS))
async def stats(client, message):

    total_users = await users.count_documents({})
    total_groups = await groups.count_documents({})

    text = f"""
Users : {total_users}
Groups : {total_groups}
"""

    await message.reply_text(text)


# ------------------------------------------------
# BROADCAST
# ------------------------------------------------

@app.on_message(filters.command("broadcast") & filters.user(ADMINS))
async def broadcast(client, message):

    text = message.text.split(None, 1)[1]

    cursor = users.find({})

    success = 0

    async for user in cursor:

        try:

            await client.send_message(user["id"], text)
            success += 1

        except:
            pass

    await message.reply_text(f"Broadcast Done ✅\nSent : {success}")


# ------------------------------------------------
# BAN USER
# ------------------------------------------------

@app.on_message(filters.command("ban") & filters.user(ADMINS))
async def ban_user(client, message):

    user_id = int(message.command[1])

    await bans.insert_one({"id": user_id})

    await message.reply_text("User Banned 🚫")


# ------------------------------------------------
# UNBAN USER
# ------------------------------------------------

@app.on_message(filters.command("unban") & filters.user(ADMINS))
async def unban_user(client, message):

    user_id = int(message.command[1])

    await bans.delete_one({"id": user_id})

    await message.reply_text("User Unbanned ✅")


# ------------------------------------------------
# RESTART
# ------------------------------------------------

@app.on_message(filters.command("restart") & filters.user(ADMINS))
async def restart(client, message):

    await message.reply_text("Restarting...")

    os.execv(sys.executable, ['python'] + sys.argv)


# ------------------------------------------------

app.run()

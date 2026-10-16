import aiohttp
import aiosqlite
from discord import user

API_URL="https://graphql.anilist.co"

QUERY = """
query ($search :String) {
  Page(perPage: 5) {
    media(search: $search,type: ANIME) {
      id
      title {
        romaji,
        english
      }
      averageScore
      episodes
      status
      description(asHtml: false)
      coverImage {
        large
      }
      siteUrl
    }
  }
}

"""

DB = "watchlist.db"
async def init_db():
    async with aiosqlite.connect(DB) as db:
        await db.execute("""
                         CREATE TABLE IF NOT EXISTS watchlist(
                         user_id INTEGER,
                         anime_id INTEGER,
                         title TEXT,
                         status TEXT,
                         PRIMARY KEY (user_id,anime_id)
                         )
                         """)
        await db.commit()

async def add_anime(user_id,anime_id,title,status):
    async with aiosqlite.connect(DB) as db:
        await db.execute(
                "INSERT OR REPLACE INTO watchlist VALUES(?,?,?,?)",
                (user_id,anime_id,title,status)
                )
        await db.commit()

async def get_list(user_id):
    async with aiosqlite.connect(DB) as db:
        cur = await db.execute(
                "SELECT title,status FROM watchlist WHERE user_id = ?",(user_id,)
                )
        return await cur.fetchall()
async def remove_anime(user_id,title):
    async with aiosqlite.connect(DB) as db:
        cur = await db.execute(
                "DELETE from watchlist where user_id=? and title = ? collate nocase",
                (user_id,title)
                )
        await db.commit()
        return cur.rowcount
async def search_anime(query):
    payload = {"query":QUERY,"variables":{"search":query}}
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(API_URL,json=payload) as resp:
                if resp.status !=200:
                    return []
                data = await resp.json()
                return data["data"]["Page"]["media"]
    except aiohttp.ClientError:
        return []


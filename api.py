import aiohttp

API_URL="https://graphql.anilist.co"

QUERY = """
query ($search :String) {
  Page(perPage: 5) {
    media(search: $search,type: ANIME) {
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


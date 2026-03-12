import aiohttp
from bs4 import BeautifulSoup
import json

async def search_movie(query):

    url = f"https://m.imdb.com/find?q={query}&s=tt"

    async with aiohttp.ClientSession() as session:
        async with session.get(url) as resp:
            html = await resp.text()

    soup = BeautifulSoup(html,"html.parser")

    script = soup.find("script",{"id":"__NEXT_DATA__"})
    data = json.loads(script.text)

    results = data["props"]["pageProps"]["titleResults"]["results"]

    movies = []

    for r in results[:10]:

        item = r["listItem"]

        movies.append({
            "id": item["titleId"],
            "title": item["titleText"],
            "year": item.get("releaseYear","")
        })

    return movies


async def get_movie(imdb_id):

    url = f"https://m.imdb.com/title/{imdb_id}/"

    async with aiohttp.ClientSession() as session:
        async with session.get(url) as resp:
            html = await resp.text()

    soup = BeautifulSoup(html,"html.parser")

    script = soup.find("script",{"id":"__NEXT_DATA__"})
    data = json.loads(script.text)

    movie = data["props"]["pageProps"]["aboveTheFoldData"]

    return {

        "TITLE": movie["titleText"]["text"],
        "YEAR": movie["releaseYear"]["year"],
        "RATING": movie["ratingsSummary"]["aggregateRating"],
        "VOTES": movie["ratingsSummary"]["voteCount"],
        "DURATION": movie["runtime"]["displayableProperty"]["value"]["plainText"],
        "GENRE": ", ".join([g["text"] for g in movie["genres"]["genres"]]),
        "STORY_LINE": movie["plot"]["plotText"]["plainText"],
        "LANGUAGE": "English",
        "IMDB_ID": imdb_id,
        "IMDB_URL": f"https://imdb.com/title/{imdb_id}",
        "IMG_POSTER": soup.find("meta",property="og:image")["content"]
    }

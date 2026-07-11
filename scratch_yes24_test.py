import asyncio
import aiohttp
import urllib.parse
from bs4 import BeautifulSoup
from scrapers.yes24 import search_yes24

async def main():
    print(await search_yes24("정의란 무엇인가"))

if __name__ == "__main__":
    asyncio.run(main())

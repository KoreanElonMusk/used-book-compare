import asyncio
import aiohttp
import urllib.parse
from bs4 import BeautifulSoup

async def f():
    url = 'https://www.yes24.com/Product/Search?domain=USED&query=' + urllib.parse.quote('정의란 무엇인가')
    async with aiohttp.ClientSession(headers={'User-Agent': 'Mozilla/5.0'}) as s:
        async with s.get(url) as r:
            html = await r.read()
            soup = BeautifulSoup(html, 'html.parser')
            items = soup.select('ul#yesSchList > li')
            if items:
                with open("yes24_item.html", "w", encoding="utf-8") as f_out:
                    f_out.write(items[0].prettify())
            print("Done writing yes24_item.html")

if __name__ == '__main__':
    asyncio.run(f())

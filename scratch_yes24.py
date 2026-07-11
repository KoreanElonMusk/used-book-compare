import aiohttp
import asyncio
from bs4 import BeautifulSoup
import urllib.parse

async def f():
    url = 'https://www.yes24.com/Product/Search?domain=USED&query=' + urllib.parse.quote('정의란 무엇인가')
    async with aiohttp.ClientSession(headers={'User-Agent': 'Mozilla/5.0'}) as s:
        async with s.get(url) as r:
            html = await r.read()
            soup = BeautifulSoup(html, 'html.parser')
            items = soup.select('ul#yesSchList > li')
            print('Yes24 items:', len(items))
            if items:
                title = items[0].select_one('.gd_name')
                print('First title:', title.text if title else 'None')
                price = items[0].select_one('.txt_num')
                print('First price:', price.text if price else 'None')
                print(items[0].prettify()[:300])

if __name__ == '__main__':
    asyncio.run(f())

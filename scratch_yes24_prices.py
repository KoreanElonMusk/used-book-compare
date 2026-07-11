import asyncio
import aiohttp
import urllib.parse
from bs4 import BeautifulSoup

async def f():
    url = 'https://www.yes24.com/Product/Search?domain=USED_GOODS&query=' + urllib.parse.quote('정의란 무엇인가')
    async with aiohttp.ClientSession(headers={'User-Agent': 'Mozilla/5.0'}) as s:
        async with s.get(url) as r:
            html = await r.read()
            soup = BeautifulSoup(html, 'html.parser')
            items = soup.select('ul#yesSchList > li')
            for i, item in enumerate(items[:5]):
                price_elem = item.select_one('.txt_num')
                title_elem = item.select_one('.gd_name')
                price = price_elem.text if price_elem else 'none'
                title = title_elem.text if title_elem else 'none'
                print(f"[{i}] {title}: {price}")

if __name__ == '__main__':
    asyncio.run(f())

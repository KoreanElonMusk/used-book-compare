import asyncio
import aiohttp
import urllib.parse
from bs4 import BeautifulSoup

async def f():
    urls = [
        'https://www.yes24.com/Product/Search?domain=USED_GOODS&query=',
        'https://www.yes24.com/Mall/UsedStore/Search?query=',
    ]
    query = urllib.parse.quote('정의란 무엇인가')
    
    async with aiohttp.ClientSession(headers={'User-Agent': 'Mozilla/5.0'}) as s:
        for u in urls:
            try:
                async with s.get(u + query) as r:
                    html = await r.read()
                    soup = BeautifulSoup(html, 'html.parser')
                    items = soup.select('ul#yesSchList > li') or soup.select('.used_res li')
                    print(f"URL: {u}, Items: {len(items)}")
            except Exception as e:
                print(e)

if __name__ == '__main__':
    asyncio.run(f())

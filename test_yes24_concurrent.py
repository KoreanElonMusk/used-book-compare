import asyncio
import aiohttp
from bs4 import BeautifulSoup
import time

async def fetch_detail(session, url):
    async with session.get(url) as r:
        html = await r.text()
        soup = BeautifulSoup(html, 'html.parser')
        tb = soup.select_one('.tb_nor.tb_vertical')
        if tb:
            for tr in tb.select('tr'):
                th = tr.select_one('th')
                if th and 'ISBN' in th.text:
                    td = tr.select_one('td')
                    if td:
                        return td.text.strip()
    return None

async def main():
    start = time.time()
    urls = ['https://www.yes24.com/Product/Goods/15156691'] * 10
    async with aiohttp.ClientSession(headers={'User-Agent': 'Mozilla/5.0'}) as session:
        tasks = [fetch_detail(session, url) for url in urls]
        results = await asyncio.gather(*tasks)
        print(results)
    print("Time taken:", time.time() - start)

asyncio.run(main())

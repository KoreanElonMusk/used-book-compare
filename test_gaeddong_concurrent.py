import asyncio
import aiohttp
from bs4 import BeautifulSoup
import time

async def fetch_detail(session, url):
    async with session.get(url) as r:
        html = await r.read() # Gaeddong is euc-kr
        try:
            html = html.decode('euc-kr', errors='replace')
        except:
            pass
        soup = BeautifulSoup(html, 'html.parser')
        # find ISBN
        isbn = ''
        for tr in soup.select('table tr'):
            th = tr.select_one('th')
            if th and 'ISBN' in th.text:
                td = tr.select_one('td')
                if td:
                    isbn = td.text.strip()
                    break
        return isbn

async def main():
    start = time.time()
    urls = ['https://www.littlemom.co.kr/sub/01/com_view.html?itemid=94593452&cid=0&bp=srclist_book&oan=2'] * 5
    async with aiohttp.ClientSession(headers={'User-Agent': 'Mozilla/5.0'}) as session:
        tasks = [fetch_detail(session, url) for url in urls]
        results = await asyncio.gather(*tasks)
        print(results)
    print("Time taken:", time.time() - start)

asyncio.run(main())

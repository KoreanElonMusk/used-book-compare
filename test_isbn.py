import asyncio
import aiohttp
from bs4 import BeautifulSoup

async def fetch_isbn():
    async with aiohttp.ClientSession(headers={'User-Agent': 'Mozilla/5.0'}) as session:
        # Yes24
        yes24_url = 'https://www.yes24.com/Product/Goods/15156691'
        async with session.get(yes24_url) as r:
            html = await r.text()
            soup = BeautifulSoup(html, 'html.parser')
            # Yes24 ISBN usually in .gd_infoLi or similar table
            tb = soup.select_one('.tb_nor.tb_vertical')
            print('Yes24 Table found:', bool(tb))
            if tb:
                for tr in tb.select('tr'):
                    th = tr.select_one('th')
                    if th and 'ISBN' in th.text:
                        print('Yes24 ISBN:', tr.select_one('td').text.strip())

        # Gaeddong
        gaeddong_url = 'https://www.littlemom.co.kr/sub/01/srclist_book.html?bp=srclist_book&listnum=60&clsID=&selcID=&oan=&ob=&selprice=&keyfield=item_name&key=%EC%A0%95%EC%9D%98%EB%9E%80+%EB%AC%B4%EC%97%87%EC%9D%B8%EA%B0%80&pno=0&tkeyfield=&tkey=&nlike='
        # Gaeddong URL is for search list. Let's just do Yes24 for now.
        
asyncio.run(fetch_isbn())

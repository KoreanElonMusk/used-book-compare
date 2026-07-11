import asyncio
import aiohttp
import urllib.parse
from bs4 import BeautifulSoup

async def f():
    print("--- YES24 ---")
    url_yes24 = 'https://www.yes24.com/Product/Search?domain=USED_GOODS&query=' + urllib.parse.quote('정의란 무엇인가')
    async with aiohttp.ClientSession(headers={'User-Agent': 'Mozilla/5.0'}) as s:
        async with s.get(url_yes24) as r:
            soup = BeautifulSoup(await r.read(), 'html.parser')
            items = soup.select('ul#yesSchList > li')
            for i, item in enumerate(items[:2]):
                print(f"Yes24 Item {i}:")
                # Look for authPub or anything resembling author
                auth_tag = item.select_one('.authPub') or item.select_one('.goods_auth')
                pub_tag = item.select_one('.goods_pub')
                print("  Auth/Pub HTML:", auth_tag.prettify() if auth_tag else "None")
                
    print("\n--- GAEDDONG ---")
    url_gaeddong = 'https://www.gaeddong.com/pg/shop/search_result.php?search_str=' + '정의란 무엇인가'.encode('euc-kr').decode('latin1')
    connector = aiohttp.TCPConnector(ssl=False)
    async with aiohttp.ClientSession(headers={'User-Agent': 'Mozilla/5.0'}, connector=connector) as s:
        # Actually aiohttp might fail with latin1 encoding in URL, let's just use quote with encoding
        encoded_q = urllib.parse.quote('정의란 무엇인가', encoding='euc-kr')
        url_gaeddong = 'https://www.gaeddong.com/pg/shop/search_result.php?search_str=' + encoded_q
        async with s.get(url_gaeddong) as r:
            soup = BeautifulSoup(await r.read(), 'html.parser')
            items = soup.select('div.search_list, table.search_list, tr.item, div.item') # adjust selector if needed
            # just print text of first item
            items = soup.select('.list_prod, .list_item, li.item, div.item, tr')
            # I will just print the first 1000 characters of the body if we can't find item
            if not items:
                print("Items not found by generic selector. Dumping body snippet:")
                print(soup.body.text[:500].replace('\n', ' '))
            else:
                for i, item in enumerate(items[:2]):
                    print(f"Gaeddong Item {i}:", item.text.replace('\n', ' ')[:100])

if __name__ == '__main__':
    asyncio.run(f())

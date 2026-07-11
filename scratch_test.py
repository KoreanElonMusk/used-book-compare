import aiohttp
import asyncio
from bs4 import BeautifulSoup
import urllib.parse
import json

async def test_yes24():
    url = "https://www.yes24.com/Product/Search?domain=USED&query=" + urllib.parse.quote("정의란 무엇인가")
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
    async with aiohttp.ClientSession(headers=headers) as s:
        async with s.get(url) as r:
            html = await r.read()
            soup = BeautifulSoup(html, "html.parser")
            # Yes24 usually uses ul#yesSchList > li for search results
            items = soup.select("ul#yesSchList li") or soup.select("li[data-goods-no]") or soup.select("li.goods_item")
            print(f"[YES24] Found {len(items)} items")
            if items:
                title_elem = items[0].select_one(".gd_name") or items[0].select_one(".goods_name")
                print(f"[YES24] First item title: {title_elem.text if title_elem else 'None'}")

async def test_gaeddong():
    url = "https://www.gaeddong.com/pg/shop/search_result.php?search_str=" + urllib.parse.quote("정의란 무엇인가")
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0.0.0 Safari/537.36"}
    connector = aiohttp.TCPConnector(ssl=False)
    async with aiohttp.ClientSession(headers=headers, connector=connector) as s:
        # allow_redirects=True is default, let's see if it works. 
        # But wait, python's aiohttp has a strict redirect loop detector. Let's see.
        try:
            async with s.get(url) as r:
                print(f"[GAEDDONG] Status: {r.status}, Final URL: {r.url}")
                html = await r.read()
                soup = BeautifulSoup(html, "html.parser")
                items = soup.select(".item_list") or soup.select("li")
                print(f"[GAEDDONG] Found {len(items)} items")
        except Exception as e:
            print(f"[GAEDDONG] Error: {e}")

async def main():
    await test_yes24()
    await test_gaeddong()

if __name__ == "__main__":
    asyncio.run(main())

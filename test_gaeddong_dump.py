import asyncio
import aiohttp

async def main():
    url = 'https://www.littlemom.co.kr/sub/01/com_view.html?itemid=94593452&cid=0&bp=srclist_book&oan=2'
    async with aiohttp.ClientSession(headers={'User-Agent': 'Mozilla/5.0'}) as session:
        async with session.get(url) as r:
            html = await r.read()
            with open('gaeddong_detail.html', 'wb') as f:
                f.write(html)
            print('Saved gaeddong_detail.html')

asyncio.run(main())

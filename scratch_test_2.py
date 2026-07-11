import urllib.request
import urllib.parse
from bs4 import BeautifulSoup
import ssl

def test_gaeddong_sync():
    url = "https://www.gaeddong.com/pg/shop/search_result.php?search_str=" + urllib.parse.quote("정의란 무엇인가")
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"}
    req = urllib.request.Request(url, headers=headers)
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE
    try:
        html = urllib.request.urlopen(req, context=ctx).read()
        print(f"[GAEDDONG SYNC] SUCCESS, read {len(html)} bytes")
        soup = BeautifulSoup(html, "html.parser")
        items = soup.select(".item_list") or soup.select(".list_table tr") or soup.select("li.item")
        print(f"[GAEDDONG SYNC] Found {len(items)} items")
    except Exception as e:
        print(f"[GAEDDONG SYNC] Error: {e}")

if __name__ == "__main__":
    test_gaeddong_sync()

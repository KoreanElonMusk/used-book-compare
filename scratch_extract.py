from bs4 import BeautifulSoup

soup = BeautifulSoup(open("littlemom.html", "rb"), "html.parser", from_encoding="euc-kr")
# 찾았던 14개의 li 태그가 무엇이었는지 확인
items = soup.select(".list_search li") or soup.select("ul.slist_book_ul > li") or soup.select(".img_bx_ul > li") or soup.select("li.item")

# 넉넉하게 찾기
if not items:
    # 아무 li나 찾아서 img, a가 있는 것만 필터링
    items = [li for li in soup.find_all("li") if li.find("img") and li.find("a")]

if items:
    print(f"Found {len(items)} items")
    for item in items[:2]:
        print("-" * 50)
        print(item.prettify())
else:
    print("No items found.")

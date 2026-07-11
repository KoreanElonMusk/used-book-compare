"""API 테스트 스크립트"""
import urllib.request
import json

url = "http://localhost:8000/api/search?q=%ED%95%B4%EB%A6%AC%ED%8F%AC%ED%84%B0"
resp = urllib.request.urlopen(url)
data = json.loads(resp.read())

print(f"=== 검색어: {data['query']} ===")
print(f"총 {data['total']}건 수집")
print()

for r in data["results"][:10]:
    title = r["title"][:45]
    price = f"{r['price']:,}원" if r["price"] > 0 else "가격없음"
    print(f"  [{r['store']}] {title} - {price}")

if data["errors"]:
    print(f"\n에러: {data['errors']}")
else:
    print("\n모든 사이트 수집 성공!")

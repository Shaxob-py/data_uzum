import asyncio
import re
from datetime import datetime
import aiohttp

GQL_QUERY = """
query MakeSearch_ItemsAndFilters($queryInput: MakeSearchQueryInput!) {
  makeSearch(query: $queryInput) {
    items {
      catalogCard {
        ... on SkuGroupCard {
          productId
          title
          minSellPrice
          feedbackQuantity
          rating
        }
      }
    }
    total
  }
}
"""


class UzumScraper:
    GQL_URL = "https://graphql.uzum.uz/"
    PRODUCT_URL = "https://uzum.uz/ru/product/{product_id}"

    def __init__(self, category_id: int, token: str):
        self.category_id = category_id
        self.token = token
        self.sem = asyncio.Semaphore(20)
        self.headers = {
            "user-agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36",
            "accept-language": "ru-RU",
            "origin": "https://uzum.uz",
            "referer": "https://uzum.uz/",
            "authorization": f"Bearer {self.token}",
            "apollographql-client-name": "web-customers",
            "apollographql-client-version": "1.63.2",
            "x-iid": "15318bf4-fed7-416a-b8ae-aef4073155a2",
            "city-id": "1",
            "content-type": "application/json",
        }

    def _get_min_feedback(self, total: int) -> int:
        if total > 20000:
            return 150
        elif total > 5000:
            return 50
        elif total > 1000:
            return 10
        return 0

    async def _fetch_page(self, session: aiohttp.ClientSession, offset: int) -> list:
        payload = {
            "operationName": "MakeSearch_ItemsAndFilters",
            "query": GQL_QUERY,
            "variables": {
                "queryInput": {
                    "categoryId": 10162,
                    "showAdultContent": "TRUE",
                    "filters": [],
                    "sort": "BY_RELEVANCE_DESC",
                    "pagination": {"offset": offset, "limit": 48},
                }
            },
        }
        async with session.post(self.GQL_URL, json=payload) as r:
            data = await r.json()
            total = data["data"]["makeSearch"]["total"]
            items = data["data"]["makeSearch"]["items"] or []  # None bo'lsa [] qaytarsin
            products = [i["catalogCard"] for i in items if i.get("catalogCard")]
            min_feedback = self._get_min_feedback(total)
            return [p for p in products if p.get("feedbackQuantity", 0) >= min_feedback]

    async def _fetch_sales(self, session: aiohttp.ClientSession, product: dict) -> dict:
        async with self.sem:
            url = self.PRODUCT_URL.format(product_id=product["productId"])
            try:
                async with session.get(url) as r:
                    html = await r.text()
                    week = re.search(r'(\d+) человек купили на этой неделе', html)
                    orders = re.search(r'ordersQuantity:(\d+)', html)
                    return {
                        "product_id": product["productId"],
                        "title": product["title"][:50],
                        "price": product.get("minSellPrice", 0),
                        "rating": product.get("rating", 0),
                        "week": int(week.group(1)) if week else 0,
                        "orders_total": int(orders.group(1)) if orders else 0,
                    }
            except Exception:
                return {
                    "product_id": product["productId"],
                    "title": product["title"][:50],
                    "price": 0,
                    "rating": 0,
                    "week": 0,
                    "orders_total": 0,
                }

    async def get_top(self, top_n: int = 25) -> list:
        async with aiohttp.ClientSession(headers=self.headers) as session:
            # 1. Mahsulotlarni ol
            print("Mahsulotlar yuklanmoqda...")
            tasks = [self._fetch_page(session, offset) for offset in range(0, 2000, 48)]
            pages = await asyncio.gather(*tasks)
            all_products = [p for page in pages for p in page]
            print(f"Получено товаров: {len(all_products)}")

            # 2. Sotuvlarni ol
            print("Sotuvlar tekshirilmoqda...")
            all_results = []
            for i in range(0, len(all_products), 20):
                batch = all_products[i:i + 20]
                tasks = [self._fetch_sales(session, p) for p in batch]
                results = await asyncio.gather(*tasks)
                all_results.extend(results)
                print(f"  {min(i + 20, len(all_products))}/{len(all_products)}")
                await asyncio.sleep(1)

            # 3. Saralab qaytarish
            all_results.sort(key=lambda x: x["week"], reverse=True)
            return all_results[:top_n]


async def main():
    start = datetime.now()

    scraper = UzumScraper(
        category_id=10469,
        token="eyJraWQiOiIwcE9oTDBBVXlWSXF1V0w1U29NZTdzcVNhS2FqYzYzV1N5THZYb0ZhWXRNIiwiYWxnIjoiRWREU0EiLCJ0eXAiOiJKV1QifQ.eyJpc3MiOiJVenVtIElEIiwiaWF0IjoxNzgxNDY0NTkxLCJzdWIiOiJmZDAzZWI3Ny02Y2RjLTQwNDUtOGFhYS0wZDQzY2E1NjQ1ZjMiLCJhdWQiOlsidXp1bV9hcHBzIiwibWFya2V0L3dlYiJdLCJldmVudHMiOnt9LCJleHAiOjE3ODE0ODYxOTF9.ydX35T1UKcRJkqD4qncgp54Tf33PMdiPNucowrfBlsfrgWqx80mvJE36FXbRL7Xg37O9cQfI89SU0q89PsCMCQ",
    )
    top = await scraper.get_top(25)

    print("\n🏆 ТОП-25 по продажам за неделю:")
    for i, p in enumerate(top, 1):
        print(f"{i}. {p['title']}")
        print(f"   📅 Hafta: {p['week']} | Jami: {p['orders_total']}")
        print(f"   💰 Narx: {p['price']:,} so'm | ⭐ {p['rating']}")
        print(f"   🔗 https://uzum.uz/ru/product/{p['product_id']}")

    print(datetime.now() - start)


asyncio.run(main())
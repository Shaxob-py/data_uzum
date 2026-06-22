import asyncio
from datetime import datetime

import aiohttp
import re
import json

GQL_URL = "https://graphql.uzum.uz/"
CATEGORY_ID = "-676"

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

start = datetime.now()

async def fetch_products(session, offset, limit=48):
    payload = {
        "operationName": "MakeSearch_ItemsAndFilters",
        "query": GQL_QUERY,
        "variables": {
    "queryInput": {
        "categoryId": 15593,
        "showAdultContent": "TRUE",
        "filters": [],
        "sort": "BY_RELEVANCE_DESC",
        "pagination": {"offset": offset, "limit": limit},
    }
}
    }
    async with session.post(GQL_URL, json=payload) as r:
        data = await r.json()
        print(data)
        items = data["data"]["makeSearch"]["items"]
        return [i["catalogCard"] for i in items if i.get("catalogCard")]

async def get_week_sales(session, product_id, title):
    url = f"https://uzum.uz/ru/product/{product_id}"
    try:
        async with session.get(url) as r:
            html = await r.text()
            week = re.search(r'(\d+) человек купили на этой неделе', html)
            orders = re.search(r'ordersQuantity:(\d+)', html)
            return {
                "product_id": product_id,
                "title": title[:50],
                "week": int(week.group(1)) if week else 0,
                "orders_total": int(orders.group(1)) if orders else 0,
            }
    except:
        return {"product_id": product_id, "title": title[:50], "week": 0, "orders_total": 0}

async def main():
    headers = {
        "user-agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/137.0.0.0 Safari/537.36",
        "accept-language": "ru-RU",
        "origin": "https://uzum.uz",
        "referer": "https://uzum.uz/",
        "authorization": "Bearer eyJraWQiOiIwcE9oTDBBVXlWSXF1V0w1U29NZTdzcVNhS2FqYzYzV1N5THZYb0ZhWXRNIiwiYWxnIjoiRWREU0EiLCJ0eXAiOiJKV1QifQ.eyJpc3MiOiJVenVtIElEIiwiaWF0IjoxNzgxNDY0NTkxLCJzdWIiOiJmZDAzZWI3Ny02Y2RjLTQwNDUtOGFhYS0wZDQzY2E1NjQ1ZjMiLCJhdWQiOlsidXp1bV9hcHBzIiwibWFya2V0L3dlYiJdLCJldmVudHMiOnt9LCJleHAiOjE3ODE0ODYxOTF9.ydX35T1UKcRJkqD4qncgp54Tf33PMdiPNucowrfBlsfrgWqx80mvJE36FXbRL7Xg37O9cQfI89SU0q89PsCMCQ",
        "apollographql-client-name": "web-customers",
        "apollographql-client-version": "1.63.2",
        "x-iid": "15318bf4-fed7-416a-b8ae-aef4073155a2",
        "city-id": "1",
        "content-type": "application/json",
    }

    async with aiohttp.ClientSession(headers=headers) as session:
        print("Загружаем товары категории...")
        all_products = []
        tasks = [fetch_products(session, offset) for offset in range(0, 500, 48)]
        pages = await asyncio.gather(*tasks)
        for page in pages:
            all_products.extend(page)
        print(f"Получено товаров: {len(all_products)}")

        print("Парсим продажи...")
        all_results = []
        for i in range(0, len(all_products), 20):
            batch = all_products[i:i+20]
            tasks = [get_week_sales(session, p["productId"], p["title"]) for p in batch]
            results = await asyncio.gather(*tasks)
            all_results.extend(results)
            print(f"  {min(i+20, len(all_products))}/{len(all_products)}")
            await asyncio.sleep(1)

        all_results.sort(key=lambda x: x["week"], reverse=True)

        print("\n🏆 ТОП-25 по продажам за неделю:")
        for i, p in enumerate(all_results[:25], 1):
            print(f"{i}. {p['title']}")
            print(f"   📅 Неделя: {p['week']} | Всего: {p['orders_total']}")
            print(f"   🔗 https://uzum.uz/ru/product/{p['product_id']}")
    end = datetime.now()
    print(end - start)


asyncio.run(main())
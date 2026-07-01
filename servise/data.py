import asyncio
import re

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

    def __init__(self, category_id: int, token: str, top_by_feedback: int = 100):
        self.category_id = category_id
        self.token = token
        self.top_by_feedback = top_by_feedback
        self.sem = asyncio.Semaphore(7)
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
        self.has_auth_error = False
        self.has_server_error = False

    async def _fetch_page(self, session: aiohttp.ClientSession, offset: int) -> list:
        payload = {
            "operationName": "MakeSearch_ItemsAndFilters",
            "query": GQL_QUERY,
            "variables": {
                "queryInput": {
                    "categoryId": self.category_id,
                    "showAdultContent": "TRUE",
                    "filters": [],
                    "sort": "BY_RELEVANCE_DESC",
                    "pagination": {"offset": offset, "limit": 48},
                }
            },
        }
        try:
            async with session.post(self.GQL_URL, json=payload) as r:
                if r.status == 401:
                    self.has_auth_error = True
                    return []
                elif r.status >= 500:
                    self.has_server_error = True
                    return []
                elif r.status != 200:
                    return []

                data = await r.json()
                if "errors" in data or "data" not in data or not data["data"].get("makeSearch"):
                    return []

                items = data["data"]["makeSearch"]["items"] or []
                return [i["catalogCard"] for i in items if i.get("catalogCard")]
        except Exception:
            return []

    async def _fetch_sales(self, session: aiohttp.ClientSession, product: dict) -> dict:
        fallback_data = {
            "product_id": product["productId"],
            "title": product["title"][:50],
            "price": product.get("minSellPrice", 0),
            "rating": product.get("rating", 0),
            "feedback_quantity": product.get("feedbackQuantity", 0),
            "week": 0,
            "orders_total": 0,
        }
        async with self.sem:
            url = self.PRODUCT_URL.format(product_id=product["productId"])
            try:
                async with session.get(url, timeout=10) as r:
                    if r.status == 401:
                        self.has_auth_error = True
                        return fallback_data
                    elif r.status >= 500:
                        self.has_server_error = True
                        return fallback_data
                    elif r.status != 200:
                        return fallback_data

                    html = await r.text()
                    week = re.search(r'(\d+) человек купили на этой неделе', html)
                    orders = re.search(r'ordersAmount:(\d+)', html)

                    return {
                        "product_id": product["productId"],
                        "title": product["title"][:50],
                        "price": product.get("minSellPrice", 0),
                        "rating": product.get("rating", 0),
                        "feedback_quantity": product.get("feedbackQuantity", 0),
                        "week": int(week.group(1)) if week else 0,
                        "orders_total": int(orders.group(1)) if orders else 0,
                    }

            except Exception:
                return fallback_data

    async def _collect_raw_data(self) -> list:
        self.has_auth_error = False
        self.has_server_error = False

        page_headers = {
            "user-agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/137.0.0.0 Safari/537.36",
            "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "accept-language": "ru-RU,ru;q=0.9",
            "referer": "https://uzum.uz/",
        }

        async with aiohttp.ClientSession(headers=self.headers) as gql_session:
            print("Загрузка страниц категории...")
            tasks = [self._fetch_page(gql_session, offset) for offset in range(0, 5100, 48)]
            pages = await asyncio.gather(*tasks)
            all_products = [p for page in pages for p in page]

        print(f"Всего товаров получено: {len(all_products)}")
        if not all_products:
            return []

        deduped = {}
        for p in all_products:
            pid = p["productId"]
            if pid not in deduped or p.get("feedbackQuantity", 0) > deduped[pid].get("feedbackQuantity", 0):
                deduped[pid] = p
        all_products = list(deduped.values())

        all_products.sort(key=lambda p: p.get("feedbackQuantity", 0), reverse=True)
        top_products = all_products[: self.top_by_feedback]
        print(f"Отобрано топ-{len(top_products)} товаров по feedbackQuantity для проверки продаж...")

        print("Сбор статистики продаж по каждому товару...")
        async with aiohttp.ClientSession(headers=page_headers) as page_session:
            all_results = []
            for i in range(0, len(top_products), 20):
                batch = top_products[i:i + 20]
                tasks = [self._fetch_sales(page_session, p) for p in batch]
                results = await asyncio.gather(*tasks)
                all_results.extend(results)
                print(f"  Проверено: {min(i + 20, len(top_products))}/{len(top_products)}")
                await asyncio.sleep(2)

        return all_results

    async def get_weekly_trends(self, top_n: int = 25) -> list:
        raw_data = await self._collect_raw_data()
        if not raw_data:
            return []

        raw_data.sort(key=lambda x: x["week"], reverse=True)
        return raw_data[:top_n]

    async def get_total_leaders(self, top_n: int = 25) -> list:
        raw_data = await self._collect_raw_data()
        if not raw_data:
            return []
        raw_data.sort(key=lambda x: x["orders_total"], reverse=True)
        return raw_data[:top_n]
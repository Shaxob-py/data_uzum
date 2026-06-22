def format_weekly_top(top: list, category_name: str) -> str:
    text = f"🔥 {category_name} — HAFTALIK TRENDLAR (TOP {len(top)})\n"
    text += f"⚡️ Bu hafta eng ko'p sotilgan mahsulotlar:\n\n"

    for i, p in enumerate(top, 1):
        price_formatted = f"{p['price']:,}".replace(",", " ")

        text += f"{i}. 📦 {p['title']}\n"
        text += f"   🚀 **Bu hafta sotildi: {p['week']} ta**\n"  # Акцент на неделю
        text += f"   💰 Narxi: {price_formatted} so'm | ⭐ {p['rating']}\n"
        text += f"   🔗 uzum.uz/uz/product/{p['product_id']}\n\n"
    return text


def format_total_top(top: list, category_name: str) -> str:
    text = f"🏆 {category_name} — BARCHA VAQTDAGI LIDERLAR (TOP {len(top)})\n"
    text += f"📊 Eng ko'p buyurtma qilingan barqaror mahsulotlar:\n\n"

    for i, p in enumerate(top, 1):
        price_formatted = f"{p['price']:,}".replace(",", " ")

        text += f"{i}. 📦 {p['title']}\n"
        text += f"   📈 **Jami buyurtmalar: {p['orders_total']} ta**\n"  # Акцент на общее количество
        text += f"   💰 Narxi: {price_formatted} so'm | ⭐ {p['rating']}\n"
        text += f"   🔗 uzum.uz/uz/product/{p['product_id']}\n\n"
    return text
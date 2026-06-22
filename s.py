import httpx
for i in range(400):
    print(httpx.get("https://api.edubase.uz/api/v1/users"))
import requests
import httpx
s = "987656789,21"
s.split(',')
print(s.split(',')[1])

for i in range(400):
    print(httpx.get("https://api.edubase.uz/api/v1/users"))
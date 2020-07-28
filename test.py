import requests
import json

r = requests.get(
    'https://ip-geolocation.whoisxmlapi.com/api/v1?apiKey=at_cY0kTF6KP8LuMrXidniTMnkOa7XTE&ipAddress=191.179.109.201')

print(f'Status code {r.status_code}')
print(f'type {type(r.status_code)}')

responseJson = json.loads(r.text)

print(
    f"city: {responseJson['location']['city']} region: {responseJson['location']['region']} country: {responseJson['location']['country']}")

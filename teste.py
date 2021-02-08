import requests

while True:
    print(requests.get('http://localhost:8000/api/v1/produtos').json())

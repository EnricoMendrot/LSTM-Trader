import requests

headers = {
    "Authorization": "Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiI1IiwiZXhwIjoxNzgwODQzMjgyfQ.PecWLg6G4aR9O28d-usoJPMaMmQ0maslhvekxeMxb1Q"
}

requisicao= requests.get("http://127.0.0.1:8000/auth/refresh", headers=headers)
print(requisicao)
print(requisicao.json())
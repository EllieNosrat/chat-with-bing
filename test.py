import requests


def test():
    response = requests.get("http://localhost:7071/api/chat", json={"user_message":"Hello"})
    res = response.text
    print(res)

test()
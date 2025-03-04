import requests

API = 'https://demoforfischatagent.azurewebsites.net'

def test():
    response = requests.get(f"{API}/api/talk", json={
        "conversation_id": "b61e5ca49b9a411dbfa6902e11127b14", # for follow up
        "user_message":"Can you share some links to SEC website?",
    })
    res = response.json()
    ans = res['answer']
    conversation_id = res['conversation_id']
    print(conversation_id)
    print(ans)


def main():
    conversation_id = None
    print('This is a simple terminal app to showcase the utility.')
    print('Type exit to quit.')
    while True:
        print('User:-------------------------------')
        user_message = input("> ")
        if user_message == 'exit':
            break
        response = requests.get(f"{API}/api/talk", json={
            "conversation_id": conversation_id,
            "user_message":user_message,
        })
        res = response.json()
        conversation_id = res['conversation_id']
        print('Assistant:--------------------------')
        print(res['answer'])

if __name__ == '__main__':
    main()

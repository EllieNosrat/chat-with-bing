// sample code to call the API
// Note that if you don't send a conversation_id, system will generate one for you. 
// In the subsequent messages, you can use the conversation_id to follow up on the 
// same conversation.
// At this point, I don't have a database, so conversation history is deleted every 
// 30 to 40 minutes.


async function chat(user_message, conversation_id=undefined) {
    const API = 'https://demoforfischatagent.azurewebsites.net';
    const response = await fetch(`${API}/api/talk`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({
            "conversation_id": conversation_id, // for follow up
            "user_message":user_message,
        }),
    });
    const res = await response.json();
    return {
        answer: res.answer,
        conversation_id: res.conversation_id,
    }
}


async function test() {
    const res1 = await chat('Hi! My name is John Doe.');
    console.log(res1);
    const res2 = await chat('What is my name?', res1.conversation_id);
    console.log(res2);
}
test().catch(console.error);
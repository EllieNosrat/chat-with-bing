import azure.functions as func
import json 
import logging
from src import chat
import uuid
from datetime import datetime, timedelta
app = func.FunctionApp(http_auth_level=func.AuthLevel.ANONYMOUS)


memory = {
    '1':{'messages':[],'last_modified':0}
}

@app.route(route="chat")
def chat_route(req: func.HttpRequest) -> func.HttpResponse:
    logging.info('Python HTTP trigger function processed a request.')

    body = req.get_body().decode('utf-8')
    body = json.loads(body)
    user_message = body['user_message']
    conversation_id = body.get('conversation_id', None)
    
    if conversation_id is None:
        conversation_id = uuid.uuid4().hex
    if conversation_id not in memory:
        memory[conversation_id] = {
            'messages':[ {'role':'system','content':"You are a financial advice agent. You have access to sec.gov and finra.org for regulatory information. If you don't know the answer to a user's quesiton, use the search tool that will perform seach n these websites. Always cite your answers using the id provided in sources, for example <cite id=\"1\"/>. The answers must be tailored to US customers. Do not include site: in your search query."},],
            'last_modified':datetime.now(),
        }
    memory[conversation_id]['messages'].append({'role':'user','content':user_message})  
    memory[conversation_id]['last_modified'] = datetime.now()
    res = chat(messages=memory[conversation_id]['messages'])
    memory[conversation_id]['messages'].append(res)
    
    return func.HttpResponse(
        json.dumps({
            'answer':res,
            'conversation_id':conversation_id
        }),
        mimetype="application/json",
        status_code=200
    )
    


@app.timer_trigger(schedule="0 10 * * * *", arg_name="myTimer", run_on_startup=False,
              use_monitor=False) 
def clean_up_memory(myTimer: func.TimerRequest) -> None:
    
    if myTimer.past_due:
        logging.info('The timer is past due!')

    now = datetime.now()
    for k in list(memory.keys()):
        if now - memory[k]['last_modified'] > timedelta(minutes=30):
            del memory[k]
    
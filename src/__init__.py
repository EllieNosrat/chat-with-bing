from openai import AzureOpenAI
import os 
import requests
from bs4 import BeautifulSoup
import re 
import logging

bing_grounded_sites = [
    'sec.gov',
    'finra.org/rules-guidance/rulebooks',
]


client = AzureOpenAI(
    azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
    api_key=os.getenv("AZURE_OPENAI_API_KEY"),
    api_version=os.getenv("AZURE_OPENAI_API_VERSION")
)

def bing_search(query):
    sites_str= ' OR '.join([f'site:{s}' for s in bing_grounded_sites])
    url = f'v7.0/search?q={query} ({sites_str})'
    print(f'Searching Bing: {url}')
    response = requests.get(f'{os.getenv("BING_ENDPOINT")}{url}', headers={'Ocp-Apim-Subscription-Key': os.getenv("BING_API_KEY")})
    return response

def get_result_clean_text(url):
    response = requests.get(url)
    soup = BeautifulSoup(response.text, 'html.parser')
    for el in soup(['script', 'style', 'header', 'footer']):
        el.decompose()

    for el in soup.find_all(class_='sidebar'):
        el.decompose()

    text_content = soup.get_text()
    text_content = re.sub(r' {2,}', ' ', text_content)
    text_content = re.sub(r'\n{3,}', '\n\n', text_content)

    print(f'Extracted {len(text_content)} characters from {url}')

    return text_content

def search_and_get_text(query):
    context = []
    response = bing_search(query)
    data = response.json()
    id = 1
    if 'webPages' in data:
        for page in data['webPages']['value']:
            url = page['url']
            text = get_result_clean_text(url)
            context.append({'id':id, 'src':url, 'content':text})
            id+=1
    
    # serialize answer
    srcs = '\n'.join([f'<source id=="{c["src"]}">\n{c["content"]}\n</source>' for c in context])
    srcs_short = '\n'.join([f'<source id="{c["src"]}">\n{len(c["content"])}\n</source>' for c in context])
    print(f'<sources>{srcs_short}</sources>')
    return f'<sources>{srcs}</sources>'


bing_tool_def = {
    'type':'function',
    'function':{
        'name':'search_and_get_text',
        # 'description':f'Searches {", ".join(bing_grounded_sites)} for a query and returns the text content of the first few results',
        'strict':True,
        'parameters':{
            'type':'object',
            'properties':{
                'query':{'type':'string'}
            },
            'required':['query'],
            'additionalProperties':False
        }
    }
}

import json 
def chat(messages):
    logging.info(f"chatting with {len(messages)} messages")
    res = client.chat.completions.create(
        model="gpt-4o",
        messages=messages,
        tools=[bing_tool_def,]
    )
    logging.info(f"received: {res.choices[0].message.content}")
    appendix = []
    while res.choices[0].message.tool_calls:
        logging.info(f"processing tool_calls")
        appendix.append(res.choices[0].message)
        for tool in res.choices[0].message.tool_calls:
            logging.info(f"processing tool_call: {tool.function.name}")
            if tool.function.name == 'search_and_get_text':
                args = json.loads(tool.function.arguments)
                query = args['query']
                print(args, query)
                appendix.append({
                    'role':'tool',
                    'tool_call_id':tool.id,
                    'content': search_and_get_text(query)
                })
                logging.info(f"  - searched and got text")
        messages = messages + appendix
        print(f"sending {len(messages)} messages")
        res = client.chat.completions.create(
            model="gpt-4o",
            messages=messages,
        )
        appendix = []
    logging.info(f"returning: {res.choices[0].message.content}")
    return res.choices[0].message
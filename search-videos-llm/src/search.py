import requests
import json
from openai import AzureOpenAI
from config import AZURE_SEARCH_INDEX_NAME, AZURE_SEARCH_API_KEY, AZURE_OPENAI_DEPLOYMENT_ENDPOINT, AZURE_OPENAI_DEPLOYMENT_KEY, AZURE_SEARCH_ENDPOINT
# from config import AZURE_SEARCH_SERVICE_NAME, AZURE_SEARCH_INDEX_NAME, AZURE_SEARCH_API_KEY, AZURE_OPENAI_DEPLOYMENT_ENDPOINT, AZURE_OPENAI_DEPLOYMENT_KEY

from azure.core.credentials import AzureKeyCredential
from azure.search.documents import SearchClient

# Azure Cognitive Search Details
client = SearchClient(
    endpoint=AZURE_SEARCH_ENDPOINT,
    index_name=AZURE_SEARCH_INDEX_NAME,
    credential=AzureKeyCredential(AZURE_SEARCH_API_KEY)
)

# Define a search query
# query = question = input("Enter your question: ")
query = "What types of firms use Supervision Compliance Manager?"
results = client.search(query)
print(f"Search results for query: '{query}'") 

# Collect the relevant document snippets
relevant_documents = []
for result in results:
    relevant_documents.append(result['content'])
 
print("Retrieved Documents:")
for doc in relevant_documents:
    print(doc)

oaiClient = AzureOpenAI(
    api_version="2024-10-21",
    azure_endpoint=AZURE_OPENAI_DEPLOYMENT_ENDPOINT,
    api_key=AZURE_OPENAI_DEPLOYMENT_KEY,
)

sys_prompt = f'''
Answer questions about processes and filters found in the work documents. Be professional in your response.
++++
{relevant_documents[0]}
++++
'''
new_msg = relevant_documents[0] 

history=[]
inputs = [
    {'role':'system', 'content':sys_prompt},
    *history, 
    {'role':'user','content':new_msg}
]
openAiResult = oaiClient.chat.completions.create(
    # engine="gpt-4o",
    model="gpt-4o",
    messages=inputs,
    temperature=0.5,
    max_tokens=450,
    top_p=1,
    frequency_penalty=0,
    presence_penalty=0.6,
    stop=["\n", " Human:", " AI:"],
)

openAiMessage = openAiResult.choices[0].message

print("Response:")
print(openAiMessage)


"""
This script integrates Azure Cognitive Search and Azure OpenAI to perform a search query and generate a response 
based on the retrieved documents. It performs the following steps:
1. Imports necessary libraries and configuration variables.
2. Initializes an Azure Cognitive Search client using the provided service name, index name, and API key.
3. Executes a search query against the Azure Cognitive Search index to retrieve relevant documents.
4. Extracts the content of the retrieved documents for further processing.
5. Initializes an Azure OpenAI client using the provided endpoint and API key.
6. Constructs a system prompt using the first retrieved document and prepares a conversation history.
7. Sends the prompt and conversation history to the Azure OpenAI service to generate a response.
8. Prints the retrieved documents and the AI-generated response.
Dependencies:
- `requests` and `json` for handling HTTP requests and JSON data.
- `openai.AzureOpenAI` for interacting with Azure OpenAI.
- `azure.search.documents.SearchClient` for querying Azure Cognitive Search.
- Configuration variables (`AZURE_SEARCH_SERVICE_NAME`, `AZURE_SEARCH_INDEX_NAME`, etc.) must be defined in the `config` module.
Note:
- Ensure that the Azure Cognitive Search and Azure OpenAI services are properly configured and accessible.
- The script assumes the presence of at least one relevant document in the search results.
- The OpenAI model used is `gpt-4o`, and the parameters for the chat completion request can be adjusted as needed.
- This script is intended for demonstration purposes only and is not designed for production use.
"""

import requests
import json
from openai import AzureOpenAI
from config import AZURE_SEARCH_SERVICE_NAME, AZURE_SEARCH_INDEX_NAME, AZURE_SEARCH_API_KEY, AZURE_OPENAI_DEPLOYMENT_ENDPOINT, AZURE_OPENAI_DEPLOYMENT_KEY

from azure.core.credentials import AzureKeyCredential
from azure.search.documents import SearchClient

# Azure Cognitive Search Details
search_endpoint = f"https://{AZURE_SEARCH_SERVICE_NAME}.search.windows.net/"
client = SearchClient(
    endpoint=search_endpoint,
    index_name=AZURE_SEARCH_INDEX_NAME,
    credential=AzureKeyCredential(AZURE_SEARCH_API_KEY)
)

# Define a search query
# query = question = input("Enter your question: ")
query = "What are the SCM core modules?"
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


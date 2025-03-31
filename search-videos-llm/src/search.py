"""
This script is a proof of concept for integrating Azure Cognitive Search and Azure OpenAI to retrieve 
and process relevant information from a search index and generate responses to user queries.
Modules:
    - requests: For making HTTP requests (not used in the current implementation).
    - json: For handling JSON data (not used in the current implementation).
    - openai.AzureOpenAI: For interacting with Azure OpenAI services.
    - azure.core.credentials.AzureKeyCredential: For authenticating with Azure services.
    - azure.search.documents.SearchClient: For querying Azure Cognitive Search.
    - config: Contains configuration variables such as API keys and endpoint URLs.
Configuration:
    The script relies on the following configuration variables from the `config` module:
        - AZURE_SEARCH_INDEX_NAME: Name of the Azure Cognitive Search index.
        - AZURE_SEARCH_API_KEY: API key for Azure Cognitive Search.
        - AZURE_OPENAI_DEPLOYMENT_ENDPOINT: Endpoint for Azure OpenAI deployment.
        - AZURE_OPENAI_DEPLOYMENT_KEY: API key for Azure OpenAI deployment.
        - AZURE_SEARCH_ENDPOINT: Endpoint for Azure Cognitive Search.
Workflow:
    1. Initializes a `SearchClient` to query the Azure Cognitive Search index.
    2. Executes a search query to retrieve relevant documents based on the user's question.
    3. Collects and prints the retrieved document snippets.
    4. Constructs a system prompt using the retrieved documents to guide the Azure OpenAI model.
    5. Sends the query and context to the Azure OpenAI model to generate a precise response.
    6. Prints the question and the generated response.
Usage:
    - Modify the `query` variable to specify the search query.
    - Ensure that the required configuration variables are correctly set in the `config` module.
    - Run the script to retrieve relevant documents and generate a response using Azure OpenAI.
Note:
    - This script is intended for demonstration purposes only and is not designed for production use.
"""

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
# query = "What types of firms use Supervision Compliance Manager?"
# query = "What is the first category of Data Domains?"
# query = "Who founded the company?"
query = "Tell me about the The account rank module"
# query = "What are physical units?"
results = client.search(query)
print(f"Search results for query: '{query}'") 

# Collect the relevant document snippets
number_of_relevant_documents = 0
relevant_documents = []
for result in results:
    relevant_documents.append(result['content'])
    number_of_relevant_documents += 1
 
print("Retrieved Documents:")
# for doc in relevant_documents:
    # print(doc)

print(f"Number of relevant documents: {number_of_relevant_documents}")

oaiClient = AzureOpenAI(
    api_version="2024-10-21",
    azure_endpoint=AZURE_OPENAI_DEPLOYMENT_ENDPOINT,
    api_key=AZURE_OPENAI_DEPLOYMENT_KEY,
)

all_relevant_docs = ''
for i in range(len(relevant_documents)):
    all_relevant_docs += relevant_documents[i] + '\n\n'

sys_prompt = f'''
Answer questions about information found in the video transcriptions. Be professional in your response. 
We want a precise response - not just a general summary of the text.
Please pay the most attention to where in the text you can find the specific answer to the question.
Be precise in your answer.
++++
{all_relevant_docs}
++++
'''
new_msg = query 

history=[]
inputs = [
    {'role':'system', 'content':sys_prompt},
    *history, 
    {'role':'user','content':new_msg}
]
openAiResult = oaiClient.chat.completions.create(
    model="gpt-4o",
    messages=inputs,
    temperature=0.3,
    max_tokens=1450,
    # top_p=1,
    # frequency_penalty=0,
    # presence_penalty=0.6,
    # stop=["\n", " Human:", " AI:"],
)

openAiMessage = openAiResult.choices[0].message

print("==========================================================")
print("Question:")
print(query)
print("Response:")
print(openAiMessage.content)


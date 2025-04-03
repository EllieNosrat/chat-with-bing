'''
This program processes video transcript files, converts them into JSON 
documents, and uploads them to an Azure Cognitive Search index for 
semantic search capabilities. It includes functionality for creating 
the search index, processing transcript files, and uploading documents.
Key Features:
- Converts transcript `.txt` files into structured JSON documents.
- Creates an Azure Cognitive Search index with vector search capabilities.
- Uploads processed documents to the search index in batches.
Dependencies:
- Azure SDKs: azure.search.documents, azure.core.credentials, openai.
- Environment management: dotenv.
- File handling: os, glob, shutil.
Usage:
- Place transcript `.txt` files in the `data/transcripts` folder.
- Run the script to process files, create the index, and upload documents.
Note:
- This script is intended for demonstration purposes only and is not designed for production use.
'''

import os 
from openai import AzureOpenAI
import json 
import re 
from azure.core.credentials import AzureKeyCredential
from azure.search.documents import SearchClient
from azure.search.documents.indexes import SearchIndexClient 
from azure.search.documents.indexes.models import SimpleField, SearchableField, SearchIndex, SearchField
from config import AZURE_SEARCH_ENDPOINT, AZURE_SEARCH_API_KEY, AZURE_OPENAI_ENDPOINT, AZURE_OPENAI_API_KEY, AZURE_OPENAI_DEPLOYMENT_ENDPOINT, AZURE_OPENAI_DEPLOYMENT_KEY, AZURE_SEARCH_INDEX_NAME

from dotenv import load_dotenv

def clean_str_for_id(id:str)->str:
    '''Cleans a string to be used as an id in Azure Search'''
    return re.sub(r'[^a-zA-Z0-9]','_',id)

oai_client = AzureOpenAI(
    api_version="2024-10-21",
    azure_endpoint=AZURE_OPENAI_DEPLOYMENT_ENDPOINT,
    api_key=AZURE_OPENAI_DEPLOYMENT_KEY,
)

def create_ai_search_index(index_name: str):
    ai_search_index_client = SearchIndexClient(
        endpoint=AZURE_SEARCH_ENDPOINT, 
        credential=AzureKeyCredential(AZURE_SEARCH_API_KEY),
    )

    # Check if the index already exists
    try:
        ai_search_index_client.get_index(index_name)
        print(f"Index {index_name} already exists. No need to create a new index.")
        return
    except Exception as e:
        print(f"Index {index_name} does not exist. Creating a new index.")

    # Create the index
    index = SearchIndex(
        name=index_name,
        fields=[
            SimpleField(name="id", type="Edm.String", key=True),
            SearchableField(name="content", type="Edm.String", analyzer_name="en.microsoft"),
            SimpleField(name="transcription_file_name", type="Edm.String", retrievable=True),
            SimpleField(name="chunk_start_seconds", type="Edm.Int32", retrievable=True, filterable=True, sortable=True),
            SimpleField(name="video_file_name", type="Edm.String", retrievable=True),
            SimpleField(name="chunk_number", type="Edm.Int32", retrievable=True, filterable=True, sortable=True),
            SearchField(name="vector", type="Collection(Edm.Single)", vector_search_dimensions=1536, vector_search_profile_name='vector-profile-1'),
        ],
        vector_search= {
            "algorithms": [
                {
                    "name": "hnsw-1",
                    "kind": "hnsw",
                    "hnswParameters": {
                        "m": 4,
                        "efConstruction": 400,
                        "efSearch": 500,
                        "metric": "cosine"
                    }
                },

            ],
            "profiles": [
            {
                "name": "vector-profile-1",
                "algorithm": "hnsw-1"
            }
        ]
    }
    )
    ai_search_index_client.create_index(index)

def process_file_to_json(src_file_path: str, dest_file_path: str, vectorize: bool = True):
    '''Converts a text file to a json file with the following structure:
    {
        'content': str, # the content of the text file
        'video_file_name': str, # the name of the video file
        'chunk_start_seconds': int, # the start time of the chunk in seconds
        'transcription_file_name': str, # the name of the transcription file
        'chunk_number': int, # the chunk number of the transcription
        'vector': list, # the vector representation of the content'
    }

    Note: the vector is only computed if vectorize is set to True

    Note: At this point, the transcriptions are put into one chunk. Please implement your
    own logic to split the transcriptions into chunks if needed. My recommendation would be to 
    have the transcripts printed per minute (or 30 seconds) of the video. In this case, the chunk_start_seconds
    would be the start time of the chunk.
    '''
    print(f'processing {src_file_path} to {dest_file_path}')

    content = open(src_file_path, 'r').read()
    chunk_number = 0
    chunk_start_seconds = 0
    
    vector=None
    if vectorize:
        vectorizer = oai_client.embeddings.create(
            input=[content],
            model='text-embedding-ada-002',
        )
        vector = vectorizer.data[0].embedding
    video_file_name = os.path.basename(src_file_path).replace('.txt','.mp4')
    transcription_file_name = os.path.basename(src_file_path)
    id = f"{video_file_name}#{chunk_number}"

    document = {
        'id': clean_str_for_id(id),
        'content': content,
        'video_file_name': video_file_name,
        'chunk_start_seconds': chunk_start_seconds,
        'transcription_file_name': transcription_file_name,
        'chunk_number': chunk_number,
        'vector': vector,
    }

    with open(dest_file_path, 'w') as f:
        json.dump(document, f)

def upload_documents_to_index(index_name: str, document_paths: list, *,batch_size=5):
    ai_search_client = SearchClient(
        endpoint=AZURE_SEARCH_ENDPOINT, 
        index_name=index_name, 
        credential=AzureKeyCredential(AZURE_SEARCH_API_KEY),
    )
    batch = []
    for document_path in document_paths:
        with open(document_path, 'r') as f:
            document = json.load(f)
            batch.append(document)
        if len(batch) == batch_size:
            ai_search_client.upload_documents(documents=batch)
            batch = []
    if len(batch) > 0:
        ai_search_client.upload_documents(documents=batch)

def get_folder_full_path(folder_name):
    current_folder = os.path.dirname(__file__)
    parent_folder = os.path.dirname(current_folder)
    target_folder = os.path.join(parent_folder, folder_name)
    return target_folder

def main():
    from dotenv import load_dotenv
    load_dotenv('.env', override=True)
    from glob import glob 
    import shutil
    transcript_folder = get_folder_full_path('data/transcripts')
    transcript_files_selector = os.path.join(transcript_folder, '*.txt')
    json_folder = get_folder_full_path('data/transcripts_json')
    json_files_selector = os.path.join(json_folder, '*.json')

    src_files = glob(transcript_files_selector)
    shutil.rmtree(json_folder, ignore_errors=True)
    os.makedirs(json_folder, exist_ok=True)

    # convert txt files to json
    for src_file in src_files:
        src_file = src_file.replace('\\','/')
        dest_file = src_file.replace('/transcripts/','/transcripts_json/').replace('.txt', '.json')
        process_file_to_json(src_file, dest_file, vectorize=True)
    
    create_ai_search_index(AZURE_SEARCH_INDEX_NAME)
    # upload documents
    documents = glob(json_files_selector)
    upload_documents_to_index(AZURE_SEARCH_INDEX_NAME, documents)
    print('Finished uploading documents to index')

if __name__ == "__main__":
    main()   
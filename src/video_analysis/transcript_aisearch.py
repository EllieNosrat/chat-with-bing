import os 
from openai import AzureOpenAI
import json 
import re 
from azure.core.credentials import AzureKeyCredential
from azure.search.documents import SearchClient
from azure.search.documents.indexes import SearchIndexClient 
from azure.search.documents.indexes.models import SimpleField, SearchableField, SearchIndex, SearchField

from dotenv import load_dotenv
load_dotenv('.env', override=True)

def clean_str_for_id(id:str)->str:
    '''Cleans a string to be used as an id in Azure Search'''
    return re.sub(r'[^a-zA-Z0-9]','_',id)

oai_client = AzureOpenAI(
    azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
    api_key=os.getenv("AZURE_OPENAI_API_KEY"),
    api_version="2024-02-01",
)

def create_ai_search_index(index_name: str):
    ai_search_index_client = SearchIndexClient(
        endpoint=os.getenv("AZURE_SEARCH_ENDPOINT"), 
        credential=AzureKeyCredential(os.getenv("AZURE_SEARCH_API_KEY")),
    )

    index = SearchIndex(
        name=index_name,
        fields=[
            SimpleField(name="id", type="Edm.String", key=True),
            SearchableField(name="content", type="Edm.String", analyzer_name="en.microsoft"),
            SimpleField(name="transcription_file_name", type="Edm.String", retrievable=True),
            SimpleField(name="chunk_start_seconds", type="Edm.Int32", retrievable=True, filterable=True, sortable=True),
            SimpleField(name="video_file_name", type="Edm.String", retrievable=True),
            SimpleField(name="chunk_number", type="Edm.Int32", retrievable=True, filterable=True, sortable=True),
            SearchField(name="vector", type="Collection(Edm.Single)", retrievable=True, vector_search_dimensions=1536, vector_search_profile_name='vector-profile-1'),
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


def process_file_to_json(src_file_path: str, dest_file_path: str, vectorize=False):
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
        endpoint=os.getenv("AZURE_SEARCH_ENDPOINT"), 
        index_name=index_name, 
        credential=AzureKeyCredential(os.getenv("AZURE_SEARCH_API_KEY")),
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




if __name__ == "__main__":
    from dotenv import load_dotenv
    load_dotenv('.env', override=True)
    from glob import glob 
    import shutil
    src_files = glob('data/transcripts/*.txt')
    shutil.rmtree('data/transcripts_json', )
    os.makedirs('data/transcripts_json', exist_ok=True)

    # convert txt files to json
    for src_file in src_files:
        src_file = src_file.replace('\\','/')
        dest_file = src_file.replace('/transcripts/','/transcripts_json/').replace('.txt', '.json')
        process_file_to_json(src_file, dest_file, vectorize=True)
    
    # create index
    index_name = 'transcripts'  
    # create_ai_search_index(index_name)

    # upload documents
    documents = glob('data/transcripts_json/*.json')
    upload_documents_to_index(index_name, documents)
    print('done')
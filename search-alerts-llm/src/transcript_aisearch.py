import os 
from openai import AzureOpenAI
import json 
import re 
from azure.core.credentials import AzureKeyCredential
from azure.search.documents import SearchClient
from azure.search.documents.indexes import SearchIndexClient 
from azure.search.documents.indexes.models import SimpleField, SearchableField, SearchIndex, SearchField
from config import AZURE_SEARCH_INDEX_NAME, AZURE_SEARCH_API_KEY, AZURE_OPENAI_DEPLOYMENT_ENDPOINT, AZURE_OPENAI_DEPLOYMENT_KEY, AZURE_SEARCH_ENDPOINT, AZURE_OPENAI_ENDPOINT, AZURE_OPENAI_API_KEY

from dotenv import load_dotenv
load_dotenv('.env', override=True)

oai_client = AzureOpenAI(
    azure_endpoint=AZURE_OPENAI_DEPLOYMENT_ENDPOINT,
    api_key=AZURE_OPENAI_DEPLOYMENT_KEY,
    api_version="2024-02-01",
)

def clean_str_for_id(id:str)->str:
    '''Cleans a string to be used as an id in Azure Search'''
    return re.sub(r'[^a-zA-Z0-9]','_',id)

    # azure_endpoint=os.getenv("AZURE_OPENAI_DEPLOYMENT_ENDPOINT"),
    # api_key=os.getenv("AZURE_OPENAI_DEPLOYMENT_API_KEY"),
    # api_version="2024-02-01"

def create_ai_search_index(index_name: str, fields: list = None):
    ai_search_index_client = SearchIndexClient(
        endpoint=AZURE_SEARCH_ENDPOINT, 
        credential=AzureKeyCredential(AZURE_SEARCH_API_KEY),
    )

    try:
        ai_search_index_client.get_index(index_name)
        print(f"Index {index_name} already exists. No need to create a new index.")
        return
    except Exception as e:
        print(f"Index {index_name} does not exist. Creating a new index.")

    # Check if the index already exists
    try:
        ai_search_index_client.get_index(index_name)
        print(f"Index {index_name} already exists. No need to create a new index.")
        return
    except Exception as e:
        print(f"Index {index_name} does not exist. Creating a new index.")

    index = SearchIndex(
        name=index_name,
        fields=fields,
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
    ```
    {
        "id": str, # the id of the document, in this case the video file name + chunk number
        "content": str, # the content of the text file
        "video_file_name": str, # the name of the video file
        "chunk_start_seconds": int, # the start time of the chunk in seconds
        "transcription_file_name": str, # the name of the transcription file
        "chunk_number": int, # the chunk number of the transcription
        "vector": list, # the vector representation of the content'
    }
    ```

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
    # azureSearchApiKey = os.getenv("AZURE_SEARCH_API_KEY")
    # azureSearchEndpoint = AZURE_SEARCH_ENDPOINT # os.getenv("AZURE_SEARCH_ENDPOINT")
    ai_search_client = SearchClient(
        endpoint=AZURE_SEARCH_ENDPOINT, 
        index_name=index_name, 
        credential=AzureKeyCredential(AZURE_SEARCH_API_KEY),
    )
    # ai_search_client = SearchClient(
    #     endpoint=azureSearchEndpoint, 
    #     index_name=index_name, 
    #     credential=AzureKeyCredential(azureSearchApiKey),
    # )
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

def process_doc_intel_to_json(src_file_path: str, dest_file_path: str, vectorize=False):
    '''Converts a text file to a json file with the following structure:
    ```
    {
        "id": str, # the id of the document, in this case the video file name + chunk number
        "content": str, # the content of the text file
        "original_file_name": str, # the name of the transcription file
        "chunk_number": int, # the chunk number of the transcription
        "vector": list, # the vector representation of the content'
    }
    ```
    '''
    with open(src_file_path, 'r') as f:
        content_all = json.load(f)
    content_markdown = content_all['analyzeResult']['content']
    markdown_break_priority = [
        {'text': '\n# ', 'break_before': True,},
        {'text': '\n## ', 'break_before': True,},
        {'text': '\n### ','break_before': True,},
        {'text': '</table>', 'break_before': False,},
        {'text': '<!-- PageBreak -->', 'break_before': True,},
        {'text': '\n\n', 'break_before': True,},
        {'text': '\n','break_before': True,},
        ]
    CONTENT_MAX_LENGTH = 5000
    CONTENT_MIN_LENGTH = 3000
    completed = False
    chunk_number = 0
    chunks = []

    while not completed:
        # Extract the maximum length of content
        if len(content_markdown) < CONTENT_MAX_LENGTH:
            # If the content is less than the minimum length, take the whole content
            content = content_markdown
        else:
            content: str = content_markdown[:CONTENT_MAX_LENGTH]
        breakpoint_found = False

        # Iterate through breakpoints by priority
        for b in markdown_break_priority:
            breakpoint = b['text']
            break_before = b['break_before']
            # Find the last occurrence of the breakpoint within the valid range
            breakpoint_index = content.rfind(breakpoint, CONTENT_MIN_LENGTH, CONTENT_MAX_LENGTH)
            if breakpoint_index != -1:
                # If break_before is True, adjust the content to include the breakpoint
                if break_before:
                    content = content_markdown[:breakpoint_index]
                else:
                    content = content_markdown[:breakpoint_index + len(breakpoint)]
                breakpoint_found = True
                break

        # If no breakpoint is found, take the maximum allowed length
        if not breakpoint_found:
            content = content_markdown[:CONTENT_MAX_LENGTH]

        vector = None
        if vectorize:
            vectorizer = oai_client.embeddings.create(
                input=[content],
                model='text-embedding-ada-002',
            )
            vector = vectorizer.data[0].embedding
        # Add the chunk to the list
        chunk={
            'id': clean_str_for_id(f"{os.path.basename(src_file_path)}#{chunk_number}"),
            'content': content.strip(),
            'chunk_number': chunk_number,
            'original_file_name': os.path.basename(src_file_path),
            'vector': vector,
        }
        with open(dest_file_path.replace('.chunk.json',f'.chunk{chunk_number}.json'), 'w') as f:
            json.dump(chunk, f, indent=4)

        # Remove the processed content from the markdown
        content_markdown = content_markdown[len(content):]
        chunk_number += 1

        # Check if all content has been processed
        if len(content_markdown) == 0:
            completed = True
        

def process_video():
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
    # create_ai_search_index(index_name, fields=[
    #     SimpleField(name="id", type="Edm.String", key=True),
    #     SearchableField(name="content", type="Edm.String", analyzer_name="en.microsoft"),
    #     SimpleField(name="transcription_file_name", type="Edm.String", retrievable=True),
    #     SimpleField(name="chunk_start_seconds", type="Edm.Int32", retrievable=True, filterable=True, sortable=True),
    #     SimpleField(name="video_file_name", type="Edm.String", retrievable=True),
    #     SimpleField(name="chunk_number", type="Edm.Int32", retrievable=True, filterable=True, sortable=True),
    #     SearchField(name="vector", type="Collection(Edm.Single)", retrievable=True, vector_search_dimensions=1536, vector_search_profile_name='vector-profile-1'),
    # ])

    # upload documents
    documents = glob('data/transcripts_json/*.json')
    upload_documents_to_index(index_name, documents)
    print('done')

def get_folder_full_path(folder_name):
    current_folder = os.path.dirname(__file__)
    parent_folder = os.path.dirname(current_folder)
    target_folder = os.path.join(parent_folder, folder_name)
    return target_folder


def process_doc_intel(src_glob, *, create_index=False):
    from dotenv import load_dotenv
    load_dotenv('.env', override=True)
    from glob import glob 
    import shutil

    pdfjson_folder = get_folder_full_path(src_glob)
    src_files: list[str] = glob(pdfjson_folder)
    
    index_name = 'pdf_docintel'  
    # create index
    # if create_index:
    create_ai_search_index(index_name, fields=[
        SimpleField(name="id", type="Edm.String", key=True),
        SearchableField(name="content", type="Edm.String", analyzer_name="en.microsoft"),
        SimpleField(name="original_file_name", type="Edm.String", retrievable=True),
        SimpleField(name="chunk_number", type="Edm.Int32", retrievable=True, filterable=True, sortable=True),
        SearchField(name="vector", type="Collection(Edm.Single)", retrievable=True, vector_search_dimensions=1536, vector_search_profile_name='vector-profile-1'),
    ])
    
    for src_file in src_files:
        src_file = src_file.replace('\\','/')
        dest_file = src_file.replace('.pdf.json', '.chunk.json')
        process_doc_intel_to_json(src_file, dest_file, vectorize=True)

    # upload documents
    results_pattern = src_glob.replace('.pdf.json', '.chunk*.json')
    documents = glob(results_pattern)
    upload_documents_to_index(index_name, documents)

if __name__ == "__main__":
    # process_PDFs
    process_doc_intel('data/pdf_docintel/*.pdf.json', create_index=False)

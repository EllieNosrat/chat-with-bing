import requests
import json
import os
from openai import AzureOpenAI
from config import AZURE_SEARCH_SERVICE_NAME, AZURE_SEARCH_INDEX_NAME, AZURE_SEARCH_API_KEY, AZURE_OPENAI_DEPLOYMENT_ENDPOINT, AZURE_OPENAI_DEPLOYMENT_KEY, DEPLOYED_MODEL, AZURE_OPENAI_API_VERSION, AZURE_OPENAI_ENDPOINT, AZURE_OPENAI_KEY, AZURE_OPENAI_WHISPER_DEPLOYMENT_ENDPOINT, AZURE_OPENAI_WHISPER_DEPLOYMENT_KEY, AZURE_OPENAI_WHISPER_DEPLOYMENT_VERSION, AZURE_STORAGE_CONNECTION_STRING
from azure.core.credentials import AzureKeyCredential
from azure.search.documents import SearchClient
from azure.storage.blob import BlobServiceClient

def get_video_full_path(file_name, folder_name):
    current_folder = os.path.dirname(__file__)
    parent_folder = os.path.dirname(current_folder)
    video_folder = os.path.join(parent_folder, folder_name)
    return os.path.join(video_folder, file_name)

def save_string_to_file(file_name, content):
    with open(file_name, "w") as file:
        file.write(content)

def download_file_from_blob_storage(blob_name, file_path, container_name):
    blob_service_client = BlobServiceClient.from_connection_string(AZURE_STORAGE_CONNECTION_STRING)
    blob_client = blob_service_client.get_blob_client(container=container_name, blob=blob_name)
    with open(file_path, "wb") as file:
        blob_data = blob_client.download_blob()
        blob_data.readinto(file)

def upload_file_to_blob_storage(file_path, blob_name, container_name):
    blob_service_client = BlobServiceClient.from_connection_string(AZURE_STORAGE_CONNECTION_STRING)
    blob_client = blob_service_client.get_blob_client(container="transcripts", blob=blob_name)
    with open(file_path, "rb") as data:
        blob_client.upload_blob(data, overwrite=True)

video_container_name = "mp4s"
transcript_container_name = "transcripts"
video_folder_name = "videos-to-search"
transcript_folder_name = "transcripts"
blob_service_client = BlobServiceClient.from_connection_string(AZURE_STORAGE_CONNECTION_STRING)
container_client = blob_service_client.get_container_client(video_container_name)
# Process each blob in container
blobs = container_client.list_blobs()
for blob in blobs:
    print(f"Processing {blob.name}...")
    video_file_name = blob.name
    video_full_path = get_video_full_path(video_file_name, video_folder_name)
    transcript_file_name = video_file_name.replace(".mp4", ".txt")
    transcript_full_path = get_video_full_path(transcript_file_name, transcript_folder_name)
    download_file_from_blob_storage(video_file_name, video_full_path, "mp4s")
    print(f"Video downloaded from Azure Blob Storage to {video_full_path}")

    client = AzureOpenAI(
        api_key=AZURE_OPENAI_WHISPER_DEPLOYMENT_KEY,
        api_version=AZURE_OPENAI_WHISPER_DEPLOYMENT_VERSION,
        azure_endpoint = AZURE_OPENAI_WHISPER_DEPLOYMENT_ENDPOINT
    )

    deployment_id = "whisper"
    video_file=open(video_full_path, mode="rb")
    transcript_results = client.audio.transcriptions.create(
        file=video_file,
        model=deployment_id
    )

    save_string_to_file(transcript_full_path, transcript_results.text)
    print(f"Transcript saved locally to {transcript_full_path}")

    upload_file_to_blob_storage(transcript_full_path, transcript_file_name, transcript_container_name)
    print(f"Transcript uploaded to Azure Blob Storage container {transcript_container_name} with blob name {transcript_file_name}")

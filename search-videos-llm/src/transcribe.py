# This script downloads a video file from Azure Blob Storage, extracts the audio, transcribes it using OpenAI's Whisper model, and uploads the transcription back to Azure Blob Storage.
# It is still incomplete, as of 2025-03-25
# This script requires the following libraries:
# pip install azure-storage-blob openai moviepy
# pip install moviepy[ffmpeg]
# pip install openai
# pip install azure-ai-ml

import os
from azure.storage.blob import BlobServiceClient, BlobClient, ContainerClient
import openai
from moviepy.editor import AudioFileClip

# Azure Blob Storage configuration
AZURE_STORAGE_CONNECTION_STRING = "DefaultEndpointsProtocol=https;AccountName=dgtest0314storage;AccountKey=xW5GbvWncLoFqyRMGQrp9JhSS7IVQgluFCPjIQnjazjPaPdxFKQxU+UQS3ZBOPY+b0leyGuFHLYk+AStnlTcSA==;EndpointSuffix=core.windows.net"
INPUT_CONTAINER_NAME = "mp4s"
OUTPUT_CONTAINER_NAME = "transcriptions"

# OpenAI Whisper configuration
openai.api_key = "your_openai_api_key"

def download_blob_to_file(blob_service_client, container_name, blob_name, download_path):
    blob_client = blob_service_client.get_blob_client(container=container_name, blob=blob_name)
    with open(download_path, "wb") as file:
        file.write(blob_client.download_blob().readall())

def upload_file_to_blob(blob_service_client, container_name, file_path, blob_name):
    blob_client = blob_service_client.get_blob_client(container=container_name, blob=blob_name)
    with open(file_path, "rb") as file:
        blob_client.upload_blob(file, overwrite=True)

def transcribe_audio(file_path):
    with open(file_path, "rb") as audio_file:
        response = openai.Audio.transcribe("whisper-1", audio_file)
    return response["text"]

def extract_audio_from_video(video_path, audio_path):
    audio_clip = AudioFileClip(video_path)
    audio_clip.write_audiofile(audio_path)
    audio_clip.close()

def main():
    blob_service_client = BlobServiceClient.from_connection_string(AZURE_STORAGE_CONNECTION_STRING)
    
    # Example: Replace with your actual blob name
    input_blob_name = "example_video.mp4"
    local_video_path = "temp_video.mp4"
    local_audio_path = "temp_audio.mp3"
    local_transcription_path = "transcription.txt"

    # Download video from Azure Blob Storage
    download_blob_to_file(blob_service_client, INPUT_CONTAINER_NAME, input_blob_name, local_video_path)

    # Extract audio from video
    extract_audio_from_video(local_video_path, local_audio_path)

    # Transcribe audio using OpenAI Whisper
    transcription_text = transcribe_audio(local_audio_path)

    # Save transcription to a local file
    with open(local_transcription_path, "w") as file:
        file.write(transcription_text)

    # Upload transcription to Azure Blob Storage
    output_blob_name = f"{os.path.splitext(input_blob_name)[0]}.txt"
    upload_file_to_blob(blob_service_client, OUTPUT_CONTAINER_NAME, local_transcription_path, output_blob_name)

    # Clean up local files
    os.remove(local_video_path)
    os.remove(local_audio_path)
    os.remove(local_transcription_path)

if __name__ == "__main__":
    main()
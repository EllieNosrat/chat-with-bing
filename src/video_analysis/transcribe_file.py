from openai import AzureOpenAI
import os

client = AzureOpenAI(
    azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
    api_key=os.getenv("AZURE_OPENAI_API_KEY"),
    api_version="2024-02-01",
)
deployment_id = "whisper"


def transcribe_file(file_path):
    with open(file_path, mode="rb") as video_file:
        transcript_results = client.audio.transcriptions.create(
            file=video_file,
            model=os.getenv("AZURE_OPENAI_TRANSCRIPTION_MODEL"),
            response_format='verbose_json',
            timestamp_granularities=['segment'],
        )
        print(transcript_results)
        return transcript_results
    

if __name__ == "__main__":
    from dotenv import load_dotenv
    load_dotenv('.env', override=True)
    print(os.getenv("AZURE_OPENAI_ENDPOINT"))
    print(os.getenv("AZURE_OPENAI_API_KEY"))
    print(os.getenv("AZURE_OPENAI_TRANSCRIPTION_MODEL"))
    transcribe_file('data/videos/SCM #2 Product Overview.mp4')

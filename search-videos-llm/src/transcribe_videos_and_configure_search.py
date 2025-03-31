import transcript_aisearch
import transcribe_videos

def main():
    """
    Main function to orchestrate the transcription of videos and configuration of AI-based search.
    This function performs the following tasks:
    1. Executes the `transcribe_videos` module to transcribe video files.
    2. Executes the `transcript_aisearch` module to configure AI-based search using the generated transcripts.
    3. Prints status messages to indicate the progress and completion of tasks.
    Raises:
        Any exceptions raised by the `transcribe_videos` or `transcript_aisearch` modules.
    Note:
        This script is intended for demonstration purposes only and is not designed for production use.
    """

    print("Running transcribe-videos.py...")
    transcribe_videos.main()

    print("Running transcript_aisearch.py...")
    transcript_aisearch.main()

    print("All tasks completed successfully.")

if __name__ == "__main__":
    main()
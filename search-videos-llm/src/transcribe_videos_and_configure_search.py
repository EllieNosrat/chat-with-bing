# Import the scripts
import transcript_aisearch
import transcribe_videos

def main():
    # Call the main method of transcribe-videos.py
    print("Running transcribe-videos.py...")
    transcribe_videos.main()

    # Call the main method of transcript_aisearch.py
    print("Running transcript_aisearch.py...")
    transcript_aisearch.main()

    print("All tasks completed successfully.")

if __name__ == "__main__":
    main()
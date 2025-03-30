import transcript_aisearch
import transcribe_videos

def main():
    print("Running transcribe-videos.py...")
    transcribe_videos.main()

    print("Running transcript_aisearch.py...")
    transcript_aisearch.main()

    print("All tasks completed successfully.")

if __name__ == "__main__":
    main()
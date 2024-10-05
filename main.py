import os
import sys
from transcriber import VideoTranscriber
import single_shot_fixer
import logging
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')


def main():
    if len(sys.argv) != 2:
        logging.error("Usage: python script.py <path_to_video_file>")
        sys.exit(1)

    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise ValueError("OPENAI_API_KEY environment variable is not set")

    video_path = sys.argv[1]
    transcriber = VideoTranscriber(video_path)
    transcription, transcription_path = transcriber.process()

    logging.info("Fixing transcription...")
    improved = single_shot_fixer.fix(file_path=transcription_path, api_key=api_key)
    logging.info("Improved transcription:")
    logging.info(improved)


if __name__ == '__main__':
    main()

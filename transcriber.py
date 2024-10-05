import os
import subprocess
from pathlib import Path
from typing import Tuple
import logging

from openai import OpenAI

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')


class VideoTranscriber:
    def __init__(self, video_path: str):
        self.video_path = Path(video_path)
        self.audio_path = self.video_path.with_suffix('.mp3')
        self.whisper_subs_path = self.video_path.parent / "whisper_subs"
        self.transcription_path = self.whisper_subs_path / "transcription.txt"

        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("OPENAI_API_KEY environment variable is not set")
        self.client = OpenAI(api_key=api_key)

    def extract_audio(self) -> None:
        """Extract audio from video file if it doesn't already exist."""
        if self.audio_path.exists():
            logging.info('Audio already extracted')
            return

        command = [
            'ffmpeg',
            '-i', str(self.video_path),
            '-q:a', '0',
            '-map', 'a',
            str(self.audio_path)
        ]

        try:
            subprocess.run(command, check=True, capture_output=True, text=True)
            logging.info(f"Audio extracted successfully: {self.audio_path}")
        except subprocess.CalledProcessError as e:
            logging.error(f"Error extracting audio: {e}")
            logging.error(f"FFMPEG stderr: {e.stderr}")
            raise

    def transcribe(self) -> Tuple[str, Path]:
        """Transcribe audio file if transcription doesn't already exist."""
        if self.transcription_path.exists():
            logging.info('Transcription already exists')
            return self.transcription_path.read_text(), self.transcription_path

        if not self.audio_path.exists():
            logging.warning("Audio file not found. Extracting audio first.")
            self.extract_audio()

        try:
            with self.audio_path.open("rb") as audio_file:
                transcription = self.client.audio.transcriptions.create(
                    model="whisper-1",
                    file=audio_file,
                    response_format="text"
                )

            self.whisper_subs_path.mkdir(parents=True, exist_ok=True)
            self.transcription_path.write_text(transcription)
            logging.info(f"Transcription saved to: {self.transcription_path}")

            return transcription, self.transcription_path
        except Exception as e:
            logging.error(f"Error during transcription: {str(e)}")
            raise

    def process(self) -> Tuple[str, Path]:
        """Extract audio and transcribe in one step."""
        self.extract_audio()
        return self.transcribe()

 

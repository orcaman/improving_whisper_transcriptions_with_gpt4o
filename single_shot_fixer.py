import json
from openai import OpenAI
from pathlib import Path
import logging
from typing import Dict, Any

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')


class TranscriptionImprover:
    def __init__(self, api_key: str):
        self.client = OpenAI(api_key=api_key)
        self.model = "gpt-4o"

    def suggest_improvements(self, file_path: Path) -> Dict[str, Any]:
        try:
            original_transcription = self._read_file(file_path)
            video_topic = self._get_video_topic(original_transcription)
            suggestions = self._get_suggestions(original_transcription, video_topic)
            return suggestions
        except Exception as e:
            logging.error(f"Error in suggest_improvements: {str(e)}")
            raise

    def _read_file(self, file_path: Path) -> str:
        try:
            with file_path.open('r') as file:
                return file.read()
        except IOError as e:
            logging.error(f"Error reading file {file_path}: {str(e)}")
            raise

    def _get_video_topic(self, transcription: str) -> str:
        prompt = f"The following text is a transcription of a video. What is the video about?\nTranscription:\n{transcription}"
        response = self._create_chat_completion(prompt)
        return response.choices[0].message.content.strip()

    def _get_suggestions(self, transcription: str, video_topic: str) -> Dict[str, Any]:
        prompt = f"""The following text is a transcription of a video. The video is about "{video_topic}". 
        Based on this information, suggest corrections to possible mistakes in the transcription. 

        Generate JSON of suggestions in the following format: 

        {{
                "word_to_replace_1": "suggested_word_1",
                "word_to_replace_2": "suggested_word_2",
                ...
        }}

        Transcription: 
        {transcription}
        """
        response = self._create_chat_completion(prompt, response_format={"type": "json_object"})
        return json.loads(response.choices[0].message.content.strip())

    def _create_chat_completion(self, prompt: str, response_format: Dict[str, str] = None) -> Any:
        messages = [
            {"role": "system", "content": "You are an AI assistant that improves video transcriptions."},
            {"role": "user", "content": prompt}
        ]
        kwargs = {
            "model": self.model,
            "messages": messages,
            "n": 1,
            "temperature": 0.5,
        }
        if response_format:
            kwargs["response_format"] = response_format
        return self.client.chat.completions.create(**kwargs)


def save_suggestions(file_path: Path, suggestions: Dict[str, Any]) -> Path:
    output_path = file_path.with_suffix('.suggestions.json')
    with output_path.open('w') as file:
        json.dump(suggestions, file, indent=2)
    return output_path


def save_improved(file_path: Path, improved_transcription: str) -> Path:
    output_path = file_path.with_suffix('.improved.txt')
    with output_path.open('w') as file:
        file.write(improved_transcription)
    return output_path


def find_and_replace_suggestions(file_path: Path, suggestions: Dict[str, str]) -> str:
    with file_path.open('r') as file:
        original_transcription = file.read()
        for word_to_replace, suggested_word in suggestions.items():
            original_transcription = original_transcription.replace(word_to_replace, suggested_word)
        return original_transcription


def fix(file_path: Path, api_key: str) -> str:
    try:
        improver = TranscriptionImprover(api_key)
        suggestions = improver.suggest_improvements(file_path)
        save_suggestions(file_path, suggestions)
        improved_transcription = find_and_replace_suggestions(file_path, suggestions)
        save_improved(file_path, improved_transcription)
        return improved_transcription
    except Exception as e:
        logging.error(f"Error in fix function: {str(e)}")
        raise
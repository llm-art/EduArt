"""OpenAI LLM provider via Harvard API gateway with vision support."""

import os
import time
import logging
import requests
from typing import Optional
from pathlib import Path
from .base import LLMProvider
from ..core.exceptions import ProcessingError

logger = logging.getLogger(__name__)

_RETRYABLE_STATUS_CODES = {429, 500, 502, 503, 504}

API_BASE_URLS = {
    'community': 'https://go.apis.huit.harvard.edu/ais-openai-direct-limited-schools/v1',
    'paid': 'https://go.apis.huit.harvard.edu/ais-openai-direct/v1',
}

# Models that require max_completion_tokens instead of max_tokens
_MAX_COMPLETION_TOKENS_MODELS = {'o1', 'o3', 'o4', 'gpt-5', 'gpt-4.5'}


def _needs_max_completion_tokens(model_name: str) -> bool:
    lower = model_name.lower()
    return any(lower.startswith(p) for p in _MAX_COMPLETION_TOKENS_MODELS)


class OpenAIProvider(LLMProvider):
    """OpenAI LLM provider using Harvard API gateway with vision support."""

    def __init__(self, model_name: str, api_key: Optional[str] = None,
                 temperature: float = 0.0, max_tokens: int = 1024, timeout: int = 30,
                 seed: Optional[int] = None,
                 max_retries: int = 3, retry_base_delay: float = 5.0):
        super().__init__(model_name)
        self.api_key = api_key or os.getenv('HARVARD_API_KEY')
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.timeout = timeout
        self.seed = seed
        self.max_retries = max_retries
        self.retry_base_delay = retry_base_delay

        tier = os.getenv('HARVARD_OPENAI_TIER', 'community').lower()
        self.base_url = API_BASE_URLS.get(tier, API_BASE_URLS['community'])

    def query(self, prompt: str, system_prompt: str = None,
              image_path: Optional[str] = None, image_paths: Optional[list] = None):
        if not self.validate_prompt(prompt):
            raise ProcessingError("Invalid prompt provided")

        if not self.api_key:
            raise ProcessingError("Harvard API key not configured")

        try:
            images_to_process = []
            if image_paths:
                images_to_process = [img for img in image_paths if Path(img).exists()]
            elif image_path and Path(image_path).exists():
                images_to_process = [image_path]

            payload = self._build_payload(prompt, system_prompt, images_to_process)
            url = f"{self.base_url}/chat/completions"

            headers = {
                'Content-Type': 'application/json',
                'api-key': self.api_key,
            }

            last_error = None
            for attempt in range(1, self.max_retries + 1):
                try:
                    response = requests.post(
                        url,
                        headers=headers,
                        json=payload,
                        timeout=self.timeout,
                    )

                    if response.status_code == 200:
                        result = response.json()
                        response_text = self._extract_response_text(result)
                        token_metadata = self._extract_token_usage(result)

                        if not response_text or len(response_text.strip()) == 0:
                            reasoning_tokens = token_metadata.get('reasoning_tokens', 0)
                            if reasoning_tokens > 0:
                                raise ProcessingError(
                                    f"Model {self.model_name} consumed all {self.max_tokens} tokens for reasoning, "
                                    f"leaving no tokens for output. Increase MAX_TOKENS for reasoning models."
                                )

                        return response_text, token_metadata

                    if response.status_code in _RETRYABLE_STATUS_CODES:
                        try:
                            error_data = response.json()
                            detail = error_data.get('error', {}).get('message', str(error_data))
                        except Exception:
                            detail = response.text
                        last_error = f"API request failed with status {response.status_code}: {detail}"
                        if attempt < self.max_retries:
                            delay = self.retry_base_delay * (2 ** (attempt - 1))
                            logger.warning("Attempt %d/%d failed (%d), retrying in %.0fs…",
                                           attempt, self.max_retries, response.status_code, delay)
                            time.sleep(delay)
                            continue

                    error_msg = f"API request failed with status {response.status_code}"
                    try:
                        error_data = response.json()
                        error_msg += f": {error_data.get('error', {}).get('message', error_data)}"
                    except Exception:
                        error_msg += f": {response.text}"
                    raise ProcessingError(error_msg)

                except requests.exceptions.Timeout:
                    last_error = f"Request timed out after {self.timeout} seconds"
                    if attempt < self.max_retries:
                        delay = self.retry_base_delay * (2 ** (attempt - 1))
                        logger.warning("Attempt %d/%d timed out, retrying in %.0fs…",
                                       attempt, self.max_retries, delay)
                        time.sleep(delay)
                        continue

                except requests.exceptions.RequestException as e:
                    last_error = f"Harvard OpenAI API error: {str(e)}"
                    if attempt < self.max_retries:
                        delay = self.retry_base_delay * (2 ** (attempt - 1))
                        logger.warning("Attempt %d/%d network error, retrying in %.0fs…",
                                       attempt, self.max_retries, delay)
                        time.sleep(delay)
                        continue

            raise ProcessingError(f"Failed after {self.max_retries} attempts: {last_error}")

        except ProcessingError:
            raise
        except Exception as e:
            raise ProcessingError(f"OpenAI API error: {str(e)}")

    def _build_payload(self, prompt: str, system_prompt: Optional[str],
                       images: list) -> dict:
        messages = []

        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})

        if images:
            content = [{"type": "text", "text": prompt}]
            for img_path in images:
                img_ext = Path(img_path).suffix.lower()
                if img_ext in ['.jpg', '.jpeg']:
                    img_type = 'image/jpeg'
                elif img_ext == '.png':
                    img_type = 'image/png'
                elif img_ext == '.gif':
                    img_type = 'image/gif'
                elif img_ext == '.webp':
                    img_type = 'image/webp'
                else:
                    img_type = 'image/png'

                content.append({
                    "type": "image_url",
                    "image_url": {
                        "url": f"data:{img_type};base64,{self._encode_image(img_path)}"
                    }
                })
            messages.append({"role": "user", "content": content})
        else:
            messages.append({"role": "user", "content": prompt})

        payload = {
            "model": self.model_name,
            "messages": messages,
        }

        # Newer models (o1, o3, o4, gpt-5, gpt-4.5) require max_completion_tokens
        if _needs_max_completion_tokens(self.model_name):
            payload['max_completion_tokens'] = self.max_tokens
        else:
            payload['max_tokens'] = self.max_tokens

        # o1/o3/o4 reasoning models only accept default temperature
        if not any(p in self.model_name.lower() for p in ['o1', 'o3', 'o4']):
            payload['temperature'] = self.temperature

        if self.seed is not None:
            payload['seed'] = self.seed

        return payload

    def _extract_response_text(self, response: dict) -> str:
        try:
            choices = response.get('choices', [])
            if choices:
                return choices[0].get('message', {}).get('content', '').strip()
            raise ProcessingError(f"No choices in response: {response}")
        except ProcessingError:
            raise
        except Exception as e:
            raise ProcessingError(f"Error parsing response: {str(e)}")

    def _extract_token_usage(self, response: dict) -> dict:
        token_metadata = {
            'input_tokens': 0,
            'output_tokens': 0,
            'reasoning_tokens': 0,
        }

        usage = response.get('usage', {})
        if isinstance(usage, dict):
            token_metadata['input_tokens'] = usage.get('prompt_tokens', 0)
            token_metadata['output_tokens'] = usage.get('completion_tokens', 0)

            completion_details = usage.get('completion_tokens_details', {})
            if isinstance(completion_details, dict):
                token_metadata['reasoning_tokens'] = completion_details.get('reasoning_tokens', 0)

        return token_metadata

    def _encode_image(self, image_path: str) -> str:
        import base64
        with open(image_path, "rb") as image_file:
            return base64.b64encode(image_file.read()).decode('utf-8')

    def get_model_name(self) -> str:
        return f"openai/{self.model_name}"

    def is_available(self) -> bool:
        return bool(self.api_key)

    def get_provider_info(self) -> dict:
        info = super().get_provider_info()
        info.update({
            'provider_type': 'openai_harvard',
            'base_url': self.base_url,
            'temperature': self.temperature,
            'max_tokens': self.max_tokens,
            'timeout': self.timeout,
            'has_api_key': bool(self.api_key),
        })
        return info

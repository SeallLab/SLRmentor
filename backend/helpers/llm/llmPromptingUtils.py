from typing import Type
from pydantic import BaseModel, ValidationError
from openai import OpenAI
from google import genai
from helpers.llm.llmReturnFormat import Response, ResponseCriteria, ResponseMentor
import json


def _safe_json_loads(raw: str, provider_name: str) -> dict:
    if raw is None:
        raise ValueError(f"{provider_name} returned None instead of JSON")

    if not str(raw).strip():
        raise ValueError(f"{provider_name} returned an empty response")

    try:
        return json.loads(raw)
    except json.JSONDecodeError as e:
        preview = str(raw)[:1000]
        raise ValueError(
            f"{provider_name} returned invalid JSON. "
            f"Raw response preview: {repr(preview)}"
        ) from e


def _validate_response(data: dict, schema: Type[BaseModel], provider_name: str) -> dict:
    try:
        validated = schema(**data)
        return validated.model_dump()
    except ValidationError as e:
        raise ValueError(
            f"{provider_name} returned JSON, but it did not match the expected schema. "
            f"Validation error: {e}. "
            f"JSON received: {data}"
        ) from e


def call_gemini_with_schema(
    api_key: str,
    prompt: str,
    schema: Type[BaseModel],
    model: str = "gemini-2.0-flash",
) -> dict:
    client = genai.Client(api_key=api_key)

    response = client.models.generate_content(
        model=model,
        contents=prompt,
        config={
            "response_mime_type": "application/json",
            "response_schema": schema,
        },
    )

    raw = response.text
    print(f"RAW GEMINI RESPONSE ({schema.__name__}):", repr(raw))

    data = _safe_json_loads(raw, "Gemini")
    return _validate_response(data, schema, "Gemini")


def call_chatgpt_with_schema(
    api_key: str,
    prompt: str,
    schema: Type[BaseModel],
    model: str = "gpt-4o-mini",
) -> dict:
    client = OpenAI(api_key=api_key)

    try:
        completion = client.beta.chat.completions.parse(
            model=model,
            messages=[
                {
                    "role": "system",
                    "content": (
                        "Return only the structured response requested by the schema. "
                        "Do not include markdown, comments, explanations outside the JSON, "
                        "or code fences. Use the field name has_changed, not has_chaged."
                    ),
                },
                {"role": "user", "content": prompt},
            ],
            response_format=schema,
            temperature=0.2,
        )

        parsed = completion.choices[0].message.parsed

        if parsed is None:
            raw = completion.choices[0].message.content
            print(f"RAW GPT RESPONSE ({schema.__name__}):", repr(raw))
            data = _safe_json_loads(raw, "ChatGPT")
            return _validate_response(data, schema, "ChatGPT")

        return parsed.model_dump()

    except Exception as e:
        print(f"ChatGPT structured call failed ({schema.__name__}): {e}")
        raise


def call_ai_with_fallback(
    gemini_key: str,
    gpt_key: str,
    prompt: str,
    schema: Type[BaseModel],
) -> tuple[dict, str]:
    gemini_error = None

    try:
        response = call_gemini_with_schema(gemini_key, prompt, schema)
        return response, "Gemini"
    except Exception as e:
        gemini_error = e
        print(f"Gemini call failed, falling back to ChatGPT: {e}")

    try:
        response = call_chatgpt_with_schema(gpt_key, prompt, schema)
        return response, "ChatGPT"
    except Exception as chatgpt_error:
        print(f"ChatGPT fallback also failed: {chatgpt_error}")
        raise RuntimeError(
            f"Both AI providers failed. "
            f"Gemini error: {gemini_error}. "
            f"ChatGPT error: {chatgpt_error}"
        ) from chatgpt_error


# Backward-compatible route-specific function names

def call_gemini(api_key: str, prompt: str) -> dict:
    return call_gemini_with_schema(api_key, prompt, Response)


def call_gemini_mentor(api_key: str, prompt: str) -> dict:
    return call_gemini_with_schema(api_key, prompt, ResponseMentor)


def call_gemini_criteria(api_key: str, prompt: str) -> dict:
    return call_gemini_with_schema(api_key, prompt, ResponseCriteria)


def call_chatgpt(api_key: str, prompt: str) -> dict:
    return call_chatgpt_with_schema(api_key, prompt, Response)


def call_chatgpt_criteria(api_key: str, prompt: str) -> dict:
    return call_chatgpt_with_schema(api_key, prompt, ResponseCriteria)


def call_chatgpt_mentor(api_key: str, prompt: str) -> dict:
    return call_chatgpt_with_schema(api_key, prompt, ResponseMentor)
import os
from dataclasses import dataclass


@dataclass
class Config:
    NOTION_TOKEN: str = os.getenv("NOTION_TOKEN", "")
    NOTION_DATABASE_ID: str = os.getenv("NOTION_DATABASE_ID", "")
    HF_BASE_URL: str = "https://huggingface.co"
    HF_API_URL: str = "https://huggingface.co/api/models"
    ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")
    UPDATE_TIME: str = "09:00"
    MODEL_LIMIT: int = 10

    @classmethod
    def validate(cls):
        if not cls.NOTION_TOKEN or not cls.NOTION_DATABASE_ID:
            raise ValueError(
                "NOTION_TOKEN と NOTION_DATABASE_ID の環境変数を設定してください"
            )

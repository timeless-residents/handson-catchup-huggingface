from dataclasses import dataclass
from typing import List, Union, Optional
from datetime import datetime

@dataclass
class ModelCommit:
    title: str
    date: datetime
    description: Optional[str] = None

@dataclass
class ModelStats:
    downloads: int
    likes: int
    recent_downloads: Optional[str] = None

@dataclass
class TrendReason:
    type: str
    description: str

@dataclass
class HuggingFaceModel:
    id: str
    author: str
    description: Optional[str]
    tags: List[str]
    last_modified: Union[str, datetime]  
    stats: ModelStats
    recent_commits: List[ModelCommit]
    trend_reasons: List[TrendReason]
    private: bool = False

    @classmethod
    def from_api_response(cls, data: dict, trend_data: dict = None):
        stats = ModelStats(
            downloads=data.get('downloads', 0),
            likes=data.get('likes', 0),
            recent_downloads=trend_data.get('recent_downloads') if trend_data else None
        )

        return cls(
            id=data.get('id', ''),
            author=data.get('author', 'Unknown'),
            description=data.get('description'),
            tags=data.get('tags', []),
            last_modified=data.get('lastModified', ''),
            stats=stats,
            recent_commits=[],  # 後で更新
            trend_reasons=[],   # 後で更新
            private=data.get('private', False)
        )
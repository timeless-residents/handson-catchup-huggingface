from datetime import datetime
from typing import List, Optional
import requests
from models.huggingface import HuggingFaceModel, ModelCommit, TrendReason
from config import Config


class HuggingFaceService:
    def __init__(self):
        self.headers = {
            "Accept": "application/json",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        }

    def get_model_details(self, model_id: str) -> Optional[dict]:
        """モデルの詳細情報を取得"""
        url = f"{Config.HF_API_URL}/{model_id}"
        response = requests.get(url, headers=self.headers, timeout=30)
        return response.json() if response.status_code == 200 else None

    def get_model_commits(self, model_id: str, limit: int = 3) -> List[ModelCommit]:
        """モデルの最近のコミット履歴を取得"""
        url = f"{Config.HF_BASE_URL}/api/models/{model_id}/commits"
        response = requests.get(url, headers=self.headers, timeout=30)
        if response.status_code != 200:
            return []

        commits = []
        for commit in response.json()[:limit]:
            commits.append(
                ModelCommit(
                    title=commit.get("title", ""),
                    date=datetime.fromisoformat(
                        commit.get("date", "").replace("Z", "+00:00")
                    ),
                    description=commit.get("description"),
                )
            )
        return commits

    def analyze_trend_reasons(self, model: HuggingFaceModel) -> List[TrendReason]:
        """トレンドの理由を分析"""
        reasons = []

        # 最近のコミットがあれば理由として追加
        if model.recent_commits:
            latest_commit = model.recent_commits[0]
            reasons.append(
                TrendReason(
                    type="update",
                    description=f"🔄 Recent update: {latest_commit.title}",
                )
            )

        # 最近のダウンロード増加
        if model.stats.recent_downloads:
            reasons.append(
                TrendReason(
                    type="downloads", description=f"📈 {model.stats.recent_downloads}"
                )
            )

        return reasons

    def get_popular_models(self, limit: int = 10) -> List[HuggingFaceModel]:
        """人気のモデルを取得"""
        params = {
            "sort": "downloads",
            "direction": -1,
            "limit": str(limit),
            "full": "true",
        }

        response = requests.get(Config.HF_API_URL, params=params, headers=self.headers, timeout=30)
        if response.status_code != 200:
            return []

        models = []
        for data in response.json():
            model = HuggingFaceModel.from_api_response(data)
            model.recent_commits = self.get_model_commits(model.id)
            models.append(model)

        return models

    def enrich_model_data(
        self, model: HuggingFaceModel, trend_data: Optional[dict] = None
    ) -> HuggingFaceModel:
        """モデル情報を充実させる"""
        # コミット履歴の取得
        model.recent_commits = self.get_model_commits(model.id)

        # トレンド理由を分析
        trend_reasons = []

        # スクレイピングデータからの追加情報
        if trend_data:
            if trend_data.get("recent_downloads"):
                trend_reasons.append(
                    TrendReason(
                        type="downloads",
                        description=f"📈 Recent Activity: {trend_data['recent_downloads']}",
                    )
                )

            if trend_data.get("card_description"):
                trend_reasons.append(
                    TrendReason(
                        type="description",
                        description=f"📝 Latest Update: {trend_data['card_description'][:200]}...",
                    )
                )

        # 最近のコミットに基づくトレンド理由
        if model.recent_commits:
            latest_commit = model.recent_commits[0]
            trend_reasons.append(
                TrendReason(
                    type="update",
                    description=f"🔄 Recent Update: {latest_commit.title} ({latest_commit.date.strftime('%Y-%m-%d')})",
                )
            )

        # ダウンロード数に基づくトレンド理由
        if model.stats.downloads > 1000000:
            trend_reasons.append(
                TrendReason(
                    type="popularity",
                    description=f"🌟 Popular: {model.stats.downloads:,} total downloads",
                )
            )

        model.trend_reasons = trend_reasons
        return model

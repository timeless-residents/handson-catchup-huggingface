from typing import Dict, List, Optional

import requests
from bs4 import BeautifulSoup

from config import Config


class HuggingFaceScraper:
    def __init__(self):
        self.headers = {
            "Accept": "application/json",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        }

    def get_trending_models_data(self) -> List[Dict]:
        """トレンドページからモデル情報を取得"""
        print("トレンドモデルのスクレイピングを開始...")

        try:
            response = requests.get(
                f"{Config.HF_BASE_URL}/models?sort=trending",
                headers=self.headers,
                timeout=30,
            )

            if response.status_code != 200:
                print(f"ページの取得に失敗: {response.status_code}")
                return []

            soup = BeautifulSoup(response.text, "html.parser")
            model_cards = soup.find_all("article", class_="overview-card-wrapper")
            trend_data = []

            for card in model_cards[: Config.MODEL_LIMIT]:
                try:
                    data = self._extract_card_data(card)
                    if data:
                        trend_data.append(data)
                except Exception as e:
                    print(f"カードの解析中にエラー: {str(e)}")
                    continue

            print(f"{len(trend_data)}件のトレンドモデルを取得しました")
            return trend_data

        except Exception as e:
            print(f"スクレイピング中にエラー: {str(e)}")
            return []

    def _extract_card_data(self, card) -> Optional[Dict]:
        """モデルカードから情報を抽出"""
        model_link = card.find("a", href=True)
        if not model_link:
            return None

        model_id = model_link["href"].strip("/")

        # トレンド関連の情報を抽出
        downloads_span = card.find(
            "span", string=lambda text: text and "downloads" in text.lower()
        )
        description = card.find("div", class_=lambda x: x and "description" in x)

        return {
            "model_id": model_id,
            "recent_downloads": downloads_span.text.strip() if downloads_span else None,
            "card_description": description.text.strip() if description else None,
        }

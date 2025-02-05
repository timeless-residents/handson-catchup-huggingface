import time

import schedule

from config import Config
from models.huggingface import HuggingFaceModel
from services.huggingface import HuggingFaceService
from services.notion import NotionService
from services.scraper import HuggingFaceScraper


class ModelTracker:
    def __init__(self):
        self.hf_service = HuggingFaceService()
        self.notion_service = NotionService()
        self.scraper = HuggingFaceScraper()

    def run_update(self):
        """トレンド情報の更新を実行"""
        try:
            print("\n=== 日次アップデート開始 ===")

            # トレンドモデルの取得
            trend_data = self.scraper.get_trending_models_data()
            trending_models = []

            for data in trend_data:
                model_details = self.hf_service.get_model_details(data["model_id"])
                if model_details:
                    model = HuggingFaceModel.from_api_response(model_details, data)
                    model = self.hf_service.enrich_model_data(model)
                    trending_models.append(model)

            # 人気モデルの取得
            popular_models = self.hf_service.get_popular_models()

            if trending_models and popular_models:
                self.notion_service.create_page(popular_models, trending_models)
                print("アップデート完了")
            else:
                print("モデルの取得に失敗しました")

            print("=== 日次アップデート終了 ===\n")

        except Exception as e:
            print(f"エラーが発生しました: {str(e)}")


def main():
    # 設定の検証
    Config.validate()

    tracker = ModelTracker()

    # 初回実行
    print("初回実行を開始します...")
    tracker.run_update()

    # スケジューラーの設定
    print(f"スケジューラーを開始します（毎日 {Config.UPDATE_TIME} に実行）")
    schedule.every().day.at(Config.UPDATE_TIME).do(tracker.run_update)

    try:
        while True:
            schedule.run_pending()
            time.sleep(60)
    except KeyboardInterrupt:
        print("\nプログラムを終了します")


if __name__ == "__main__":
    main()

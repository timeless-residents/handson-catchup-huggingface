import argparse
import logging
from pathlib import Path

from config import Config
from models.huggingface import HuggingFaceModel
from services.huggingface import HuggingFaceService
from services.notion import NotionService
from services.scraper import HuggingFaceScraper

# ロギングの設定
log_dir = Path.home() / "Library" / "Logs" / "handson-catchup-huggingface"
log_dir.mkdir(parents=True, exist_ok=True)
log_file = log_dir / "application.log"

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.FileHandler(log_file), logging.StreamHandler()],
)

logger = logging.getLogger(__name__)


class ModelTracker:
    def __init__(self):
        self.hf_service = HuggingFaceService()
        self.notion_service = NotionService()
        self.scraper = HuggingFaceScraper()

    def run_update(self):
        """トレンド情報の更新を実行"""
        try:
            logger.info("=== 日次アップデート開始 ===")

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
                logger.info("アップデート完了")
            else:
                logger.error("モデルの取得に失敗しました")

            logger.info("=== 日次アップデート終了 ===")

        except Exception as e:
            logger.error("エラーが発生しました: %s", str(e), exc_info=True)
            raise


def main():
    parser = argparse.ArgumentParser(description="AI Model Trend Tracker")
    parser.add_argument("--check", action="store_true", help="設定の検証のみを実行")
    args = parser.parse_args()

    try:
        # 設定の検証
        Config.validate()
        if args.check:
            logger.info("設定の検証が完了しました")
            return

        # 更新の実行
        tracker = ModelTracker()
        tracker.run_update()

    except Exception as e:
        logger.error("致命的なエラーが発生しました: %s", str(e), exc_info=True)
        raise


if __name__ == "__main__":
    main()

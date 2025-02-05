from datetime import datetime
from typing import List
import json
from anthropic import Anthropic
from notion_client import Client
from config import Config
from models.huggingface import HuggingFaceModel


class NotionService:
    def __init__(self):
        self.client = Client(auth=Config.NOTION_TOKEN)
        self.database_id = Config.NOTION_DATABASE_ID
        self.anthropic = Anthropic(api_key=Config.ANTHROPIC_API_KEY)

    def prepare_model_data(self, model: HuggingFaceModel) -> dict:
        """モデル情報を構造化データに変換"""
        # last_modified の処理
        last_modified = (
            model.last_modified.isoformat()
            if isinstance(model.last_modified, datetime)
            else model.last_modified
        )

        # trend_reasons を文字列のリストに変換
        trend_reasons = (
            [reason.description for reason in model.trend_reasons]
            if model.trend_reasons
            else []
        )

        # recent_commits を整形
        commits = (
            [
                {
                    "title": commit.title,
                    "date": commit.date.isoformat(),
                    "description": commit.description,
                }
                for commit in model.recent_commits
            ]
            if model.recent_commits
            else []
        )

        return {
            "id": model.id,
            "name": model.id.split("/")[-1],
            "author": model.author,
            "description": model.description,
            "downloads": model.stats.downloads,
            "likes": model.stats.likes,
            "recent_downloads": model.stats.recent_downloads,
            "tags": model.tags,
            "last_modified": last_modified,
            "trend_reasons": trend_reasons,
            "recent_commits": commits,
            "private": model.private,
        }

    def generate_news_script(
        self,
        trending_models: List[HuggingFaceModel],
        popular_models: List[HuggingFaceModel],
    ) -> str:
        """Claude APIを使用してニュース原稿を生成"""

        def model_to_dict(model: HuggingFaceModel) -> dict:
            """モデルをJSON変換可能な辞書形式に変換"""
            return {
                "id": model.id,
                "name": model.id.split("/")[-1],
                "author": model.author,
                "description": model.description,
                "downloads": model.stats.downloads,
                "likes": model.stats.likes,
                "recent_downloads": model.stats.recent_downloads,
                "tags": model.tags,
                "last_modified": (
                    model.last_modified.isoformat()
                    if isinstance(model.last_modified, datetime)
                    else model.last_modified
                ),
                "trend_reasons": (
                    [
                        {"type": tr.type, "description": str(tr.description)}
                        for tr in model.trend_reasons
                    ]
                    if model.trend_reasons
                    else []
                ),
                "recent_commits": (
                    [
                        {
                            "title": str(commit.title),
                            "date": (
                                commit.date.isoformat()
                                if isinstance(commit.date, datetime)
                                else str(commit.date)
                            ),
                            "description": (
                                str(commit.description) if commit.description else None
                            ),
                        }
                        for commit in model.recent_commits
                    ]
                    if model.recent_commits
                    else []
                ),
            }

        try:
            # モデルデータの構造化
            data = {
                "trending_models": [model_to_dict(m) for m in trending_models],
                "popular_models": [model_to_dict(m) for m in popular_models],
                "date": datetime.now().strftime("%Y-%m-%d"),
            }

            # プロンプトの作成
            prompt = f"""以下のデータを基に、AIニュースキャスターが読み上げることを想定したトレンド分析のニュース原稿を作成してください。
    データは、Hugging Faceの最新のモデルトレンドと累計人気モデルの情報です。

    # データ
    ```json
    {json.dumps(data, ensure_ascii=False, indent=2)}
    ```

    以下の点を意識して原稿を作成してください：
    1. トレンドの分析（複数のモデルを展開している企業の動向、注目分野での進展など）
    2. 数値の効果的な活用（ダウンロード数などの具体的な数字を適切に含める）
    3. 分野別の動向（音声、画像、3D生成など）
    4. 長期的な視点でのモデル採用状況
    5. 業界全体のトレンドの示唆
    6. 各モデルのトレンド理由や最近のアップデート情報も含める

    なお、原稿は聞き手が理解しやすい、自然な話し言葉で作成してください。"""

            # Claude APIを使用して生成
            message = self.anthropic.messages.create(
                model="claude-3-sonnet-20240229",
                max_tokens=1500,
                temperature=0.7,
                messages=[{"role": "user", "content": prompt}],
            )

            # TextBlockからテキストを抽出
            if message and hasattr(message.content, "text"):
                return message.content.text
            elif message and hasattr(message.content, "__iter__"):
                # TextBlockのリストの場合、最初のブロックのテキストを取得
                for block in message.content:
                    if hasattr(block, "text"):
                        return block.text

            # デフォルトの応答
            return "ニュース原稿の生成に失敗しました。"

        except Exception as e:
            print(f"ニュース原稿生成でエラー発生: {str(e)}")
            return "申し訳ありません。ニュース原稿の生成中にエラーが発生しました。"

    def create_model_blocks(
        self, model: HuggingFaceModel, idx: int, is_trending: bool = False
    ) -> List[dict]:
        """モデル情報のブロックを作成"""
        blocks = []

        # モデル名をh3ヘッダーとして追加
        blocks.append(
            {
                "object": "block",
                "type": "heading_3",
                "heading_3": {
                    "rich_text": [
                        {"type": "text", "text": {"content": f"{idx}. {model.id}"}}
                    ]
                },
            }
        )

        # モデルの説明を追加
        if model.description:
            blocks.append(
                {
                    "object": "block",
                    "type": "paragraph",
                    "paragraph": {
                        "rich_text": [
                            {
                                "type": "text",
                                "text": {"content": f"{model.description[:500]}..."},
                            }
                        ]
                    },
                }
            )

        # トレンド理由を追加（is_trendingがTrueの場合のみ）
        if is_trending and model.trend_reasons:
            blocks.append(
                {
                    "object": "block",
                    "type": "callout",
                    "callout": {
                        "rich_text": [
                            {
                                "type": "text",
                                "text": {
                                    "content": "\n".join(
                                        reason.description
                                        for reason in model.trend_reasons
                                    )
                                },
                            }
                        ],
                        "icon": {"emoji": "🔥"},
                    },
                }
            )

        # モデル情報を表示
        stats_text = (
            f"👤 Author: {model.author}\n"
            f"⭐ Likes: {model.stats.likes:,}\n"
            f"📥 Downloads: {model.stats.downloads:,}\n"
        )

        if model.stats.recent_downloads:
            stats_text += f"📈 Recent Downloads: {model.stats.recent_downloads}\n"

        stats_text += (
            f"🏷 Tags: {', '.join(model.tags[:5])}\n"
            f"📝 Last Modified: {model.last_modified}"
        )

        blocks.append(
            {
                "object": "block",
                "type": "paragraph",
                "paragraph": {
                    "rich_text": [{"type": "text", "text": {"content": stats_text}}]
                },
            }
        )

        # 最近のコミットを追加（存在する場合）
        if model.recent_commits:
            blocks.append(
                {
                    "object": "block",
                    "type": "heading_3",
                    "heading_3": {
                        "rich_text": [
                            {"type": "text", "text": {"content": "Recent Updates"}}
                        ]
                    },
                }
            )

            for commit in model.recent_commits[:3]:  # 最新3件のみ表示
                commit_text = (
                    f"📅 {commit.date.strftime('%Y-%m-%d %H:%M')}\n"
                    f"🔄 {commit.title}"
                )
                if commit.description:
                    commit_text += f"\n📝 {commit.description}"

                blocks.append(
                    {
                        "object": "block",
                        "type": "callout",
                        "callout": {
                            "rich_text": [
                                {"type": "text", "text": {"content": commit_text}}
                            ],
                            "icon": {"emoji": "📌"},
                        },
                    }
                )

        # URLをクリック可能なリンクとして追加
        blocks.append(
            {
                "object": "block",
                "type": "paragraph",
                "paragraph": {
                    "rich_text": [
                        {
                            "type": "text",
                            "text": {
                                "content": "🔗 View on Hugging Face",
                                "link": {"url": f"https://huggingface.co/{model.id}"},
                            },
                        }
                    ]
                },
            }
        )

        # セパレータを追加
        blocks.append({"object": "block", "type": "divider", "divider": {}})

        return blocks

    def create_page(
        self,
        popular_models: List[HuggingFaceModel],
        trending_models: List[HuggingFaceModel],
    ):
        """Notionページを作成"""
        today = datetime.now().strftime("%Y-%m-%d")
        print(f"Notionページ作成開始: {today}")

        try:
            # ニュース原稿を生成
            news_script = self.generate_news_script(trending_models, popular_models)

            page_properties = {
                "title": {
                    "title": [{"text": {"content": f"HF Models Report - {today}"}}]
                },
                "Date": {"date": {"start": today}},
                "Tags": {"multi_select": [{"name": "キャッチアップ"}]},
            }

            content_blocks = []

            # ニュースキャスター原稿セクション
            content_blocks.extend(
                [
                    {
                        "object": "block",
                        "type": "heading_1",
                        "heading_1": {
                            "rich_text": [
                                {
                                    "type": "text",
                                    "text": {"content": "📰 AIニュースキャスター原稿"},
                                }
                            ]
                        },
                    },
                    {
                        "object": "block",
                        "type": "callout",
                        "callout": {
                            "rich_text": [
                                {"type": "text", "text": {"content": news_script}}
                            ],
                            "icon": {"emoji": "🎤"},
                        },
                    },
                    {"object": "block", "type": "divider", "divider": {}},
                ]
            )

            # トレンドモデルセクション
            content_blocks.extend(
                [
                    {
                        "object": "block",
                        "type": "heading_1",
                        "heading_1": {
                            "rich_text": [
                                {
                                    "type": "text",
                                    "text": {"content": "🔥 Real-Time Trending Models"},
                                }
                            ]
                        },
                    },
                    {
                        "object": "block",
                        "type": "paragraph",
                        "paragraph": {
                            "rich_text": [
                                {
                                    "type": "text",
                                    "text": {
                                        "content": "現在注目を集めているモデル\n\n"
                                    },
                                }
                            ]
                        },
                    },
                ]
            )

            # トレンドモデルの情報を追加
            for idx, model in enumerate(trending_models, 1):
                content_blocks.extend(
                    self.create_model_blocks(model, idx, is_trending=True)
                )

            # セパレータ
            content_blocks.append({"object": "block", "type": "divider", "divider": {}})

            # 人気モデルセクション
            content_blocks.extend(
                [
                    {
                        "object": "block",
                        "type": "heading_1",
                        "heading_1": {
                            "rich_text": [
                                {
                                    "type": "text",
                                    "text": {"content": "🌟 Most Downloaded Models"},
                                }
                            ]
                        },
                    },
                    {
                        "object": "block",
                        "type": "paragraph",
                        "paragraph": {
                            "rich_text": [
                                {
                                    "type": "text",
                                    "text": {
                                        "content": "累計ダウンロード数の多いモデル\n\n"
                                    },
                                }
                            ]
                        },
                    },
                ]
            )

            # 人気モデルの情報を追加
            for idx, model in enumerate(popular_models, 1):
                content_blocks.extend(self.create_model_blocks(model, idx))

            page = self.client.pages.create(
                parent={"database_id": self.database_id},
                properties=page_properties,
                children=content_blocks,
            )

            page_id = page["id"]
            page_url = f"https://notion.so/{page_id.replace('-', '')}"
            print(f"Notionページを作成しました: {page_url}")
            return page

        except Exception as e:
            print(f"ページ作成でエラー発生: {str(e)}")
            raise

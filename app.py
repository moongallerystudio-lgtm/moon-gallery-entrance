from __future__ import annotations

import os
import json
from datetime import datetime
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from flask import Flask, jsonify, render_template, request


app = Flask(__name__)


def load_env_file() -> None:
    env_path = os.path.join(os.path.dirname(__file__), ".env")
    if not os.path.exists(env_path):
        return

    with open(env_path, "r", encoding="utf-8") as env_file:
        for raw_line in env_file:
            line = raw_line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue

            key, value = line.split("=", 1)
            key = key.strip()
            value = value.strip().strip('"').strip("'")
            os.environ.setdefault(key, value)


load_env_file()


GALLERY_PROFILE = {
    "name": "Moon Gallery & Studio",
    "company": "合同会社新月芸術",
    "opening_hours": "展览期间通常 13:00 - 19:00，具体以当期展览公告为准",
    "closed": "非展览期间和布展期间请提前联系确认",
    "address": "東京都台東区北上野2丁目3-13 上野ダイカンプラザ102",
    "phone": "080-6098-6862",
    "email": "moon.gallery.studio@gmail.com",
    "website": "https://www.moon-gallery-studio.com/",
    "instagram": "moon.gallerystudio",
    "wechat": "abyotine",
    "xiaohongshu": "月画廊 (Moon Gallery)",
    "mission": "Moon Gallery & Studio 为来自不同国家的艺术家提供展览、交流和实验性艺术项目的平台。",
    "services": "个展、群展、作品销售、艺术活动、版画工房、3D 打印、艺术工作坊与艺术课程。",
    "staff_call": "请稍候，我已经提示工作人员前来协助。",
}


FAQS = [
    {
        "id": "hours",
        "keywords": ["营业", "时间", "几点", "open", "hours", "営業時間"],
        "answer": "展览期间通常开放到 19:00，部分活动时间会调整。请以当前展览现场公告或官网活动页为准。",
    },
    {
        "id": "ticket",
        "keywords": ["门票", "票", "预约", "ticket", "reservation", "予約"],
        "answer": "展览参观和活动预约请以官网活动页或现场公告为准。如需确认空位、导览或场地预约，我可以帮你联系工作人员。",
    },
    {
        "id": "photo",
        "keywords": ["拍照", "摄影", "照片", "photo", "camera", "写真"],
        "answer": "大部分区域可以拍照，但请不要使用闪光灯。若作品旁有禁止摄影标识，请以标识为准。",
    },
    {
        "id": "restroom",
        "keywords": ["洗手间", "厕所", "restroom", "toilet", "トイレ"],
        "answer": "洗手间位置请向工作人员确认，我也可以帮你呼叫工作人员。",
    },
    {
        "id": "artist",
        "keywords": ["艺术家", "作者", "artist", "作家"],
        "answer": "Moon Gallery & Studio 支持来自不同国家的年轻艺术家，展出形式包括装置、绘画、行为艺术等。具体艺术家资料请参考现场标签与展览说明。",
    },
    {
        "id": "price",
        "keywords": ["价格", "购买", "收藏", "price", "buy", "購入"],
        "answer": "如果你对作品收藏或购买感兴趣，我可以帮你呼叫工作人员做进一步介绍。",
    },
    {
        "id": "address",
        "keywords": ["地址", "位置", "怎么去", "access", "address", "場所"],
        "answer": "主画廊地址是：東京都台東区北上野2丁目3-13 上野ダイカンプラザ102。",
    },
    {
        "id": "contact",
        "keywords": ["联系", "电话", "邮箱", "contact", "email", "tel"],
        "answer": "你可以通过电话 080-6098-6862 或邮箱 moon.gallery.studio@gmail.com 联系 Moon Gallery & Studio。",
    },
    {
        "id": "studio",
        "keywords": ["工房", "版画", "打印", "3d", "print", "studio"],
        "answer": "Moon Gallery & Studio 也提供版画工房、喷墨/激光打印、3D 打印和艺术工作坊等服务，价格与预约请联系工作人员确认。",
    },
    {
        "id": "school",
        "keywords": ["课程", "学校", "指导", "portfolio", "school", "講座"],
        "answer": "艺术学校方向包括艺术项目、作品指导、作品集指导和艺术相关讲座。需要课程信息的话，我可以帮你联系工作人员。",
    },
]


GREETINGS = [
    "你好",
    "您好",
    "哈喽",
    "hello",
    "hi",
    "嗨",
    "こんにちは",
    "こんばんは",
]

THANKS = ["谢谢", "感谢", "thank", "thanks", "ありがとう"]

GOODBYES = ["再见", "拜拜", "bye", "goodbye", "またね"]

LANGUAGE_LABELS = {
    "zh": "中文",
    "ja": "日本語",
    "en": "English",
}

LOCAL_REPLIES = {
    "empty": {
        "zh": "我在这里。你可以直接问我，也可以点下面的快捷问题。",
        "ja": "こちらにいます。展示、営業時間、アクセスなど、気軽に聞いてください。",
        "en": "I am here. You can ask me about the exhibition, hours, access, or anything you need.",
    },
    "greeting": {
        "zh": "你好呀，欢迎来 Moon Gallery & Studio。你可以先慢慢看，有想问的我就在这里。",
        "ja": "こんにちは。Moon Gallery & Studioへようこそ。どうぞゆっくりご覧ください。気になることがあれば声をかけてくださいね。",
        "en": "Hi, welcome to Moon Gallery & Studio. Take your time looking around, and I am right here if you need me.",
    },
    "thanks": {
        "zh": "不客气。你慢慢看，有需要随时叫我。",
        "ja": "どういたしまして。ごゆっくりご覧ください。必要な時はいつでも声をかけてください。",
        "en": "You are welcome. Please take your time, and call me anytime if you need anything.",
    },
    "goodbye": {
        "zh": "再见，欢迎下次再来 Moon Gallery & Studio。",
        "ja": "ありがとうございました。またMoon Gallery & Studioへお越しください。",
        "en": "Goodbye, and we hope to see you again at Moon Gallery & Studio.",
    },
    "identity": {
        "zh": "我是入口虚拟接待员，可以帮你介绍展览、开放时间、地址、拍照规则、预约方式，也可以帮你联系工作人员。",
        "ja": "私は入口のバーチャル受付です。展示、営業時間、アクセス、撮影ルール、予約についてご案内できます。スタッフへの連絡もできます。",
        "en": "I am the virtual host at the entrance. I can help with exhibitions, opening hours, access, photo rules, reservations, and calling staff.",
    },
    "staff": {
        "zh": GALLERY_PROFILE["staff_call"],
        "ja": "少々お待ちください。スタッフにお声がけします。",
        "en": "Please wait a moment. I will call a staff member for you.",
    },
    "hours": {
        "zh": "展览期间通常开放到 19:00，部分活动时间会调整。请以当前展览现场公告或官网活动页为准。",
        "ja": "展示期間中は通常19:00まで開廊しています。イベントにより時間が変わる場合がありますので、会場案内または公式サイトをご確認ください。",
        "en": "During exhibitions, the gallery is usually open until 19:00. Hours may change for events, so please check the onsite notice or official website.",
    },
    "ticket": {
        "zh": "展览参观和活动预约请以官网活动页或现场公告为准。如需确认空位、导览或场地预约，我可以帮你联系工作人员。",
        "ja": "展示やイベント予約は公式サイトまたは会場案内をご確認ください。空き状況、案内、スペース予約についてはスタッフにおつなぎできます。",
        "en": "Please check the official website or onsite notice for exhibition visits and event reservations. I can also connect you with staff for availability or guided visits.",
    },
    "photo": {
        "zh": "大部分区域可以拍照，但请不要使用闪光灯。若作品旁有禁止摄影标识，请以标识为准。",
        "ja": "多くのエリアで撮影できますが、フラッシュはご遠慮ください。作品横に撮影禁止の表示がある場合は、その案内に従ってください。",
        "en": "Photography is allowed in most areas, but please do not use flash. If a work has a no-photo sign, please follow that notice.",
    },
    "restroom": {
        "zh": "洗手间位置请向工作人员确认，我也可以帮你呼叫工作人员。",
        "ja": "お手洗いの場所はスタッフにご確認ください。必要でしたらスタッフをお呼びします。",
        "en": "Please ask staff for the restroom location. I can call someone to assist you.",
    },
    "artist": {
        "zh": "Moon Gallery & Studio 支持来自不同国家的年轻艺术家，展出形式包括装置、绘画、行为艺术等。具体艺术家资料请参考现场标签与展览说明。",
        "ja": "Moon Gallery & Studioは、さまざまな国の若いアーティストを紹介しています。インスタレーション、絵画、パフォーマンスなどを扱います。詳しい作家情報は会場のキャプションをご覧ください。",
        "en": "Moon Gallery & Studio supports young artists from different countries, with works including installation, painting, and performance. Please check the onsite labels for artist details.",
    },
    "price": {
        "zh": "如果你对作品收藏或购买感兴趣，我可以帮你呼叫工作人员做进一步介绍。",
        "ja": "作品の購入やコレクションにご興味がありましたら、スタッフをお呼びして詳しくご案内します。",
        "en": "If you are interested in collecting or purchasing a work, I can call a staff member to help.",
    },
    "address": {
        "zh": "主画廊地址是：東京都台東区北上野2丁目3-13 上野ダイカンプラザ102。",
        "ja": "住所は、東京都台東区北上野2丁目3-13 上野ダイカンプラザ102です。",
        "en": "The gallery address is Ueno Daikan Plaza 102, 2-3-13 Kita-Ueno, Taito-ku, Tokyo.",
    },
    "contact": {
        "zh": "你可以通过电话 080-6098-6862 或邮箱 moon.gallery.studio@gmail.com 联系 Moon Gallery & Studio。",
        "ja": "電話 080-6098-6862、またはメール moon.gallery.studio@gmail.com でお問い合わせいただけます。",
        "en": "You can contact Moon Gallery & Studio by phone at 080-6098-6862 or by email at moon.gallery.studio@gmail.com.",
    },
    "studio": {
        "zh": "Moon Gallery & Studio 也提供版画工房、喷墨/激光打印、3D 打印和艺术工作坊等服务，价格与预约请联系工作人员确认。",
        "ja": "版画工房、インクジェット・レーザー印刷、3Dプリント、ワークショップなども行っています。料金や予約はスタッフにご確認ください。",
        "en": "Moon Gallery & Studio also offers print studio services, inkjet and laser printing, 3D printing, and workshops. Please ask staff about prices and reservations.",
    },
    "school": {
        "zh": "艺术学校方向包括艺术项目、作品指导、作品集指导和艺术相关讲座。需要课程信息的话，我可以帮你联系工作人员。",
        "ja": "アートスクールでは、アートプロジェクト、作品指導、ポートフォリオ指導、アート関連講座などを行っています。詳しくはスタッフにおつなぎします。",
        "en": "The art school offers art projects, artwork guidance, portfolio support, and art-related lectures. I can connect you with staff for details.",
    },
    "exhibition": {
        "zh": "Moon Gallery & Studio 主要举办个展、群展、艺术家交流、实验影像放映和工作坊。当前展览请以现场公告为准。",
        "ja": "Moon Gallery & Studioでは、個展、グループ展、アーティスト交流、実験映像上映、ワークショップなどを行っています。現在の展示は会場案内をご確認ください。",
        "en": "Moon Gallery & Studio hosts solo and group exhibitions, artist exchanges, experimental screenings, and workshops. Please check the onsite notice for the current exhibition.",
    },
    "about": {
        "zh": "Moon Gallery & Studio 是位于东京台东区北上野的艺术空间，提供展览、交流、工房、工作坊与艺术教育相关服务。",
        "ja": "Moon Gallery & Studioは、東京・台東区北上野にあるアートスペースです。展示、交流、工房、ワークショップ、アート教育を行っています。",
        "en": "Moon Gallery & Studio is an art space in Kita-Ueno, Taito-ku, Tokyo, offering exhibitions, exchange, studio services, workshops, and art education.",
    },
    "fallback": {
        "zh": "嗯，我刚刚有点没接住。你可以再说一遍，或者直接问我展览、开放时间、地址、拍照、预约这些都可以。",
        "ja": "すみません、今のところを少し聞き逃したかもしれません。展示、営業時間、アクセス、撮影、予約など、もう一度聞いてみてください。",
        "en": "Sorry, I may have missed that. You can say it again, or ask me about the exhibition, hours, access, photos, or reservations.",
    },
}

SUGGESTED_TOPICS = [
    "今天的展览介绍",
    "开放时间",
    "画廊地址",
    "可以拍照吗",
    "如何预约导览",
    "版画工房服务",
    "呼叫工作人员",
]

SYSTEM_PROMPT = """
你是 Moon Gallery & Studio 入口处 iPad 上的虚拟接待员。
说话要自然、温和、带一点可爱的亲近感，像现场工作人员，不要像客服模板。
每次回答 1-3 句，避免列表、套话和“请问还有什么可以帮您”。
如果访客只是闲聊或打招呼，就轻松回应一句，不要马上推销画廊信息。
优先回答访客当下的问题；如果只是打招呼，就友好寒暄，不要主动背诵画廊资料。
不知道的信息要诚实说明，并建议查看现场公告或联系工作人员。
不要编造当前展览名称、作品风格、是否常设展、艺术家、活动安排、现场座位、设施或路线；没有明确资料时，用“可以先从入口附近/展签慢慢看起”这类安全建议。
回答语言跟随访客语言，默认使用中文。

画廊资料：
- 名称：Moon Gallery & Studio
- 公司：合同会社新月芸術
- 地址：東京都台東区北上野2丁目3-13 上野ダイカンプラザ102
- 电话：080-6098-6862
- 邮箱：moon.gallery.studio@gmail.com
- Instagram：moon.gallerystudio
- WeChat：abyotine
- 小红书：月画廊 (Moon Gallery)
- 官网：https://www.moon-gallery-studio.com/
- 定位：为来自不同国家的艺术家提供展览、交流和实验性艺术项目的平台。
- 服务：个展、群展、作品销售、艺术活动、版画工房、3D 打印、艺术工作坊与艺术课程。
- 开放时间：展览期间通常 13:00 - 19:00，具体以当期展览公告为准。
- 拍照：大部分区域可以拍照，但不要使用闪光灯；作品旁有禁止摄影标识时以标识为准。
""".strip()


def contains_any(text: str, keywords: list[str]) -> bool:
    return any(keyword.lower() in text for keyword in keywords)


def is_short_social_message(text: str, keywords: list[str]) -> bool:
    compact = text.replace(" ", "")
    return len(compact) <= 18 and contains_any(text, keywords)


def detect_language(message: str) -> str:
    text = message.strip()
    if not text:
        return "zh"
    if any("\u3040" <= char <= "\u30ff" for char in text):
        return "ja"
    latin = sum(char.isascii() and char.isalpha() for char in text)
    cjk = sum("\u4e00" <= char <= "\u9fff" for char in text)
    if latin >= 3 and latin > cjk:
        return "en"
    if contains_any(text.lower(), ["where", "what", "when", "hello", "hi", "ticket", "photo", "artist"]):
        return "en"
    if contains_any(text, ["です", "ます", "どこ", "何時", "営業時間", "場所", "予約", "写真", "展示", "トイレ", "作家", "購入", "講座"]):
        return "ja"
    return "zh"


def local_text(key: str, language: str) -> str:
    return LOCAL_REPLIES[key].get(language) or LOCAL_REPLIES[key]["zh"]


def get_llm_config() -> tuple[str, str, str]:
    deepseek_key = os.environ.get("DEEPSEEK_API_KEY", "").strip()
    if deepseek_key == "your_deepseek_api_key_here":
        deepseek_key = ""
    api_key = (
        os.environ.get("LLM_API_KEY")
        or deepseek_key
        or os.environ.get("OPENAI_API_KEY", "")
    )
    model = os.environ.get("LLM_MODEL") or ("deepseek-chat" if deepseek_key else "")
    base_url = os.environ.get(
        "LLM_BASE_URL",
        "https://api.deepseek.com" if deepseek_key else "https://api.openai.com/v1",
    )
    return api_key.strip(), model.strip(), base_url.rstrip("/")


def call_language_model(message: str, language: str) -> str | None:
    api_key, model, base_url = get_llm_config()
    if not api_key or not model:
        return None

    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {
                "role": "user",
                "content": (
                    f"Visitor language detected: {LANGUAGE_LABELS.get(language, '中文')}.\n"
                    f"Reply only in {LANGUAGE_LABELS.get(language, '中文')} unless the visitor explicitly asks otherwise.\n"
                    f"Visitor message: {message}"
                ),
            },
        ],
        "temperature": 0.7,
        "max_tokens": 220,
    }
    request = Request(
        f"{base_url}/chat/completions",
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        method="POST",
    )

    try:
        with urlopen(request, timeout=15) as response:
            data = json.loads(response.read().decode("utf-8"))
    except HTTPError as error:
        body = error.read().decode("utf-8", errors="replace")[:500]
        app.logger.warning("LLM HTTP error %s from %s: %s", error.code, base_url, body)
        return None
    except (URLError, TimeoutError, json.JSONDecodeError) as error:
        app.logger.warning("LLM request failed for %s: %s", base_url, error)
        return None

    try:
        content = data["choices"][0]["message"]["content"].strip()
    except (KeyError, IndexError, TypeError, AttributeError) as error:
        app.logger.warning("LLM response parse failed: %s", error)
        return None

    return content or None


def build_local_reply(message: str, language: str | None = None) -> str:
    language = language or detect_language(message)
    text = message.strip().lower()
    if not text:
        return local_text("empty", language)

    if is_short_social_message(text, GREETINGS):
        return local_text("greeting", language)

    if is_short_social_message(text, THANKS):
        return local_text("thanks", language)

    if is_short_social_message(text, GOODBYES):
        return local_text("goodbye", language)

    if contains_any(text, ["你是谁", "你能做什么", "怎么用", "who are you", "what can you do"]):
        return local_text("identity", language)

    if contains_any(text, ["呼叫", "工作人员", "staff", "help", "帮助"]):
        return local_text("staff", language)

    for item in FAQS:
        if contains_any(text, item["keywords"]):
            faq_key = item.get("id")
            if faq_key:
                return local_text(faq_key, language)
            return item["answer"]

    if contains_any(text, ["展览", "exhibition", "展示", "当前展", "今天的展"]):
        return local_text("exhibition", language)

    if contains_any(text, ["moon gallery", "moon gallery & studio", "画廊介绍", "介绍一下画廊", "关于画廊", "about gallery"]):
        return local_text("about", language)

    return local_text("fallback", language)


def build_reply(message: str) -> str:
    return build_chat_response(message)["reply"]


def build_chat_response(message: str) -> dict[str, str]:
    text = message.strip()
    language = detect_language(text)
    if not text:
        return {"reply": build_local_reply(message, language), "language": language}

    reply = call_language_model(text, language)
    if reply:
        return {"reply": reply, "language": language}

    return {"reply": build_local_reply(message, language), "language": language}


@app.route("/")
def index():
    return render_template(
        "index.html",
        gallery=GALLERY_PROFILE,
        suggested_topics=SUGGESTED_TOPICS,
        year=datetime.now().year,
    )


@app.post("/api/chat")
def chat():
    payload = request.get_json(silent=True) or {}
    message = str(payload.get("message", ""))
    return jsonify(build_chat_response(message))


@app.route("/manage")
def manage():
    return render_template("manage.html", gallery=GALLERY_PROFILE, faqs=FAQS)


@app.get("/health")
def health():
    api_key, model, _ = get_llm_config()
    return jsonify({
        "ok": True,
        "app": "gallery-entrance",
        "llm": bool(api_key and model),
        "model": model or None,
    })


if __name__ == "__main__":
    port = int(os.environ.get("PORT", "5002"))
    ssl_context = None
    if os.environ.get("HTTPS") == "1":
        cert_path = os.environ.get("SSL_CERT", "certs/localhost.pem")
        key_path = os.environ.get("SSL_KEY", "certs/localhost-key.pem")
        ssl_context = (cert_path, key_path)
    app.run(host="0.0.0.0", port=port, debug=False, ssl_context=ssl_context)

from flask import Flask, request, jsonify, send_file
import os
import io
import json
import re
import base64
import requests
from google.cloud import vision, translate_v2 as translate
import google.generativeai as genai
from flask_cors import CORS

app = Flask(__name__)
CORS(app, origins="*", supports_credentials=True)

# Google API 설정
# GCP 서비스 계정 키를 base64로 환경변수에 저장한 뒤 복원
with open("gcp_key.json", "wb") as f:
    f.write(base64.b64decode(os.environ["GCP_JSON_BASE64"]))
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "gcp_key.json"

# Gemini API 키 설정
genai.configure(api_key=os.environ["GEMINI_API_KEY"])

# OCR 처리 함수
def extract_text_from_image_bytes(image_bytes):
    client = vision.ImageAnnotatorClient()
    image = vision.Image(content=image_bytes)
    response = client.text_detection(image=image)
    return response.text_annotations[0].description if response.text_annotations else ""

# Gemini 요약 요청
def summarize_menu_with_gemini(ocr_text):
    prompt = f"""
다음은 메뉴판에서 OCR로 추출한 텍스트야. 메뉴 이름과 가격만 JSON 형식으로 정리해줘.
[
  {{
    "menu": "Double Cheeseburger",
    "price": "$3.70"
  }},
  ...
]
OCR 텍스트:
{ocr_text}
"""
    model = genai.GenerativeModel("models/gemini-1.5-pro")
    response = model.generate_content(prompt)
    return response.text.strip()

# JSON 문자열 정리
def clean_json_response(text):
    if text.startswith("```json"):
        text = text.replace("```json", "").replace("```", "")
    return text.strip()

# 통화 키워드 감지
CURRENCY_KEYWORDS = {
    "rmb": "CNY", "위안": "CNY", "元": "CNY",
    "엔": "JPY", "円": "JPY", "yen": "JPY", "￥": "JPY",
    "dollar": "USD", "usd": "USD", "$": "USD", "₩": "KRW"
}

def detect_currency(price_str):
    if not price_str:
        return "USD"
    lower_price = price_str.lower()
    for keyword, code in CURRENCY_KEYWORDS.items():
        if keyword in lower_price:
            return code
    return "USD"

# 단위 번역
def translate_quantity_suffix(suffix: str) -> str:
    if not suffix:
        return ''
    match = re.match(r'/\s*(\d+)\s*([^\d]*)', suffix)
    if not match:
        return suffix
    count, unit = match.groups()
    unit = unit.strip().lower()
    unit_translation = {
        "只": "개", "個": "개", "份": "개", "包": "봉지", "瓶": "병", "本": "병", "杯": "잔", "皿": "접시",
        "piece": "개", "pieces": "개", "bottle": "병", "bottles": "병",
        "pack": "팩", "packs": "팩", "cup": "컵", "cups": "컵", "bag": "봉지", "bags": "봉지"
    }
    translated_unit = unit_translation.get(unit, unit)
    return f"/{count}{translated_unit}"

# 메뉴명 번역 및 통화 추론
LANG_TO_CURRENCY = { "ko": "KRW", "en": "USD", "zh": "CNY", "ja": "JPY" }

def translate_menu_name(text, translate_client):
    detected = translate_client.detect_language(text)
    lang = detected["language"]
    lang_code = lang.split("-")[0]
    currency = LANG_TO_CURRENCY.get(lang_code, "USD")
    result = translate_client.translate(text, target_language='ko')
    return result["translatedText"], currency

# 💱 환율 API (캐시 포함)
exchange_rates = {}

def get_exchange_rate(from_currency):
    if from_currency in exchange_rates:
        return exchange_rates[from_currency]
    url = f"https://v6.exchangerate-api.com/v6/{os.environ['EXCHANGE_RATE_API_KEY']}/pair/{from_currency}/KRW"
    response = requests.get(url)
    data = response.json()
    rate = data["conversion_rate"]
    exchange_rates[from_currency] = rate
    return rate

# 🛠 메뉴 변환 및 저장
def enrich_menu_data_and_save(menu_json_str, output_path="result.json"):
    translate_client = translate.Client()
    menu_items = json.loads(menu_json_str)
    enriched = []

    for item in menu_items:
        menu_original = item.get("menu", "")
        price_str = item.get("price", "")

        # 숫자 추출
        try:
            price_matches = re.findall(r"\d+(?:\.\d+)?", price_str or "")
            price_num = float(price_matches[0]) if price_matches else None
        except:
            price_num = None

        # 단위 변환
        suffix_match = re.search(r"/\s*\d+\s*[^\s]*", price_str or "")
        suffix_raw = suffix_match.group().strip() if suffix_match else ""
        suffix_translated = translate_quantity_suffix(suffix_raw)

        # 메뉴 번역 + 통화 추정
        menu_ko, lang_currency = translate_menu_name(menu_original, translate_client)
        currency = detect_currency(price_str) or lang_currency

        # 환율 적용
        price_krw = None
        if price_num is not None:
            try:
                rate = get_exchange_rate(currency)
                price_krw = f"{int(price_num * rate):,}원{suffix_translated}"
            except:
                price_krw = None

        enriched.append({
            "menu_original": menu_original,
            "menu_ko": menu_ko,
            "price_original": price_str,
            "price_krw": price_krw,
            "currency": currency
        })

    # JSON 저장
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(enriched, f, ensure_ascii=False, indent=2)

    return enriched

# API 엔드포인트
@app.route('/process', methods=['GET', 'POST'])
def process_image():
    print("🔔 [요청 수신] /process 엔드포인트에 요청이 들어왔습니다.")
    print(f"📦 요청 방식: {request.method}")
    
    if request.method == 'GET':
        print("📡 GET 요청: 상태 확인용 응답 반환")
        return jsonify({"message": "📡 서버 정상 작동 중입니다. POST로 이미지를 업로드해주세요."}), 200

    if 'image' not in request.files:
        print("⚠️ 오류: 이미지 파일이 포함되지 않았습니다.")
        return jsonify({"error": "No image uploaded"}), 400

    image_file = request.files['image']
    print(f"📁 이미지 수신 완료: 파일 이름 = {image_file.filename}, 콘텐츠 타입 = {image_file.content_type}")
    
    image_bytes = image_file.read()
    print(f"📥 이미지 바이트 크기: {len(image_bytes)} bytes")

    try:
        print("🔍 OCR 처리 시작")
        ocr_text = extract_text_from_image_bytes(image_bytes)
        print(f"✅ OCR 결과:\n{ocr_text[:300]}...")  # 긴 텍스트는 일부만 출력

        print("🧠 Gemini 요약 요청 시작")
        gemini_json = summarize_menu_with_gemini(ocr_text)
        print(f"✅ Gemini 응답:\n{gemini_json}")

        print("🧹 JSON 정제 시작")
        cleaned_json = clean_json_response(gemini_json)
        print(f"✅ 정제된 JSON:\n{cleaned_json}")

        print("🌐 메뉴 번역 + 환율 적용 + 저장 시작")
        enriched_result = enrich_menu_data_and_save(cleaned_json, output_path="result.json")
        print(f"✅ 최종 변환된 메뉴 개수: {len(enriched_result)}")

        return jsonify(enriched_result)
    except Exception as e:
        print(f"🔥 예외 발생: {str(e)}")
        return jsonify({"error": str(e)}), 500
        return jsonify({"error": str(e)}), 500

# 서버 실행
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)

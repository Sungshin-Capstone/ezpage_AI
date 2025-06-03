import os
from dotenv import load_dotenv
import requests
from fastapi import FastAPI, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from ultralytics import YOLO
from PIL import Image
from io import BytesIO
import cv2
import numpy as np
import base64
from collections import Counter

app = FastAPI()
load_dotenv()  # 환경변수 로드

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
# Load the YOLO model
base_dir = os.path.dirname(__file__)
model_path = os.path.join(base_dir, "best.pt")
model = YOLO(model_path)

# 클래스별 화폐 단위 금액
currency_values = {
    # USD
    'USD_1cent': 0.01, 'USD_5cent': 0.05, 'USD_10cent': 0.10, 'USD_25cent': 0.25,
    'USD_50cent': 0.50, 'USD_100cent': 1.00, 'USD_1dollar': 1.0, 'USD_2dollar': 2.0,
    'USD_5dollar': 5.0, 'USD_10dollar': 10.0, 'USD_20dollar': 20.0, 'USD_50dollar': 50.0, 'USD_100dollar': 100.0,

    # JPY
    'JPY_1yen': 1, 'JPY_5yen': 5, 'JPY_10yen': 10, 'JPY_50yen': 50,
    'JPY_100yen': 100, 'JPY_500yen': 500, 'JPY_1000yen': 1000,
    'JPY_5000yen': 5000, 'JPY_10000yen': 10000,

    # # CNY
    # 'CNY_1jiao': 0.1, 'CNY_5jiao': 0.5, 'CNY_1yuan': 1.0, 'CNY_5yuan': 5.0,
    # 'CNY_10yuan': 10.0, 'CNY_20yuan': 20.0, 'CNY_50yuan': 50.0, 'CNY_100yuan': 100.0
}

currency_symbols = {
    'USD': '$',
    'JPY': '¥',
}

CONF_THRESHOLD = 0.5  # 신뢰도 기준
exchange_rates={} #캐시 저장소

# 화율 불러오기 (환경변수 + 캐시)
def get_exchange_rate(from_currency):
    if from_currency in exchange_rates:
        return exchange_rates[from_currency]

    api_key = os.environ.get("EXCHANGE_RATE_API_KEY")
    if not api_key:
        raise ValueError("환경변수에 EXCHANGE_RATE_API_KEY가 설정되지 않았습니다.")

    url = f"https://v6.exchangerate-api.com/v6/{api_key}/pair/{from_currency}/KRW"
    response = requests.get(url)
    if response.status_code == 200:
        data = response.json()
        rate = data["conversion_rate"]
        exchange_rates[from_currency] = rate
        return rate
    else:
        return 0.0


# 바운딩 박스 시각화 함수
def draw_boxes_on_image(image_path, results, threshold=0.5):
    image = cv2.imread(image_path)
    boxes = results[0].boxes

    for box in boxes:
        conf = float(box.conf)
        if conf < threshold:
            continue

        x1, y1, x2, y2 = map(int, box.xyxy[0].tolist())
        label = results[0].names[int(box.cls[0])]

        cv2.rectangle(image, (x1, y1), (x2, y2), (0,255,0), 2)
        cv2.putText(image, f"{label} {conf:.2f}", (x1, y1 - 10),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0,255,0), 2)

    _, buffer = cv2.imencode('.jpg', image)
    return base64.b64encode(buffer).decode('utf-8')


@app.post("/predict")
async def predict(file: UploadFile = File(...)):
    contents = await file.read()
    image = Image.open(BytesIO(contents)).convert("RGB")

    results = model(image)
    boxes = results[0].boxes
    class_names = model.names

    # 클래스 및 confidence 추출
    pred_classes = boxes.cls.tolist()
    confidences = boxes.conf.tolist()

    # threshold 필터링
    filtered = [(int(cls), conf) for cls, conf in zip(pred_classes, confidences) if conf >= CONF_THRESHOLD]
    pred_class_names = [class_names[cls] for cls, _ in filtered]

    # 총액 계산
    counts = Counter(pred_class_names)
    total = sum(currency_values.get(name, 0) * cnt for name, cnt in counts.items())

    # 국가 코드 추출
    first_class = pred_class_names[0] if pred_class_names else "UNKNOWN"
    country_prefix = first_class.split('_')[0]
    symbol = currency_symbols.get(country_prefix, '')

     #환율 변환 적용
    converted_total = round(total * get_exchange_rate(country_prefix), 2)

    # 시각화된 이미지 생성
    annotated_image_base64 = draw_boxes_on_image(image, results, threshold=CONF_THRESHOLD)

    return {
        "total": round(total, 2),
        "currency_symbol": symbol,
        "detected": dict(counts),
        "converted_total_krw": converted_total,
        "image_base64": annotated_image_base64
    }
import os
import cv2
import base64
from PIL import Image
from ultralytics import YOLO
from collections import Counter
from dotenv import load_dotenv
import requests

# 환경변수 로드
load_dotenv()

# 모델 로드
model = YOLO("best.pt")  

# 클래스별 화폐 단위 금액
currency_values = {
    'USD_1cent': 0.01, 'USD_5cent': 0.05, 'USD_10cent': 0.10, 'USD_25cent': 0.25,
    'USD_50cent': 0.50, 'USD_100cent': 1.00, 'USD_1dollar': 1.0, 'USD_2dollar': 2.0,
    'USD_5dollar': 5.0, 'USD_10dollar': 10.0, 'USD_20dollar': 20.0, 'USD_50dollar': 50.0, 'USD_100dollar': 100.0,
    'JPY_1yen': 1, 'JPY_5yen': 5, 'JPY_10yen': 10, 'JPY_50yen': 50,
    'JPY_100yen': 100, 'JPY_500yen': 500, 'JPY_1000yen': 1000,
    'JPY_5000yen': 5000, 'JPY_10000yen': 10000,
}

currency_symbols = {
    'USD': '$',
    'JPY': '¥',
}

CONF_THRESHOLD = 0.5
exchange_rates = {}

def get_exchange_rate(from_currency):
    if from_currency in exchange_rates:
        return exchange_rates[from_currency]

    api_key = os.environ.get("EXCHANGE_RATE_API_KEY")
    url = f"https://v6.exchangerate-api.com/v6/{api_key}/pair/{from_currency}/KRW"
    response = requests.get(url)
    if response.status_code == 200:
        rate = response.json()["conversion_rate"]
        exchange_rates[from_currency] = rate
        return rate
    else:
        return 0.0

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

    cv2.imwrite("annotated_result.jpg", image)
    print("시각화된 이미지 저장됨: annotated_result.jpg")

def main():
    image_path = "test_image.jpg"
    image = Image.open(image_path).convert("RGB")
    results = model(image)
    boxes = results[0].boxes
    class_names = model.names

    pred_classes = boxes.cls.tolist()
    confidences = boxes.conf.tolist()

    filtered = [(int(cls), conf) for cls, conf in zip(pred_classes, confidences) if conf >= CONF_THRESHOLD]
    pred_class_names = [class_names[cls] for cls, _ in filtered]

    counts = Counter(pred_class_names)
    total = sum(currency_values.get(name, 0) * cnt for name, cnt in counts.items())

    first_class = pred_class_names[0] if pred_class_names else "UNKNOWN"
    country_prefix = first_class.split('_')[0]
    symbol = currency_symbols.get(country_prefix, '')

    converted_total = round(total * get_exchange_rate(country_prefix), 2)

    draw_boxes_on_image(image_path, results, threshold=CONF_THRESHOLD)

    print("탐지된 클래스:", dict(counts))
    print(f"총액: {symbol}{round(total, 2)}")
    print(f"환산 금액: {converted_total} 원")

if __name__ == "__main__":
    main()

from ultralytics import YOLO
from PIL import Image

# 모델 로드
model = YOLO("best.pt")  # best.pt 파일은 현재 디렉토리에 있어야 합니다

# 테스트 이미지 열기
img = Image.open("test_image.jpg")  # 테스트할 이미지 경로

# 추론
results = model(img)

# 결과 출력
results[0].show()  # 바운딩 박스 시각화

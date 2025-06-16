# ezpage_AI
### ezpage 의 AI/ML파트를 맡고 있는 성신여자대학교 AI융합학부 성유빈,  오지윤,  홍수인입니다.
<table>
  <tr>
    <td align="center">
      <img src="https://github.com/user-attachments/assets/6c705621-4eb6-4ae0-897e-cb1daa9e1b34" width="200"/><br/>
      <b> 20211350 성유빈 </b>
    </td>
    <td align="center">
      <img src="https://github.com/user-attachments/assets/455809b7-d489-4035-af2a-a9fdd6d2b407" width="200"/><br/>
      <b> 20211419 홍수인 </b>
    </td>
    <td align="center">
      <img src="https://github.com/user-attachments/assets/2a26b657-1051-45da-8ed9-874181603e41" width="200"/><br/>
      <b> 20211367 오지윤 </b>
    </td>
  </tr>
</table>  

ezpage의 AI 기능은 다음과 같습니다.
- **AI지불스캐너**는 OCR을 활용해 메뉴판 이미지를 인식하고 Gemini로 텍스트를 정리한 후, 한국어 번역과 환율을 적용해 한국인 맞춤 정보를 제공합니다. <br>
- **글로벌 머니 스캐너**는 사용자가 촬영한 화폐 이미지를 국가와 단위 정보를 인식해 화폐 총 금액과 실시간 환율을 적용한 한화 금액을 알려줍니다. <br>

저희는 유저의 촬영 이미지를 활용해 사용자 친화적인 AI 파이프라인을 구축하여 여행자에게 실용적인 정보 제공을 목표로 합니다. 
<br>여행 중에도 메뉴판과 화폐 때문에 헤매지 않도록, ezpage가 도와드립니다. 더 똑똑하고 편리한 서비스를 향해, 저희는 계속 발전해 나가겠습니다 :)

<br>

#### 📁 [menu_ocr](https://github.com/Sungshin-Capstone/ezpage_AI/tree/861af1989789337ab33a976d98bbda382990422e/menu_ocr) : 사용자가 찍은 메뉴판 사진을 읽고, 메뉴를 번역한 뒤 가격을 원화로 바꿔주는 AI 지불스캐너입니다. 
      ├── __init__.py              : 패키지 인식용 초기화 파일
      ├── app.py                   : Flask 기반 API 서버 및 메인 코드(OCR + 번역 처리)
      ├── .env.sample              : 환경변수 템플릿 (API Key 등 설정용)
      ├── requirements.txt         : 설치해야 할 라이브러리 목록
      └── render.yaml              : Render 배포 설정 파일  
      

#### 📁 [global_money_scanner](https://github.com/Sungshin-Capstone/ezpage_AI/tree/main/global_money_scanner) : 사용자가 찍은 화폐가 어느 나라의 화폐로 얼마인지 인식하고, 현재 환율로 환산해주는 글로벌 머니 스캐너입니다.  
      ├── best.pt                  : YOLOv8 기반 화폐 탐지 모델 가중치 
      ├── main.py                  : Flask 기반 API 서버 및 메인 코드(화폐 탐지 및 금액 추출)
      ├── test.py                  : 로컬 테스트용 스크립트 
      ├── test_image.jpg           : 테스트 화폐 이미지 예시    
      ├── requirements.txt         : 실행에 필요한 라이브러리 목록
      ├── .gitignore.txt           : Git 추적 제외 설정 파일
      └── render.yaml              : Render 배포 설정 파일  
  **글로벌 머니 스캐너**는 사용자가 촬영한 **화폐 이미지**를 기반으로 <br>
- **화폐의 국가** 및 **단위 종류**를 인식 <br>
- 인식된 금액을 **자동 합산**한 뒤 <br>
- **실시간 환율 API**를 통해 **원화(KRW)로 환산**하는 AI 기반 화페 분석 서비스입니다.

#### 📁 [expenses/payment_guide.py](https://github.com/Sungshin-Capstone/ezpage_Frontend/blob/main/components/modals/PaymentGuide.jsx) : 사용자의 마이 월렛에 있는 금액 기반으로 최적의 지불 방법 2가지 추천해주는 알고리즘입니다.
      └── payment_guide.py          : 지불 알고리즘 메인 코드

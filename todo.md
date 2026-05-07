# Finance Compass - Project TODO

## Core Features
- [x] 모바일 앱 초기화 및 스캐폴딩 설정
- [x] 브랜드 테마와 앱 설정 업데이트
- [x] 홈 화면에 유학생 금융 요약 대시보드 구현
- [x] 결제 알림 텍스트 파싱 및 자동 카테고리화 로직 구현
- [x] 거래 기록 화면과 카테고리 수정 흐름 구현
- [x] 장학금·비자·부모님 보고용 증빙 리포트 화면 구현

## Advanced Features
- [x] 환율 시계열 분석 기반 '지금 보내세요 / N일 대기 권장' 추천 화면 구현
- [x] 설정 화면에 자동 분류 규칙과 앱 설명 추가
- [x] 앱 아이콘 생성 및 브랜딩 자산 반영
- [x] 타입 검사와 앱 상태 점검 수행

## Data Input Methods
- [x] 백그라운드 알림 자동 수집 기능 (알림 권한, 노티피케이션 리스너)
- [x] 영수증 OCR 인식 기능 (사진 업로드 및 텍스트 추출)
- [x] Excel 파일 업로드 기능 (달단위 거래내역 일괄 분석)
- [x] 클립보드 자동 붙여넣기 기능 (결제 알림 텍스트 자동 감지)

## UI/UX Improvements
- [x] 전체 UI 디자인 리루늘 (단정한 도미넌스, 동적 애니메이션, 마이크로 인터랙션)
- [x] 전체 앱 상태 점검 및 최종 체크포인트

## Integration & Intelligence
- [x] 오픈뱅킹 API 연동 (주요 은행 거래내역 자동 조회)
- [x] AI 규칙 자동 학습 기능 (사용자 수정 내역 단순 연스 내 규칙 추천)
- [x] PDF 증빙 리포트 내보내기 (기간별 필터링 및 장학금 신청용 서식)
- [x] 분류 정확도 단위 테스트 및 검증 방법 구현

## Budget & Analytics
- [x] 예산 설정 데이터 모델 및 저장 로직 구현
- [x] 월별/카테고리별 지출 트렌드 차트 화면 구현
- [x] 예산 초과 알림 및 카테고리별 진행률 표시
- [x] 지출 목표 설정 및 달성도 시각화
- [x] 예산 관리 통합 화면 구현
- [x] 예산 및 목표 관리 테스트
- [x] 최종 검증 및 체크포인트 저장

## Key Metrics
- Classification Accuracy: 73.3% (11/15 merchants correctly classified)
- Test Coverage: 10 tests passing, 1 skipped
- Type Safety: 0 TypeScript errors


## 다국 영수증 인증 서비스 (완료)
- [x] 영수증 OCR 분석 (Gemini 1.5 Flash)
- [x] 상호명, 품목, 금액 추출
- [x] 원화 환산 금액 계산
- [x] 더치페이 자동 정산 추천

## 더치페이 정산 서비스 (완료)
- [x] 참가자 추가/제거
- [x] 각 참가자 결제 금액 입력
- [x] 자동 정산 계산
- [x] 정산 내역 시각화

## 메뉴판 스캐너 (완료)
- [x] 메뉴판 이미지 분석
- [x] 메뉴명 및 가격 추출
- [x] 평균가 비교 분석
- [x] 텍스트 입력 모드 지원

## 국가/통화 설정 (완료)
- [x] 10개 국가 지원 (USD, JPY, GBP, EUR, CNY, THB, SGD, AUD, CAD, HKD)
- [x] 환율 자동 계산
- [x] XRPL 지갑 설정
- [x] 백엔드 URL 설정

## 모바일 앱 화면 (완료)
- [x] 설정 화면 - 국가/통화, XRPL, 백엔드 설정
- [x] 영수증 스캐너 - 카메라/갤러리, 분석, 더치페이
- [x] 메뉴판 스캐너 - 이미지/텍스트, 평균가 비교
- [x] 더치페이 정산 - 인원 관리, 금액 입력, 자동 정산
- [x] 탭 네비게이션 - 4개 새로운 탭 추가

## API 훅 (완료)
- [x] useSettings - AsyncStorage 기반 설정 관리
- [x] useReceiptScanner - 영수증 스캔 및 분석
- [x] useMenuScanner - 메뉴판 스캔 및 분석
- [x] useDutchPay - 더치페이 정산 계산
- [x] useXRPL - XRPL 트랜잭션 기록

## 타입 정의 (완료)
- [x] Currency, CountryConfig
- [x] ReceiptAnalysisResult, MenuAnalysisResult
- [x] DutchPaySettlement, DutchPayMember
- [x] XRPLTransactionResult, AppSettings

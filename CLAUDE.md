# CLAUDE.md

POSCO FLOW CSU(연속식 하역기) AI 하역 디지털 트윈. Streamlit 단일 파일 앱이며, 발표용 시뮬레이션입니다(실시간 설비 연동 없음). 자세한 설명은 README.md를 참고하세요.

## 파일 구조
- `streamlit_app.py`: 앱 본체 (단일 파일)
- `requirements.txt`: 의존 패키지
- `run.bat`: 로컬 실행 스크립트
- `archive_prev_v4/`: 이전 버전 백업

## 실행
- `run.bat`을 실행합니다. 포트는 8501입니다.
- venv는 OneDrive 밖(`%LOCALAPPDATA%\csu_venv`)에 있습니다. 프로젝트 폴더 안에 venv를 만들지 마세요.

## 응답 규칙
- 항상 한국어로, 쉬운 말로 답합니다. 전문용어는 풀어서 설명합니다.

## streamlit_app.py 수정 원칙
- 큰 수정 전에 백업을 먼저 만듭니다. 이름은 `archive_prev_v4/`의 방식(`csu_digital_twin_v4_..._YYYYMMDD.py`)을 따릅니다.
- 요청한 부분만 최소로 수정합니다. 승인된 화면과 동작은 건드리지 않습니다.
- 단일 파일 구조를 유지합니다. 파일을 쪼개지 않습니다.
- 수정 후 실행하거나 구문 검사를 해서 동작을 확인합니다.

## archive_prev_v4/
- 요청할 때만 수정합니다.

## git
- 작업이 끝나면 커밋은 자동으로 합니다.
- GitHub 푸시는 반드시 사용자에게 먼저 확인합니다.

## 알려진 주의점
- 수집·입력한 데이터는 브라우저 세션에만 저장됩니다. CSV 다운로드가 필요합니다.
- `st.components.v1.html`은 향후 `st.iframe`으로 바뀔 수 있습니다.
- 회사 관련 화면이므로 배포는 비공개를 권장합니다.

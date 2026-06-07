프로젝트 설명: 이 프로젝트는 AI 기반의 스마트 사진 앨범입니다.
1. 폴더를 엽니다.

smart_album

2. backend 폴더로 이동합니다.

cd backend

venv라는 이름의 가상 환경 폴더를 생성합니다.
python -m venv venv

3. 가상 환경을 활성화합니다.

.\venv\Scripts\Activate.ps1

성공:

(venv) PS ...

터미널(venv)에서 실행하세요.
pip install -r requirements.txt

4. FastAPI를 시작합니다.

python -m uvicorn main:app --reload

성공:

Uvicorn이 http://127.0.0.1:8000에서 실행 중입니다.

5. 백엔드를 테스트합니다.

http://127.0.0.1:8000/docs

6. 새 VS Code 창을 엽니다.

frontend 폴더로 이동합니다.

cd frontend

7. Flutter를 실행합니다.

flutter run

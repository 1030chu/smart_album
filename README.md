프로젝트 설명: 이 프로젝트는 AI 기반의 스마트 사진 앨범입니다.
1. 폴더를 엽니다.

smart_album_system

2. VS Code 터미널을 엽니다.

3. backend 폴더로 이동합니다.

cd backend

4. 가상 환경을 활성화합니다.

venv\Scripts\activate

성공:

(venv) PS ...

5. FastAPI를 시작합니다.

python -m uvicorn main:app --reload

성공:

Uvicorn이 http://127.0.0.1:8000에서 실행 중입니다.

6. 백엔드를 테스트합니다.

http://127.0.0.1:8000/docs

7. 새 VS Code 창을 엽니다.

frontend 폴더로 이동합니다.

cd frontend_flutter

8. Flutter를 실행합니다.

flutter run

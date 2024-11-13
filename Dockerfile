# Python 3.9 이미지를 베이스로 사용
FROM python:3.11

# 작업 디렉토리 설정
WORKDIR /code

# requirements.txt 복사
COPY ./requirements.txt /code/requirements.txt

# 패키지 설치
RUN pip install --no-cache-dir --upgrade -r /code/requirements.txt

# 애플리케이션 파일 복사 (main.py와 필요한 폴더들)
COPY ./main.py /code/main.py
COPY ./practice.py /code/practice.py
COPY ./riot_module.py /code/riot_module.py
COPY ./imgs /code/imgs
COPY ./templates /code/templates
COPY ./__pycache__ /code/__pycache__

# FastAPI 실행 명령어 (main.py 파일을 80번 포트로 실행)
CMD ["uvicorn", "practice:app", "--host", "0.0.0.0", "--port", "80"]
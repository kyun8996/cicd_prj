############################# fastapi모듈 ###################################
from fastapi import FastAPI
from fastapi.templating import Jinja2Templates
# Jinja2Templates: Jinja2 템플릿 엔진을 FastAPI에서 사용하도록 하는 클래스입니다. HTML 파일을 렌더링할 때 사용합니다.
from fastapi import APIRouter, Request, status, Depends, Form
# APIRouter: API의 경로를 분리하여 정의하고 관리하는 라우터입니다. API의 특정 부분을 독립적으로 관리할 수 있어 코드의 모듈화를 돕습니다.
# Request: 요청 객체로, 클라이언트가 서버에 보낸 요청의 모든 정보를 담고 있습니다.
# status: FastAPI에서 HTTP 상태 코드를 쉽게 참조할 수 있는 모듈입니다.
# Depends와 Form: 의존성 주입과 폼 데이터를 처리하는 데 사용됩니다. 이 코드에서는 사용되지 않지만, 확장 시 필요한 기능일 수 있습니다.
from fastapi.responses import RedirectResponse
#############################################################################
############################# roit 관련 모듈 #################################
import pandas as pd
import requests
import time
from datetime import datetime
from collections import Counter
from urllib import parse
from fastapi.staticfiles import StaticFiles

############################# index page 출력 #################################
app = FastAPI()
templates = Jinja2Templates(directory="templates")
# 정적 파일 경로 설정 (imgs 폴더를 위한 설정)
app.mount("/imgs", StaticFiles(directory="imgs"), name="imgs")


@app.get("/")
async def get_main_page(request : Request):
    return templates.TemplateResponse(
        "index.html", {"request": request}
    )



@app.post("/champs")  # 폼 데이터를 처리할 경로
async def submit_form(request : Request, tag_line: str = Form(...), user_nickname: str = Form(...)):
    # 폼 데이터를 처리
    print(f"UserTag: {tag_line}, UserNickname: {user_nickname}")

    recommended_champion_name = 'Akshan'

    return templates.TemplateResponse("champ.html", {"request": request, "recommended_champion_name": recommended_champion_name})  # 폼을 제출한 후 메인 페이지로 리다이렉트
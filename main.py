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
#############################################################################
import riot_module as r_m 


############################# index page 출력 #################################
app = FastAPI()
templates = Jinja2Templates(directory="templates")


@app.get("/")
async def get_main_page(request : Request):
    return templates.TemplateResponse(
        "index.html", {"request": request}
    )

##############################################################################
############################# riot api 설정 #################################
# API 키 및 헤더 설정
api_key = "RGAPI-2004a461-295e-4660-aa3d-f20a465e40c7"  # 만료 시 업데이트 필요
REQUEST_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36",
    "Accept-Language": "ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7",
    "Accept-Charset": "application/x-www-form-urlencoded; charset=UTF-8",
    "Origin": "https://developer.riotgames.com",
    "X-Riot-Token": api_key
}

# 챔피언 ID와 이름 매핑을 위한 DataDragon API URL
champ_name_url = "https://ddragon.leagueoflegends.com/cdn/14.22.1/data/en_US/champion.json"
##############################################################################
# 유저 정보 가져오기 함수
def fetch_user_info(encodedName,tagLine):
    url = f"https://asia.api.riotgames.com/riot/account/v1/accounts/by-riot-id/{encodedName}/{tagLine}"
    try:
        response = requests.get(url, headers=REQUEST_HEADERS)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error fetching user info: {e}")
        return None

@app.post("/champs")  # 폼 데이터를 처리할 경로
async def submit_form(tag_line: str = Form(...), user_nickname: str = Form(...)):
    # 폼 데이터를 처리
    print(f"UserTag: {tag_line}, UserNickname: {user_nickname}")
    userNickname = user_nickname
    tagLine = tag_line
    encodedName = parse.quote(userNickname)
    player_id = fetch_user_info(encodedName,tagLine)
    if player_id:
        puuid = player_id.get('puuid')
        player = r_m.safe_request(f"https://kr.api.riotgames.com/lol/summoner/v4/summoners/by-puuid/{puuid}", REQUEST_HEADERS)
        if player:
            player_df = pd.DataFrame([player]).T.reset_index()
            player_df.columns = ['Field', 'Value']
            # print("### 소환사 정보")
            # print(player_df.to_markdown(index=False))

            # 챔피언 숙련도 정보 가져오기
            mastery_url = f"https://kr.api.riotgames.com/lol/champion-mastery/v4/champion-masteries/by-puuid/{puuid}"
            mastery_data = r_m.safe_request(mastery_url, REQUEST_HEADERS)
            if mastery_data:
                # 상위 5개의 챔피언 정보 추출
                top_5_champions = sorted(mastery_data, key=lambda x: x['championLevel'], reverse=True)[:5]

                # championId를 챔피언 이름으로 변환
                top_5_champions_with_names = []
                for champ in top_5_champions:
                    champion_name = r_m.get_champion_name_by_id(champ['championId'])
                    if champion_name:
                        champ['championName'] = champion_name
                    top_5_champions_with_names.append(champ)

                # DataFrame으로 변환 및 출력
                mastery_df = pd.DataFrame(top_5_champions_with_names)
                # print("\n### 상위 5개 챔피언 숙련도 정보")
                # print(mastery_df[['championName', 'championLevel', 'championPoints']].to_markdown(index=False))
            else:
                print("Error: 챔피언 숙련도 정보를 가져오는 데 실패했습니다.")

            # 리그 정보 가져오기 및 솔로랭크와 자유랭크 분리
            playerInfo = r_m.safe_request(f"https://kr.api.riotgames.com/lol/league/v4/entries/by-summoner/{player['id']}", REQUEST_HEADERS)
            solo_rank, free_rank = None, None
            if playerInfo:
                for entry in playerInfo:
                    if entry['queueType'] == 'RANKED_SOLO_5x5':
                        solo_rank = entry
                    elif entry['queueType'] == 'RANKED_FLEX_SR':
                        free_rank = entry

                if solo_rank:
                    solo_rank_df = pd.DataFrame([solo_rank]).T.reset_index()
                    solo_rank_df.columns = ['Field', 'Value']

                if free_rank:
                    free_rank_df = pd.DataFrame([free_rank]).T.reset_index()
                    free_rank_df.columns = ['Field', 'Value']
                    
            # 솔로랭크와 자유랭크의 최근 50게임 챔피언의 플레이 횟수 가져오기
            if solo_rank:
                solo_match_ids = r_m.fetch_recent_matches(puuid, 420)  # 420은 솔로랭크 대기열 번호
                if solo_match_ids:
                    solo_champion_count = r_m.get_champion_play_count(puuid, solo_match_ids)
                    most_common_solo = solo_champion_count.most_common(3)    # 솔로랭크에서 가장 많이 플레이한 챔피언


            if free_rank:
                free_match_ids = r_m.fetch_recent_matches(puuid, 440)  # 440은 자유랭크 대기열 번호
                if free_match_ids:
                    free_champion_count = r_m.get_champion_play_count(puuid, free_match_ids)
                    most_common_free = free_champion_count.most_common(3)   # 자유랭크에서 가장 많이 플레이한 챔피언
    else:
        print("Error: 소환사 정보를 가져오는 데 실패했습니다.")


    # 솔로랭크의 상세 게임 정보 출력
    if solo_rank:
        solo_match_ids = r_m.fetch_recent_matches(puuid, 420)  # 솔로랭크 게임
        if solo_match_ids:
            solo_match_df = r_m.fetch_match_details(puuid, solo_match_ids)

    champion_url = "https://ddragon.leagueoflegends.com/cdn/14.22.1/data/ko_KR/champion.json"
    response = requests.get(champion_url)
    champion_data = response.json()['data']

    # 챔피언 이름, tags, stats 추출
    champion_info = {
        champ_name: {
            'tags': champion_data[champ_name]['tags'],
            'stats': champion_data[champ_name]['stats']
        }
        for champ_name in champion_data
    }

    # 챔피언별로 그룹화하여 상위 5개 챔피언의 통계 계산
    champion_stats = solo_match_df.groupby('챔피언').agg(
        games_played=('챔피언', 'size'),
        kills=('킬', 'sum'),
        deaths=('데스', 'sum'),
        assists=('어시스트', 'sum'),
        wins=('승리 여부', lambda x: (x == '승리').sum())  # 승리 횟수
    ).reset_index()

    # KDA, 승률, 숙련도 점수 계산
    champion_stats['KDA'] = ((champion_stats['kills'] + champion_stats['assists']) / champion_stats['deaths'].replace(0, 1)).round(2)
    champion_stats['승률'] = (champion_stats['wins'] / champion_stats['games_played'] * 100).round(2)
    # 게임 플레이 횟수 기준으로 상위 5개 챔피언 선택
    top_5_champions = champion_stats.sort_values(by='games_played', ascending=False).head(5)

    top_5_champions['tags'] = top_5_champions['챔피언'].apply(lambda x: champion_info.get(x, {}).get('tags', []))
    top_5_champions['stats'] = top_5_champions['챔피언'].apply(lambda x: champion_info.get(x, {}).get('stats', {}))

    ##############################################################################################

    # 1. 추천 챔피언 선정
    recommended_champion = top_5_champions.sort_values(by=["승률", "games_played"], ascending=False).iloc[0]
    recommended_champion_name = recommended_champion["챔피언"]

    # 결과 출력
    print(f"추천 챔피언: {recommended_champion_name}")
    print(type(recommended_champion_name))
    # annie


    # 예시로 리다이렉트하거나 다른 처리를 할 수 있음
    return RedirectResponse(url="/")  # 폼을 제출한 후 메인 페이지로 리다이렉트





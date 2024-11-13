############################# roit 관련 모듈 #################################
import pandas as pd
import requests
import time
from datetime import datetime
from collections import Counter
from urllib import parse
import main as m
#############################################################################
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



# 요청에 지연 시간과 재시도 로직 추가
def safe_request(url, headers, retries=3, delay=2):
    for _ in range(retries):
        try:
            response = requests.get(url, headers=headers)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.HTTPError as e:
            if response.status_code == 429:
                print(f"Rate limit exceeded. Retrying in {delay} seconds...")
                time.sleep(delay)
                # 고정된 delay를 유지해 제한된 대기 시간 확보
            else:
                print(f"HTTP error occurred: {e}")
                break
        except requests.exceptions.RequestException as e:
            print(f"Request error occurred: {e}")
            break
    print("Max retries exceeded.")
    return None


# 챔피언 ID를 이름으로 변환하는 함수
def get_champion_name_by_id(champion_id):
    # DataDragon에서 최신 챔피언 정보를 가져옴
    champions_data = safe_request(champ_name_url, REQUEST_HEADERS)
    if champions_data:
        champion_dict = champions_data.get('data', {})
        for champ_key, champ_info in champion_dict.items():
            if champ_info['key'] == str(champion_id):
                return champ_info['id']
    return None



# 최근 50게임 가져오기 (솔로랭크, 자유랭크 별)
def fetch_recent_matches(puuid, queue_type):
    url = f"https://asia.api.riotgames.com/lol/match/v5/matches/by-puuid/{puuid}/ids?count=50&queue={queue_type}"
    time.sleep(0.05)  # 초당 20번 요청 제한 유지
    return safe_request(url, REQUEST_HEADERS)


# 챔피언의 플레이 횟수 추출
def get_champion_play_count(puuid, match_ids):
    champion_counter = Counter()
    for match_id in match_ids:
        url = f"https://asia.api.riotgames.com/lol/match/v5/matches/{match_id}"
        match_data = safe_request(url, REQUEST_HEADERS)
        if match_data:
            for participant in match_data['info']['participants']:
                if participant['puuid'] == puuid:
                    champion_counter[participant['championName']] += 1
    return champion_counter



# 게임 정보 상세 추출 함수
def fetch_recent_matches(puuid, queue_type, max_retries=3, retry_delay=120):
    url = f"https://asia.api.riotgames.com/lol/match/v5/matches/by-puuid/{puuid}/ids?count=50&queue={queue_type}"
    attempts = 0

    while attempts < max_retries:
        try:
            response = requests.get(url, headers=REQUEST_HEADERS)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            if response.status_code == 429:  # Too Many Requests
                print(f"Too many requests. Waiting for {retry_delay} seconds before retrying...")
                time.sleep(retry_delay)  # 일정 시간 대기
                attempts += 1
            else:
                print(f"Error fetching recent matches: {e}")
                break
    return None  # 최대 재시도 횟수 초과 시 None 반환


# 경기 세부 정보 추출
def fetch_match_details(puuid, match_ids, max_retries=3, retry_delay=120):
    match_data_list = []
    for match_id in match_ids:
        url = f"https://asia.api.riotgames.com/lol/match/v5/matches/{match_id}"
        attempts = 0

        while attempts < max_retries:
            try:
                response = requests.get(url, headers=REQUEST_HEADERS)
                response.raise_for_status()
                match_data = response.json()

                # 현재 유저의 참여 정보 추출
                user_data = next((p for p in match_data['info']['participants'] if p['puuid'] == puuid), None)
                if user_data:
                    # KDA 계산 (데스가 0일 경우 무한대 방지)
                    kda = (user_data['kills'] + user_data['assists']) / user_data['deaths'] if user_data['deaths'] > 0 else (user_data['kills'] + user_data['assists'])

                    match_info = {
                        "게임 ID": match_id,
                        "승리 여부": "승리" if user_data['win'] else "패배",
                        "챔피언": user_data['championName'],
                        "킬": user_data['kills'],
                        "데스": user_data['deaths'],
                        "어시스트": user_data['assists'],
                        "KDA": round(kda, 2),  # 소수점 둘째 자리 반올림
                        "게임 길이(분)": match_data['info']['gameDuration'] // 60,
                        "게임 시작 시간": datetime.fromtimestamp(match_data['info']['gameStartTimestamp'] / 1000)
                    }
                    match_data_list.append(match_info)
                break  # 성공 시 반복 탈출
            except requests.exceptions.RequestException as e:
                if response.status_code == 429:  # Too Many Requests
                    print(f"Too many requests for match ID {match_id}. Waiting for {retry_delay} seconds before retrying...")
                    time.sleep(retry_delay)  # 대기 후 재시도
                    attempts += 1
                else:
                    print(f"Error fetching match details for match ID {match_id}: {e}")
                    break  # 다른 오류일 경우 반복 탈출

    return pd.DataFrame(match_data_list)
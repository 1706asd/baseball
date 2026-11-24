import streamlit as st
import pandas as pd
import random

# ==========================================
# 1. 페이지 설정 및 커스텀 CSS
# ==========================================
st.set_page_config(
    page_title="THE DIAMOND: 야구 선수 인생 시뮬레이션",
    page_icon="⚾",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
<style>
    .main-title {
        font-size: 2.3rem;
        font-weight: 800;
        color: #1E3A8A;
        margin-bottom: 0.2rem;
    }
    .sub-title {
        font-size: 1.05rem;
        color: #4B5563;
        margin-bottom: 1.5rem;
    }
    .stat-box {
        background-color: #F8FAFC;
        border: 1px solid #E2E8F0;
        border-radius: 10px;
        padding: 15px;
        text-align: center;
    }
    .log-box {
        background-color: #0F172A;
        color: #F8FAFC;
        padding: 15px;
        border-radius: 8px;
        font-family: 'Courier New', monospace;
        max-height: 280px;
        overflow-y: auto;
        font-size: 0.9rem;
    }
</style>
""", unsafe_allow_html=True)

# ==========================================
# 2. 게임 상수 및 데이터 정의
# ==========================================
KBO_TEAMS = [
    "LG 트윈스", "KT 위즈", "SSG 랜더스", "NC 다이노스", "두산 베어스",
    "KIA 타이거즈", "롯데 자이언츠", "삼성 라이온즈", "한화 이글스", "키움 히어로즈"
]

MLB_TEAMS = [
    "LA 다저스", "뉴욕 양키스", "샌디에이고 파드리스", "샌프란시스코 자이언츠",
    "보스턴 레드삭스", "텍사스 레인저스", "애틀랜타 브레이브스", "시애틀 매리너스"
]

POSITIONS = {
    "타자 (내야수)": "Batter",
    "타자 (외야수)": "Batter",
    "타자 (포수)": "Batter",
    "투수 (선발)": "Pitcher",
    "투수 (불펜/마무리)": "Pitcher"
}

# ==========================================
# 3. 세션 상태 초기화
# ==========================================
def init_game():
    if "game_started" not in st.session_state:
        st.session_state.game_started = False
    if "retired" not in st.session_state:
        st.session_state.retired = False
    if "player" not in st.session_state:
        st.session_state.player = {}
    if "career_stats" not in st.session_state:
        st.session_state.career_stats = []
    if "logs" not in st.session_state:
        st.session_state.logs = []
    if "awards" not in st.session_state:
        st.session_state.awards = []
    if "offseason_event" not in st.session_state:
        st.session_state.offseason_event = None  # None, "FA_KBO", "MLB_POSTING"

def add_log(msg, icon="⚾"):
    year = st.session_state.player.get("year", 2026)
    age = st.session_state.player.get("age", 19)
    st.session_state.logs.insert(0, f"[{year}년 / {age}세] {icon} {msg}")

# ==========================================
# 4. 시뮬레이션 핵심 엔진
# ==========================================
def get_overall(p):
    stats = p["stats"]
    return round(sum(stats.values()) / len(stats), 1)

def train_player(focus_stat, intensity):
    p = st.session_state.player
    age = p["age"]
    
    # 나이에 따른 성장 보정
    age_factor = 1.2 if age <= 24 else (1.0 if age <= 30 else 0.6)
    
    if intensity == "가벼운 컨디셔닝 (부상 위험 낮음)":
        gain = random.uniform(1.5, 3.0) * age_factor
        fatigue_add = 5
        injury_chance = 0.02
    elif intensity == "표준 시즌 준비 (균형 잡힌 훈련)":
        gain = random.uniform(3.0, 5.5) * age_factor
        fatigue_add = 15
        injury_chance = 0.07
    else:  # 지옥의 특훈
        gain = random.uniform(5.5, 9.0) * age_factor
        fatigue_add = 30
        injury_chance = 0.18

    # 집중 능력치 상승
    p["stats"][focus_stat] = min(99.0, round(p["stats"][focus_stat] + gain, 1))
    
    # 나머지 능력치 소폭 상승
    for k in p["stats"]:
        if k != focus_stat:
            sub_gain = random.uniform(0.3, 1.2) * age_factor
            p["stats"][k] = min(99.0, round(p["stats"][k] + sub_gain, 1))

    p["fatigue"] = min(100, p["fatigue"] + fatigue_add)
    
    # 부상 체크
    if random.random() < injury_chance + (p["fatigue"] / 500):
        loss = round(random.uniform(2.0, 4.5), 1)
        p["stats"][focus_stat] = max(30.0, round(p["stats"][focus_stat] - loss, 1))
        p["injured_games"] = random.randint(25, 65)
        add_log(f"비시즌 훈련 중 부상을 당했습니다! ({focus_stat} -{loss}, 시즌 결장 예상)", "🏥")
    else:
        p["injured_games"] = 0
        add_log(f"비시즌 '{focus_stat}' 집중 훈련 완료! 능력치가 크게 향상되었습니다.", "💪")

def simulate_season():
    p = st.session_state.player
    p["year"] += 1
    p["age"] += 1
    
    ovr = get_overall(p)
    league = p["league"]
    p_type = p["type"]
    age = p["age"]

    # 에이징 커브 (33세 이후 노쇠화 시작)
    if age >= 33:
        decay = (age - 32) * random.uniform(0.6, 1.4)
        for k in p["stats"]:
            p["stats"][k] = max(30.0, round(p["stats"][k] - decay, 1))
        add_log(f"세월의 무게가 느껴집니다. 전반적인 신체 능력이 하락했습니다.", "📉")

    # 리그 승격/강등 판정 (KBO 2군 -> 1군)
    if league == "KBO 퓨처스(2군)":
        if ovr >= 58 or (ovr >= 54 and random.random() < 0.5):
            p["league"] = "KBO 1군"
            league = "KBO 1군"
            add_log("축하합니다! 2군 무대를 평정하고 KBO 1군 엔트리에 콜업되었습니다!", "🎉")

    # 출전 경기 수 계산
    max_games = 144 if "KBO" in league else 162
    if ovr < 52 and league == "KBO 1군":
        base_games = random.randint(30, 75)
    elif ovr < 68 and league == "MLB":
        base_games = random.randint(45, 95)
    else:
        base_games = random.randint(int(max_games * 0.82), max_games)
    
    games = max(10, base_games - p.get("injured_games", 0))
    p["injured_games"] = 0
    p["fatigue"] = max(0, p["fatigue"] - 10)  # 시즌 중 관리

    # ------------------------------------------
    # 타자 성적 시뮬레이션
    # ------------------------------------------
    if p_type == "Batter":
        contact = p["stats"]["컨택"]
        power = p["stats"]["파워"]
        eye = p["stats"]["선구안"]
        speed = p["stats"]["주루/수비"]

        # 리그 난이도 보정
        diff = 0 if league == "KBO 퓨처스(2군)" else (8 if league == "KBO 1군" else 19)
        
        pa = int(games * random.uniform(3.8, 4.4))
        bb_rate = max(0.04, min(0.22, (eye - diff) / 420))
        bb = int(pa * bb_rate)
        ab = max(1, pa - bb)

        avg = max(0.160, min(0.395, 0.140 + ((contact - diff) * 0.0023) + random.uniform(-0.022, 0.025)))
        hits = int(ab * avg)
        
        hr_rate = max(0.005, ((power - diff) ** 1.45) / 6800)
        hr = int(ab * hr_rate * random.uniform(0.8, 1.25))
        hr = min(hits, hr)
        
        doubles = int(hits * random.uniform(0.16, 0.24))
        triples = int(hits * (speed / 2500))
        singles = max(0, hits - hr - doubles - triples)
        
        rbi = int(hr * 2.4 + (hits - hr) * 0.35 + random.randint(0, 12))
        sb = int(games * max(0, (speed - 45) / 140) * random.uniform(0.7, 1.3))

        obp = round((hits + bb) / max(1, pa), 3)
        slg = round((singles + doubles*2 + triples*3 + hr*4) / ab, 3)
        ops = round(obp + slg, 3)
        avg = round(hits / ab, 3)

        # WAR 근사치
        war = round((ops - (0.710 if "KBO" in league else 0.720)) * (pa / 48) + (speed - 55)*0.03, 1)
        war = max(-1.5, war)

        stat_record = {
            "연도": p["year"], "나이": age, "소속팀": p["team"], "리그": league,
            "경기": games, "타율": f"{avg:.3f}", "안타": hits, "홈런": hr,
            "타점": rbi, "도루": sb, "OPS": f"{ops:.3f}", "WAR": war
        }
        st.session_state.career_stats.append(stat_record)
        add_log(f"[{league}] {games}경기 타율 {avg:.3f} / {hr}홈런 / {rbi}타점 / OPS {ops:.3f} (WAR {war})")

        # 타이틀 및 수상 판정
        if league == "KBO 1군":
            if war >= 7.5:
                st.session_state.awards.append(f"{p['year']} KBO 정규시즌 MVP")
                add_log("🏆 KBO 정규시즌 MVP를 수상했습니다!", "👑")
            elif war >= 4.8:
                st.session_state.awards.append(f"{p['year']} KBO 골든글러브")
                add_log("🥇 포지션 최고 선수! KBO 골든글러브를 수상했습니다!", "🏆")
            if hr >= 38:
                st.session_state.awards.append(f"{p['year']} KBO 홈런왕 ({hr}개)")
        elif league == "MLB":
            if war >= 8.0:
                st.session_state.awards.append(f"{p['year']} MLB MVP")
                add_log("🌎 메이저리그의 왕! MLB MVP를 수상했습니다!", "👑")
            elif war >= 5.0:
                st.session_state.awards.append(f"{p['year']} MLB 올스타 선정")
                add_log("⭐ 꿈의 무대 MLB 올스타에 선정되었습니다!", "🌟")

    # ------------------------------------------
    # 투수 성적 시뮬레이션
    # ------------------------------------------
    else:
        stuff = p["stats"]["구위"]
        ctrl = p["stats"]["제구"]
        brk = p["stats"]["변화구"]
        stam = p["stats"]["체력"]

        diff = 0 if league == "KBO 퓨처스(2군)" else (8 if league == "KBO 1군" else 19)
        is_starter = "선발" in p["position"]

        if is_starter:
            g = min(32, max(10, int(games / 4.8)))
            ip = round(g * random.uniform(4.8, 6.4) * (stam / 72), 1)
        else:
            g = min(78, max(20, int(games * 0.48)))
            ip = round(g * random.uniform(0.9, 1.3), 1)

        pitch_score = (stuff * 0.35 + ctrl * 0.35 + brk * 0.30) - diff
        era = max(1.35, min(7.80, 5.90 - (pitch_score * 0.052) + random.uniform(-0.45, 0.50)))
        era = round(era, 2)

        k9 = max(3.5, min(14.5, 4.0 + ((stuff + brk)/2 - diff) * 0.11))
        so = int(ip * (k9 / 9))
        
        whip = max(0.75, min(1.85, 1.65 - ((ctrl + brk)/2 - diff) * 0.009))
        whip = round(whip, 2)

        if is_starter:
            win_prob = max(0.15, min(0.85, (5.0 - era) / 4.5 + 0.42))
            wins = int(g * win_prob * random.uniform(0.75, 1.15))
            losses = max(0, int(g * (1 - win_prob) * random.uniform(0.6, 1.0)))
            saves = 0
        else:
            wins = random.randint(1, 7)
            losses = random.randint(1, 6)
            saves = int(g * max(0.1, (5.0 - era)/6)) if ovr >= 68 else random.randint(0, 8)

        war = round(((4.50 if "KBO" in league else 4.20) - era) * (ip / 42), 1)
        war = max(-1.5, war)

        stat_record = {
            "연도": p["year"], "나이": age, "소속팀": p["team"], "리그": league,
            "경기": g, "이닝": ip, "승": wins, "패": losses, "세이브": saves,
            "평균자책": f"{era:.2f}", "탈삼진": so, "WHIP": f"{whip:.2f}", "WAR": war
        }
        st.session_state.career_stats.append(stat_record)
        add_log(f"[{league}] {g}경기 {ip}이닝 {wins}승 {losses}패 {saves}세이브 ERA {era:.2f} / {so}K (WAR {war})")

        if league == "KBO 1군":
            if war >= 7.0:
                st.session_state.awards.append(f"{p['year']} KBO MVP & 최동원상")
                add_log("🏆 압도적인 구위! KBO MVP와 최동원상을 석권했습니다!", "👑")
            elif war >= 4.8:
                st.session_state.awards.append(f"{p['year']} KBO 골든글러브(투수)")
                add_log("🥇 KBO 투수 부문 골든글러브를 수상했습니다!", "🏆")
        elif league == "MLB":
            if war >= 7.2:
                st.session_state.awards.append(f"{p['year']} MLB 사이영상")
                add_log("🌎 메이저리그 최고 투수의 영예! 사이영상을 수상했습니다!", "👑")
            elif war >= 4.8:
                st.session_state.awards.append(f"{p['year']} MLB 올스타 선정")
                add_log("⭐ MLB 올스타전에 출전했습니다!", "🌟")

    # ------------------------------------------
    # 국가대표 차출 이벤트 (4년 주기 국제대회)
    # ------------------------------------------
    if p["year"] in [2026, 2028, 2030, 2032, 2034, 2036, 2038, 2040]:
        tourney = "WBC(월드베이스볼클래식)" if p["year"] % 4 == 2 else "아시안게임 / 프리미어12"
        if ovr >= 73 or (league == "MLB" and ovr >= 68):
            add_log(f"🇰🇷 대한민국 야구 국가대표팀({tourney})에 발탁되었습니다!", "🇰🇷")
            if random.random() < 0.45:
                st.session_state.awards.append(f"{p['year']} {tourney} 국가대표 금메달/우승")
                p["service_years"] += 1  # 국가대표 혜택으로 FA 연수 단축
                add_log(f"🏅 {tourney}에서 맹활약하며 우승을 이끌었습니다! (FA 등록일수 +1년 보너스)", "🥇")
            else:
                st.session_state.awards.append(f"{p['year']} {tourney} 국가대표 출전")
                add_log(f"🔥 {tourney} 본선 무대에서 태극마크를 달고 투혼을 불살랐습니다.", "🇰🇷")

    # ------------------------------------------
    # 연봉 갱신 및 이적/FA/MLB 포스팅 체크
    # ------------------------------------------
    if league != "KBO 퓨처스(2군)":
        p["service_years"] += 1

    # 연봉 상승 로직
    last_war = stat_record["WAR"]
    if league == "KBO 퓨처스(2군)":
        p["salary"] = 3000  # 만원 단위
    elif league == "KBO 1군":
        raise_amt = int(max(-2000, last_war * 4500))
        p["salary"] = max(3500, p["salary"] + raise_amt)
    elif league == "MLB":
        # MLB는 달러(만 달러 단위 환산 표기: 1억 = 10,000만원 기준 통일)
        raise_amt = int(max(-50000, last_war * 180000))
        p["salary"] = max(100000, p["salary"] + raise_amt)

    p["total_earnings"] += p["salary"]

    # 오프시즌 대형 이벤트 트리거
    if league == "KBO 1군":
        # 7년차 이상 + 능력치 78 이상 -> MLB 포스팅 자격
        if p["service_years"] >= 7 and ovr >= 78 and not p.get("mlb_challenged", False):
            st.session_state.offseason_event = "MLB_POSTING"
        # 8년차마다 FA 자격
        elif p["service_years"] >= 8 and p["service_years"] % 4 == 0:
            st.session_state.offseason_event = "FA_KBO"

    # 강제 은퇴 체크 (42세 또는 능력치 42 미만)
    if p["age"] >= 42 or (p["age"] >= 35 and ovr < 45):
        st.session_state.retired = True
        add_log("구단과 팬들의 박수 속에 현역 은퇴를 선언했습니다.", "💐")

# ==========================================
# 5. 화면 렌더링: 캐릭터 생성 (시작 화면)
# ==========================================
init_game()

if not st.session_state.game_started:
    st.markdown('<div class="main-title">⚾ THE DIAMOND: 야구 선수 인생 시뮬레이션</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-title">고교 유망주부터 KBO 레전드, 태극마크, 그리고 메이저리그 명예의 전당까지 당신의 커리어를 개척하세요.</div>', unsafe_allow_html=True)

    col1, col2 = st.columns([1, 1.2], gap="large")

    with col1:
        st.subheader("1. 선수 기본 프로필")
        name = st.text_input("선수 이름", value="강백호")
        pos_label = st.selectbox("포지션 선택", list(POSITIONS.keys()))
        p_type = POSITIONS[pos_label]
        
        origin = st.radio(
            "출신 배경 (초기 보너스)",
            [
                "고졸 슈퍼루키 (나이 19세 시작 / 성장 잠재력 최상)",
                "대졸 즉시전력감 (나이 23세 시작 / 초기 능력치 +5 보너스)"
            ]
        )

    with col2:
        st.subheader("2. 초기 능력치 분배 (보너스 40 포인트)")
        st.caption("기본 능력치 45에서 시작하며, 총 40 포인트를 자유롭게 배분할 수 있습니다.")
        
        if p_type == "Batter":
            s1_name, s2_name, s3_name, s4_name = "컨택", "파워", "선구안", "주루/수비"
        else:
            s1_name, s2_name, s3_name, s4_name = "구위", "제구", "변화구", "체력"

        p1 = st.slider(f"{s1_name} 추가 포인트", 0, 25, 12)
        p2 = st.slider(f"{s2_name} 추가 포인트", 0, 25, 12)
        p3 = st.slider(f"{s3_name} 추가 포인트", 0, 25, 8)
        p4 = st.slider(f"{s4_name} 추가 포인트", 0, 25, 8)

        total_used = p1 + p2 + p3 + p4
        remaining = 40 - total_used

        if remaining == 0:
            st.success(f"포인트 배분 완료! (사용: {total_used} / 40)")
        elif remaining > 0:
            st.warning(f"남은 포인트가 {remaining}점 있습니다. 모두 분배해주세요.")
        else:
            st.error(f"포인트를 {-remaining}점 초과했습니다! 줄여주세요.")

    st.divider()
    if st.button("🚀 신인 드래프트 참가 및 커리어 시작", type="primary", use_container_width=True, disabled=(remaining != 0 or not name.strip())):
        is_univ = "대졸" in origin
        base = 50.0 if is_univ else 45.0
        start_age = 23 if is_univ else 19
        
        stats = {
            s1_name: base + p1,
            s2_name: base + p2,
            s3_name: base + p3,
            s4_name: base + p4
        }
        ovr = round(sum(stats.values()) / 4, 1)
        drafted_team = random.choice(KBO_TEAMS)
        
        # 능력치가 매우 높으면 바로 1군 합류
        start_league = "KBO 1군" if ovr >= 58 else "KBO 퓨처스(2군)"
        draft_round = "1라운드 전체 1순위" if ovr >= 58 else ("1라운드 상위 지명" if ovr >= 55 else "2~3라운드 지명")

        st.session_state.player = {
            "name": name.strip(),
            "position": pos_label,
            "type": p_type,
            "age": start_age,
            "year": 2026,
            "team": drafted_team,
            "league": start_league,
            "stats": stats,
            "salary": 3000,  # 만원
            "total_earnings": 3000,
            "service_years": 0,
            "fatigue": 0,
            "injured_games": 0,
            "mlb_challenged": False
        }
        st.session_state.game_started = True
        add_log(f"2026 KBO 신인 드래프트 {draft_round}로 '{drafted_team}'에 입단했습니다! ({start_league} 시작)", "🎊")
        st.rerun()

# ==========================================
# 6. 화면 렌더링: 은퇴 및 명예의 전당 리포트
# ==========================================
elif st.session_state.retired:
    p = st.session_state.player
    df = pd.DataFrame(st.session_state.career_stats)
    
    st.balloons()
    st.markdown(f'<div class="main-title">🏛️ {p["name"]} 선수 은퇴 헌정 리포트</div>', unsafe_allow_html=True)
    st.subheader(f"포지션: {p['position']} | 통산 누적 수입: {p['total_earnings']:,}만 원 ({p['total_earnings']/10000:.1f}억 원)")

    total_war = round(df["WAR"].sum(), 1) if not df.empty else 0.0
    awards_cnt = len(st.session_state.awards)

    # 레전드 등급 산정
    if total_war >= 75 or awards_cnt >= 6:
        grade = "👑 영구결번 & 명예의 전당 헌액 (역대 최고 레전드)"
    elif total_war >= 45 or awards_cnt >= 3:
        grade = "🏆 한국 야구사에 이름을 남긴 슈퍼스타"
    elif total_war >= 20:
        grade = "⭐ 1군에서 오랫동안 사랑받은 주전 선수"
    else:
        grade = "⚾ 끝까지 그라운드를 누빈 불굴의 프로 선수"

    st.info(f"**최종 커리어 평가:** {grade} (통산 WAR: {total_war} / 수상 및 대표팀 경력: {awards_cnt}회)")

    c1, c2 = st.columns([2, 1])
    with c1:
        st.markdown("### 📊 통산 시즌별 성적표")
        st.dataframe(df, use_container_width=True, hide_index=True)
    with c2:
        st.markdown("### 🏅 주요 수상 및 국가대표 이력")
        if st.session_state.awards:
            for aw in st.session_state.awards:
                st.write(f"- {aw}")
        else:
            st.write("수상 이력이 없습니다.")

    if st.button("🔄 새로운 야구 인생 시작하기", type="primary"):
        for key in list(st.session_state.keys()):
            del st.session_state[key]
        st.rerun()

# ==========================================
# 7. 화면 렌더링: 메인 게임 플레이 대시보드
# ==========================================
else:
    p = st.session_state.player
    ovr = get_overall(p)

    # 사이드바: 선수 프로필 & 능력치
    with st.sidebar:
        st.header(f"🧢 {p['name']} ({p['age']}세)")
        st.caption(f"{p['position']} | {p['year']} 시즌")
        
        st.metric("소속 구단 / 리그", f"{p['team']}", f"{p['league']}")
        st.metric("종합 능력치 (OVR)", f"{ovr} / 99.0")
        st.metric("현재 연봉", f"{p['salary']:,}만 원", f"누적 {p['total_earnings']/10000:.1f}억 원")
        
        st.divider()
        st.subheader("📈 세부 능력치")
        for stat_name, val in p["stats"].items():
            st.write(f"**{stat_name}**: {val:.1f}")
            st.progress(min(1.0, val / 99.0))

        st.divider()
        st.write(f"피로도: **{p['fatigue']}%** | 1군/빅리그 연차: **{p['service_years']}년**")
        if p["age"] >= 34:
            if st.button("💐 현역 은퇴 선언하기", use_container_width=True):
                st.session_state.retired = True
                add_log("스스로 정상의 자리에서 물러나 은퇴를 선택했습니다.", "💐")
                st.rerun()

    # 메인 상단 타이틀
    st.markdown(f'<div class="main-title">⚾ {p["year"]} 시즌 - {p["team"]} ({p["league"]})</div>', unsafe_allow_html=True)

    # ------------------------------------------
    # 오프시즌 특수 이벤트 (MLB 포스팅 / KBO FA)
    # ------------------------------------------
    if st.session_state.offseason_event == "MLB_POSTING":
        st.warning("🌎 **[긴급 속보] 메이저리그(MLB) 포스팅 시스템 진출 자격 획득!**")
        st.write(f"KBO 리그를 정복한 {p['name']} 선수에게 메이저리그 구단들의 영입 제안이 도착했습니다. 꿈의 무대에 도전하시겠습니까?")
        
        mlb_offer_team = random.choice(MLB_TEAMS)
        mlb_salary = int(ovr * 15000)  # 예: OVR 80 -> 120만 달러(약 12억 이상) 시작
        
        col_m1, col_m2 = st.columns(2)
        with col_m1:
            if st.button(f"✈️ MLB '{mlb_offer_team}' 진출! (연봉 {mlb_salary:,}만 원)", type="primary", use_container_width=True):
                p["team"] = mlb_offer_team
                p["league"] = "MLB"
                p["salary"] = mlb_salary
                p["mlb_challenged"] = True
                st.session_state.offseason_event = None
                add_log(f"🌎 대한민국을 넘어 메이저리그 '{mlb_offer_team}'에 전격 입단했습니다!", "✈️")
                st.rerun()
        with col_m2:
            if st.button(f"🇰🇷 원소속팀 '{p['team']}' 잔류 (초대형 다년 계약)", use_container_width=True):
                p["salary"] = int(p["salary"] * 1.6)
                p["mlb_challenged"] = True
                st.session_state.offseason_event = None
                add_log(f"팬들과의 의리를 지키며 '{p['team']}' 잔류를 선언했습니다! (연봉 대폭 인상)", "🤝")
                st.rerun()

    elif st.session_state.offseason_event == "FA_KBO":
        st.info("💼 **[오프시즌 FA] 자유계약선수(FA) 자격을 취득했습니다!**")
        new_team = random.choice([t for t in KBO_TEAMS if t != p["team"]])
        fa_salary = int(max(p["salary"] * 1.4, ovr * 1200))
        
        col_f1, col_f2 = st.columns(2)
        with col_f1:
            if st.button(f"✍️ '{new_team}'으로 FA 이적 (연봉 {fa_salary:,}만 원)", type="primary", use_container_width=True):
                p["team"] = new_team
                p["salary"] = fa_salary
                st.session_state.offseason_event = None
                add_log(f"💼 FA 대박! '{new_team}' 유니폼으로 갈아입었습니다!", "✍️")
                st.rerun()
        with col_f2:
            if st.button(f"🏠 원소속팀 '{p['team']}' 재계약 (연봉 {int(fa_salary*0.95):,}만 원)", use_container_width=True):
                p["salary"] = int(fa_salary * 0.95)
                st.session_state.offseason_event = None
                add_log(f"🏠 원소속팀 '{p['team']}'과 FA 재계약을 체결했습니다.", "🤝")
                st.rerun()

    # ------------------------------------------
    # 일반 시즌 진행 컨트롤 패널
    # ------------------------------------------
    else:
        with st.container(border=True):
            st.subheader("🏋️ 비시즌 훈련 및 시즌 진행")
            c_train1, c_train2, c_btn = st.columns([1.2, 1.5, 1.3])
            
            with c_train1:
                focus_stat = st.selectbox("집중 육성 능력치", list(p["stats"].keys()))
            with c_train2:
                intensity = st.selectbox(
                    "훈련 강도 선택",
                    [
                        "표준 시즌 준비 (균형 잡힌 훈련)",
                        "지옥의 특훈 (폭풍 성장 / 부상 위험 높음)",
                        "가벼운 컨디셔닝 (부상 위험 낮음)"
                    ]
                )
            with c_btn:
                st.write("")
                st.write("")
                if st.button("⚾ 훈련 완료 및 시즌 시뮬레이션", type="primary", use_container_width=True):
                    train_player(focus_stat, intensity)
                    simulate_season()
                    st.rerun()

    # ------------------------------------------
    # 하단 탭: 커리어 로그 / 통산 성적표 / 수상 내역
    # ------------------------------------------
    tab1, tab2, tab3 = st.tabs(["📰 커리어 타임라인 (뉴스)", "📊 시즌별 통산 기록", "🏆 수상 및 국가대표 이력"])

    with tab1:
        log_html = "<div class='log-box'>" + "<br>".join(st.session_state.logs) + "</div>"
        st.markdown(log_html, unsafe_allow_html=True)

    with tab2:
        if st.session_state.career_stats:
            df_stats = pd.DataFrame(st.session_state.career_stats)
            st.dataframe(df_stats, use_container_width=True, hide_index=True)
            
            # WAR 추이 차트
            st.caption("시즌별 WAR(대체 선수 대비 승리 기여도) 추이")
            chart_df = df_stats[["연도", "WAR"]].set_index("연도")
            st.line_chart(chart_df)
        else:
            st.info("아직 치른 시즌이 없습니다. 상단 버튼을 눌러 첫 시즌을 시작해보세요!")

    with tab3:
        if st.session_state.awards:
            for aw in st.session_state.awards:
                st.success(f"🏅 {aw}")
        else:
            st.write("아직 수상 내역이나 국가대표 선발 기록이 없습니다. 능력치를 키워 타이틀에 도전하세요!")

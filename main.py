import pandas as pd
import plotly.graph_objects as go
import streamlit as st

# -----------------------------------------------------------------------------
# 1. 페이지 기본 설정 및 제목
# -----------------------------------------------------------------------------
st.set_page_config(
    page_title="우리 동네 인구 피라미드", page_icon="👨‍👩‍👧‍👦", layout="wide"
)

st.title("👨‍👩‍👧‍👦 우리 동네 인구 피라미드")
st.caption(
    "전국 읍·면·동의 연령별·성별 인구 구조를 따뜻하고 한눈에 보기 쉽게 보여드립니다."
)


# -----------------------------------------------------------------------------
# 2. 데이터 불러오기 및 캐싱
# -----------------------------------------------------------------------------
# st.cache_data를 사용해 데이터를 매번 다시 받지 않고 속도를 높입니다.
@st.cache_data
def load_data():
    url = "https://raw.githubusercontent.com/first2022-cyber/contents/main/population_ts_yearly_gender.zip"
    # pandas는 zip 파일 안의 csv를 자동으로 압축 해제해서 읽습니다.
    df = pd.read_csv(url)

    # 데이터에 존재하는 가장 최신 연도만 추출합니다.
    latest_year = df["연도"].max()
    df_latest = df[df["연도"] == latest_year].copy()

    return df_latest, latest_year


with st.spinner("데이터를 불러오는 중입니다... 잠시만 기다려주세요! ☕"):
    df, latest_year = load_data()


# -----------------------------------------------------------------------------
# 3. 사이드바 / 화면 상단 드롭다운 선택 메뉴 (시도 → 시군구 → 동)
# -----------------------------------------------------------------------------
st.write(f"📅 **기준 연도:** {latest_year}년 최신 데이터")

col1, col2, col3 = st.columns(3)

with col1:
    sido_list = sorted(df["시도"].dropna().unique())
    selected_sido = st.selectbox("1. 시·도 선택", sido_list)

with col2:
    # 선택한 시·도에 해당하는 시군구만 필터링
    df_sido = df[df["시도"] == selected_sido]
    sigungu_list = sorted(df_sido["시군구"].dropna().unique())
    selected_sigungu = st.selectbox("2. 시·군·구 선택", sigungu_list)

with col3:
    # 선택한 시군구에 해당하는 동만 필터링
    df_sigungu = df_sido[df_sido["시군구"] == selected_sigungu]
    dong_list = sorted(df_sigungu["동"].dropna().unique())
    selected_dong = st.selectbox("3. 읍·면·동 선택", dong_list)


# -----------------------------------------------------------------------------
# 4. 선택한 동네 데이터 추출 및 인구 피라미드용 데이터 가공
# -----------------------------------------------------------------------------
# 선택한 동네의 행 1개 가져오기
target_row = df_sigungu[df_sigungu["동"] == selected_dong].iloc[0]

# 0세부터 100세 이상까지 나이 라벨 리스트 생성 (0세, 1세, ... 99세, 100세 이상)
age_labels = [f"{i}세" for i in range(100)] + ["100세 이상"]

# 해당 열 이름(남_0세, 여_0세 등)에서 인구수 추출
male_pop = [target_row[f"남_{age}"] for age in age_labels]
female_pop = [target_row[f"여_{age}"] for age in age_labels]

# 남자는 피라미드 왼쪽에 배치해야 하므로 음수로 변환
male_pop_neg = [-val for val in male_pop]

# 지역 전체 총인구수 계산
total_pop = sum(male_pop) + sum(female_pop)


# -----------------------------------------------------------------------------
# 5. Plotly 가로 막대 그래프 (인구 피라미드) 생성
# -----------------------------------------------------------------------------
fig = go.Figure()

# (1) 남자 막대 그래프 (왼쪽, 음수 값)
fig.add_trace(
    go.Bar(
        y=age_labels,
        x=male_pop_neg,
        name="남성",
        orientation="h",
        marker=dict(color="#5B9BD5"),  # 부드러운 파란색
        hoverinfo="text",
        # 마우스 호버 시 양수 인구수 표시
        hovertext=[
            f"<b>{age} 남성</b>: {val:,}명"
            for age, val in zip(age_labels, male_pop)
        ],
    )
)

# (2) 여자 막대 그래프 (오른쪽, 양수 값)
fig.add_trace(
    go.Bar(
        y=age_labels,
        x=female_pop,
        name="여성",
        orientation="h",
        marker=dict(color="#ED7D31"),  # 따뜻한 주황색
        hoverinfo="text",
        hovertext=[
            f"<b>{age} 여성</b>: {val:,}명"
            for age, val in zip(age_labels, female_pop)
        ],
    )
)

# (3) 그래프 레이아웃 및 세로축 순서 고정 설정
# x축의 음수 눈금을 보기 좋게 양수 형태 라벨로 바꿔주기 위해 최대 인구값 찾기
max_val = max(max(male_pop), max(female_pop))
# 적절한 눈금 간격 설정
tick_step = max(1, max_val // 4)
tick_vals = list(range(-((max_val // tick_step) + 1) * tick_step, max_val + tick_step, tick_step))
tick_text = [f"{abs(v):,}" for v in tick_vals]

fig.update_layout(
    title=dict(
        text=f"🏡 <b>{selected_sido} {selected_sigungu} {selected_dong}</b> 인구 피라미드 (총 {total_pop:,}명)",
        font=dict(size=20),
        x=0.5,  # 중앙 정렬
    ),
    barmode="relative",  # 두 막대를 중앙 기준으로 양옆 배치
    bargap=0.1,  # 막대 간격
    height=800,  # 100개 이상의 나이 축을 위해 높이를 넉넉히 설정
    font=dict(family="Nanum Gothic, Malgun Gothic, sans-serif"),
    # 가로축(인구수) 설정
    xaxis=dict(
        title="인구수 (명)",
        tickvals=tick_vals,
        ticktext=tick_text,
        gridcolor="#E5E5E5",
    ),
    # 세로축(나이) 설정: 순서를 0세(아래) ~ 100세 이상(위)으로 명시적 지정
    yaxis=dict(
        title="연령",
        type="category",  # 범주형 데이터 처리
        categoryorder="array",  # 배열 순서 그대로 반영
        categoryarray=age_labels,  # 0세부터 100세 이상까지의 리스트 지정
        dtick=5,  # 5세 단위로 눈금 표시하여 깔끔하게 정렬
    ),
    legend=dict(
        orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1
    ),
    plot_bgcolor="white",
)


# -----------------------------------------------------------------------------
# 6. 스트림릿 화면에 출력
# -----------------------------------------------------------------------------
st.plotly_chart(fig, use_container_width=True)

# 주요 정보 요약 카드
col_m, col_f, col_t = st.columns(3)
col_m.metric("🙋‍♂️ 남성 인구수", f"{sum(male_pop):,}명")
col_f.metric("🙋‍♀️ 여성 인구수", f"{sum(female_pop):,}명")
col_t.metric("🏠 전체 인구수", f"{total_pop:,}명")

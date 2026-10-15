import streamlit as st
import pandas as pd
import plotly.graph_objects as go

# -----------------------------------------------------------------------------
# 1. 페이지 기본 설정 및 스타일 정의
# -----------------------------------------------------------------------------
st.set_page_config(
    page_title="동네별 인구 피라미드",
    page_icon="👨‍👩‍👧‍👦",
    layout="wide"
)

# 따뜻하고 친근한 분위기를 위한 CSS 스타일 적용
st.markdown("""
    <style>
    .main {
        background-color: #FFFDF9;
    }
    .stTitle {
        color: #8B5E3C;
        font-family: 'Malgun Gothic', sans-serif;
    }
    </style>
""", unsafe_allow_html=True)

st.title("👨‍👩‍👧‍👦 우리 동네 인구 피라미드")
st.write("원하는 지역(시도 ➔ 시군구 ➔ 읍·면·동)을 선택하여 연령별 인구 구조를 확인해보세요!")

# -----------------------------------------------------------------------------
# 2. 데이터 불러오기 (캐싱 처리로 속도 최적화)
# -----------------------------------------------------------------------------
@st.cache_data
def load_data():
    # GitHub 저장소의 zip 원본 파일(raw stream) URL 지정
    url = "https://github.com/swan153/pop/raw/main/population_ts_yearly_gender.zip"
    
    # pandas는 zip 파일 내부의 CSV를 자동으로 압축 해제하여 읽을 수 있습니다.
    df = pd.read_csv(url)
    
    # 데이터셋 내 가장 최신 연도 추출 및 해당 연도 데이터만 필터링
    latest_year = df['연도'].max()
    df_latest = df[df['연도'] == latest_year].copy()
    
    return df_latest, latest_year

# 데이터 로딩 실행
with st.spinner("데이터를 불러오는 중입니다... 잠시만 기다려주세요 ☕"):
    df, latest_year = load_data()

st.caption(f"📅 현재 표시되는 데이터 기준 연도: **{latest_year}년**")

# -----------------------------------------------------------------------------
# 3. 드롭다운 선택 상자 (시도 ➔ 시군구 ➔ 동)
# -----------------------------------------------------------------------------
col_sido, col_sigungu, col_dong = st.columns(3)

with col_sido:
    sido_list = sorted(df['시도'].dropna().unique())
    selected_sido = st.selectbox("1. 시·도 선택", sido_list)

# 선택된 시·도에 해당하는 시군구만 필터링
df_sido = df[df['시도'] == selected_sido]

with col_sigungu:
    sigungu_list = sorted(df_sido['시군구'].dropna().unique())
    selected_sigungu = st.selectbox("2. 시·군·구 선택", sigungu_list)

# 선택된 시군구에 해당하는 동만 필터링
df_sigungu = df_sido[df_sido['시군구'] == selected_sigungu]

with col_dong:
    dong_list = sorted(df_sigungu['동'].dropna().unique())
    selected_dong = st.selectbox("3. 읍·면·동 선택", dong_list)

# 최종 선택된 동네의 데이터 1행 추출
selected_row = df_sigungu[df_sigungu['동'] == selected_dong].iloc[0]

# -----------------------------------------------------------------------------
# 4. 연령별 데이터 추출 및 주요 지표 계산
# -----------------------------------------------------------------------------
# 나이 라벨 생성 (0세, 1세, ..., 99세, 100세 이상)
age_labels = [f"{i}세" for i in range(100)] + ["100세 이상"]

male_pop = []
female_pop = []
total_pop_by_age = []

for age in age_labels:
    male_col = f"남_{age}"
    female_col = f"여_{age}"
    
    m_val = selected_row.get(male_col, 0)
    f_val = selected_row.get(female_col, 0)
    
    # 그래프 표현용 (남성은 음수, 여성은 양수)
    male_pop.append(-m_val)
    female_pop.append(f_val)
    
    # 해당 연령 전체 인구수 계산 (양수)
    total_pop_by_age.append(m_val + f_val)

# 남성/여성 총인구 합계
total_male_pop = sum([-x for x in male_pop])
total_female_pop = sum(female_pop)

# 지표 계산 1: 총인구수
total_population = sum(total_pop_by_age)

# 지표 계산 2: 평균연령 (가중평균)
weighted_age_sum = sum(i * count for i, count in enumerate(total_pop_by_age))
avg_age = (weighted_age_sum / total_population) if total_population > 0 else 0

# 지표 계산 3: 고령화율 (65세 이상 비율)
senior_population = sum(total_pop_by_age[65:])
aging_ratio = (senior_population / total_population * 100) if total_population > 0 else 0

# 지표 계산 4: 청년층 비율 (19세~34세)
youth_population = sum(total_pop_by_age[19:35])
youth_ratio = (youth_population / total_population *

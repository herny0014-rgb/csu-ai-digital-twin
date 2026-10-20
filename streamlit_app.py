import base64
import html
import time
from pathlib import Path

import streamlit as st
import streamlit.components.v1 as components


st.set_page_config(
    page_title="CSU AI 하역 디지털 트윈",
    page_icon="⚙️",
    layout="wide",
    initial_sidebar_state="collapsed",
)

if "csu_running" not in st.session_state:
    st.session_state.csu_running = False
if "actual_unloaded_tons" not in st.session_state:
    st.session_state.actual_unloaded_tons = 0.0
if "last_accumulation_time" not in st.session_state:
    st.session_state.last_accumulation_time = time.time()
if "last_unloading_rate" not in st.session_state:
    st.session_state.last_unloading_rate = 0.0
if "sim_conditions" not in st.session_state:
    st.session_state.sim_conditions = None

# 상단 로고는 프로젝트의 static 폴더 이미지를 그대로 사용한다. (임시 경로에 의존하지 않음)
LOGO_PATH = Path(__file__).parent / "static" / "posco_flow_logo_dark.png"
try:
    _logo_b64 = base64.b64encode(LOGO_PATH.read_bytes()).decode("ascii")
    LOGO_HTML = (
        f'<img class="brand-logo" src="data:image/png;base64,{_logo_b64}" '
        'alt="POSCO 포스코플로우">'
    )
except OSError:
    LOGO_HTML = ""


st.markdown(
    """
    <style>
    :root { color-scheme: dark; }
    .stApp {
        background:
            radial-gradient(circle at 50% -20%, #183c58 0, #071a2a 42%, #03101a 100%);
        color: #eef7fc;
    }
    .block-container {max-width: 1760px; padding: 4.8rem 1.5rem 2rem;}
    .app-header {display:grid; grid-template-columns:1fr auto 1fr; align-items:start;
                 min-height:78px; margin-bottom:.9rem;}
    .brand {position:static; grid-column:1; justify-self:start; margin-top:.2rem;}
    .brand-logo {display:block; width:120px; max-width:100%; height:auto;}
    .title-wrap {grid-column:2; text-align:center; min-width:0;}
    .page-title {color:#fff; font-size:2.25rem; font-weight:900;
                 line-height:1.2; margin:0;}
    .page-sub {color:#7fa8bf; font-size:.78rem;
               letter-spacing:.18em; margin:.3rem 0 0;}
    div[data-testid="stRadio"], div[data-testid="stSlider"] {
        background:#071d2e; border:1px solid #21465d; border-radius:10px;
        padding:.55rem .8rem .15rem;
    }
    div[data-testid="stTextInput"], div[data-testid="stNumberInput"] {
        background:#071d2e; border:1px solid #21465d; border-radius:10px;
        padding:.55rem .8rem .45rem;
    }
    div[data-testid="stTextInput"] input,
    div[data-testid="stNumberInput"] input {
        background:#091f30 !important; color:#eef7fc !important;
        border-color:#2a536b !important;
    }
    div[data-testid="stNumberInput"] button {
        background:#0c2a3f !important; color:#eef7fc !important;
        border-color:#2a536b !important;
    }
    .stButton > button {
        width:100%; min-height:48px; color:#fff; font-weight:850;
        background:linear-gradient(180deg,#16435f,#0a263a);
        border:1px solid #377697; border-radius:9px;
    }
    .stButton > button:hover {border-color:#65c6ff; color:#fff;}
    div[data-testid="stMetric"] {
        background:linear-gradient(180deg,#0b263a,#061925);
        border:1px solid #244c64; border-radius:10px; padding:14px;
    }
    h1,h2,h3,p,label {color:#eaf5fb !important;}
    @media (max-width: 860px) {
        .app-header {grid-template-columns:1fr; justify-items:center; gap:.6rem;}
        .brand, .title-wrap {grid-column:1; justify-self:center;}
        .page-title {font-size:1.6rem;}
    }
    .reco-card {border:1px solid #377697; border-radius:12px; padding:18px 22px;
                background:linear-gradient(180deg,#0b263a,#061925); margin:.2rem 0 .6rem;}
    .reco-badge {display:inline-block; padding:3px 10px; border:1px solid #d99120;
                 border-radius:12px; color:#ffd06b; background:#4a3109;
                 font-size:.8rem; font-weight:800;}
    .reco-label {color:#8eb4c9; font-size:.95rem; margin-top:.55rem;}
    .reco-value {color:#fff; font-size:3.2rem; font-weight:900; line-height:1.1;}
    .reco-value span {font-size:1.3rem; color:#8eb4c9; margin-left:.35rem;}
    .reco-basis {margin:.7rem 0 0; padding-left:1.2rem; color:#cfe4f0;
                 font-size:.9rem; line-height:1.7;}
    </style>
    <div class="app-header">
      <div class="brand" translate="no">__BRAND_LOGO__</div>
      <div class="title-wrap">
        <div class="page-title">CSU AI 하역 디지털 트윈</div>
        <div class="page-sub" translate="no">CSU · AI 하역 디지털 트윈</div>
      </div>
    </div>
    """.replace("__BRAND_LOGO__", LOGO_HTML),
    unsafe_allow_html=True,
)


BRAND_UNLOADING_STATS = {
    "Gemini": (127_780, 25_092),
    "SMT": (56_574, 21_581),
    "Karembe": (241_708, 21_451),
    "Ouaco": (2_473_611, 20_197),
    "Poya": (1_106_634, 18_868),
    "Nakety": (180_745, 18_300),
    "NGO": (368_634, 16_905),
    "Kouaoua": (599_028, 16_858),
    "Ivory Coast": (59_640, 15_254),
    "Poya, Ouaco": (170_013, 14_824),
    "TontoutaOuinne": (62_421, 10_836),
}

# 최근 2년 브랜드별 하역실적을 바탕으로 만든 발표용 AI 추천 운전값이다.
BRAND_AI_PROFILES = {
    "Gemini": {"depth": 67, "bucket": 82, "boom": 88, "feeder": 92, "gantry": 94},
    "SMT": {"depth": 66, "bucket": 79, "boom": 85, "feeder": 89, "gantry": 91},
    "Karembe": {"depth": 65, "bucket": 78, "boom": 84, "feeder": 88, "gantry": 90},
    "Ouaco": {"depth": 64, "bucket": 75, "boom": 82, "feeder": 86, "gantry": 88},
    "Poya": {"depth": 62, "bucket": 71, "boom": 79, "feeder": 83, "gantry": 85},
    "Nakety": {"depth": 61, "bucket": 69, "boom": 77, "feeder": 81, "gantry": 83},
    "NGO": {"depth": 60, "bucket": 66, "boom": 75, "feeder": 79, "gantry": 81},
    "Kouaoua": {"depth": 60, "bucket": 66, "boom": 74, "feeder": 78, "gantry": 80},
    "Ivory Coast": {"depth": 59, "bucket": 63, "boom": 72, "feeder": 76, "gantry": 78},
    "Poya, Ouaco": {"depth": 58, "bucket": 61, "boom": 70, "feeder": 74, "gantry": 76},
    "TontoutaOuinne": {"depth": 56, "bucket": 55, "boom": 65, "feeder": 69, "gantry": 71},
}
DEFAULT_AI_PROFILE = {"depth": 62, "bucket": 72, "boom": 80, "feeder": 84, "gantry": 86}
OVERALL_AVERAGE_DAILY_RATE = 19_114
REFERENCE_CSU_COUNT = 2
EFFECTIVE_OPERATING_HOURS_PER_DAY = 12.0
UNLOADING_RATE_CALIBRATION_FACTOR = 0.42


def render_chute_blockage_conditions() -> tuple[int, float, int]:
    """슈트 막힘 이력·조건을 입력받고 경고와 참고용 손실량을 보여 준다.

    입력값은 가상 설정값이며, 기본 하역량과 추천 하역률에서는 차감하지 않는다.
    """
    st.markdown("#### 슈트 막힘 이력·조건")
    with st.container(border=True):
        st.caption(
            "시뮬레이션과 함께 보여 줄 슈트 막힘 조건입니다. 현재 값은 가상 설정값이며 "
            "실제 과거 이력이 아닙니다. 브랜드별 실제 이력이 확보되면 같은 칸에 바꿔 입력합니다."
        )
        block_1, block_2, block_3 = st.columns(3)
        with block_1:
            chute_count = st.number_input(
                "슈트 막힘 횟수 (회)", min_value=0, max_value=999, value=3, step=1
            )
        with block_2:
            chute_minutes = st.number_input(
                "막힘·청소 누적 정지시간 (분)",
                min_value=0.0,
                max_value=100_000.0,
                value=45.0,
                step=5.0,
            )
        with block_3:
            chute_base_rate = st.number_input(
                "기준 하역률 (t/h)",
                min_value=0,
                max_value=10_000,
                value=1_200,
                step=50,
            )

        average_minutes = chute_minutes / chute_count if chute_count > 0 else 0.0
        estimated_loss = chute_base_rate * chute_minutes / 60.0

        if chute_count > 0:
            st.warning(
                f"⚠ 슈트 막힘 경고 · 발생 {chute_count}회 · "
                f"누적 정지 {chute_minutes:,.0f}분"
            )
        else:
            st.success("슈트 막힘 없음")

        stat_1, stat_2, stat_3, stat_4 = st.columns(4)
        stat_1.metric("슈트 막힘 횟수", f"{chute_count:,}회")
        stat_2.metric("누적 정지시간", f"{chute_minutes:,.0f}분")
        stat_3.metric("건당 평균 정지시간", f"{average_minutes:,.1f}분")
        stat_4.metric("추정 손실량 (참고)", f"{estimated_loss:,.0f} t")
        st.caption(
            "추정 손실량 = 기준 하역률 × 막힘 정지시간입니다. "
            "같은 하역률을 유지했을 때의 기회손실 추정값이며 실제 미하역량이 아닙니다. "
            "추천 하역률과 시뮬레이션 하역량에서는 차감하지 않습니다."
        )
    return int(chute_count), float(chute_minutes), int(chute_base_rate)


# 1. 브랜드 선택
st.markdown("#### 브랜드 선택")
brand_col, brand_input_col, brand_info_col = st.columns([1.4, 1.4, 3.2])
with brand_col:
    selected_brand = st.selectbox(
        "니켈 브랜드 기준",
        ["직접 입력", *BRAND_UNLOADING_STATS.keys()],
        key="selected_brand",
    )
with brand_input_col:
    custom_brand = st.text_input(
        "화물 브랜드 직접 입력",
        value="",
        placeholder="목록에 없는 브랜드",
        max_chars=40,
        disabled=(selected_brand != "직접 입력"),
    )

cargo_brand = custom_brand.strip() if selected_brand == "직접 입력" else selected_brand
selected_total_tons, selected_daily_rate = BRAND_UNLOADING_STATS.get(
    selected_brand,
    (0, OVERALL_AVERAGE_DAILY_RATE),
)

with brand_info_col:
    if selected_brand == "직접 입력":
        st.info(
            "직접 입력 브랜드는 전체 평균 19,114 T/D, "
            "CSU 1대 12시간 기준 9,557톤으로 계산합니다."
        )
    else:
        st.info(
            f"최근 2년 실적 · 총 {selected_total_tons:,}t · "
            f"24h 기준 {selected_daily_rate:,} T/D · "
            f"CSU 1대 12h 기준 {selected_daily_rate / REFERENCE_CSU_COUNT:,.0f}톤"
        )

# 2. 슈트 막힘 이력·조건
chute_count, chute_minutes, chute_base_rate = render_chute_blockage_conditions()

# 3. 시뮬레이션 실행
current_conditions = {
    "brand": selected_brand,
    "cargo_brand": cargo_brand,
    "chute_count": chute_count,
    "chute_minutes": chute_minutes,
    "chute_base_rate": chute_base_rate,
}
if st.button("▶ 시뮬레이션 실행", use_container_width=True):
    # 실행할 때마다 조건을 새로 확정하고 누적값을 처음부터 다시 센다.
    st.session_state.sim_conditions = current_conditions
    st.session_state.csu_running = True
    st.session_state.actual_unloaded_tons = 0.0
    st.session_state.last_accumulation_time = time.time()
    st.session_state.last_unloading_rate = 0.0

sim_conditions = st.session_state.sim_conditions
if sim_conditions is not None and sim_conditions != current_conditions:
    st.warning(
        "입력 조건이 바뀌었습니다. '시뮬레이션 실행'을 누르면 새 조건으로 갱신됩니다. "
        "아래 결과는 이전 실행 조건 기준입니다."
    )

# 아래 결과와 시뮬레이션은 마지막으로 실행한 조건만 사용한다.
active_conditions = sim_conditions or current_conditions
sim_brand = active_conditions["brand"]
sim_cargo_brand = active_conditions["cargo_brand"]
sim_has_history = sim_brand in BRAND_UNLOADING_STATS
brand_total_tons, brand_reference_daily = BRAND_UNLOADING_STATS.get(
    sim_brand,
    (0, OVERALL_AVERAGE_DAILY_RATE),
)
brand_reference_hourly = brand_reference_daily / 24
brand_reference_per_csu = brand_reference_daily / REFERENCE_CSU_COUNT
brand_performance_factor = brand_reference_daily / OVERALL_AVERAGE_DAILY_RATE
brand_ai_profile = BRAND_AI_PROFILES.get(sim_brand, DEFAULT_AI_PROFILE)


# 브랜드별 발표용 운전값에서 시뮬레이션 설정값을 정한다.
digging_depth = brand_ai_profile["depth"]
bucket_speed = brand_ai_profile["bucket"]
preliminary_fill = int(
    max(15, min(100, 18 + digging_depth * 0.92 - bucket_speed * 0.08))
)
if preliminary_fill >= 80:
    digging_depth = max(20, digging_depth - 8)
elif preliminary_fill <= 55:
    digging_depth = min(95, digging_depth + 7)
bucket_fill_rate = int(
    max(15, min(100, 18 + digging_depth * 0.92 - bucket_speed * 0.08))
)
material_supply = bucket_fill_rate
boom_speed = brand_ai_profile["boom"]
feeder_speed = brand_ai_profile["feeder"]
gantry_speed = brand_ai_profile["gantry"]

running = st.session_state.csu_running and bucket_speed > 0
conveyor_running = running

if running:
    # 호퍼 로드셀의 측정 중량을 먼저 산출하고,
    # 교정된 피더 배출계수를 적용해 순간 하역량을 계산한다.
    hopper_load = min(50.0, material_supply * 0.43 + bucket_speed * 0.045)
    feeder_discharge_coefficient = 0.86
    conveyor_line_ready = boom_speed > 0 and feeder_speed > 0 and gantry_speed > 0
    unloading = (
        hopper_load
        * bucket_speed
        * feeder_discharge_coefficient
        * brand_performance_factor
        * UNLOADING_RATE_CALIBRATION_FACTOR
        if conveyor_line_ready else 0.0
    )
    motor_load = min(100.0, 16 + bucket_speed * 0.66 + material_supply * 0.14)
    bucket_torque = min(100.0, 14 + bucket_speed * 0.58 + material_supply * 0.17)
    boom_motor_load = (
        min(100.0, 12 + boom_speed * 0.55 + material_supply * 0.12)
        if boom_speed > 0 else 0.0
    )
    boom_torque = (
        min(100.0, 10 + boom_speed * 0.45 + material_supply * 0.14)
        if boom_speed > 0 else 0.0
    )
    feeder_motor_load = (
        min(100.0, 15 + feeder_speed * 0.58 + hopper_load * 0.50)
        if feeder_speed > 0 else 0.0
    )
    feeder_torque = (
        min(100.0, 12 + feeder_speed * 0.50 + hopper_load * 0.65)
        if feeder_speed > 0 else 0.0
    )
    gantry_motor_load = (
        min(100.0, 10 + gantry_speed * 0.52 + unloading / 100)
        if gantry_speed > 0 else 0.0
    )
    gantry_torque = (
        min(100.0, 9 + gantry_speed * 0.45 + unloading / 120)
        if gantry_speed > 0 else 0.0
    )
    loadcell_status = "시뮬레이션 값 · 실제 계측값 아님"
else:
    unloading = motor_load = bucket_torque = hopper_load = 0.0
    boom_motor_load = boom_torque = 0.0
    feeder_motor_load = feeder_torque = 0.0
    gantry_motor_load = gantry_torque = 0.0
    loadcell_status = "시뮬레이션 대기"

# 최근 2년 브랜드 실적을 CSU 1대·12시간 기준으로 환산한 고정 비교값이다.
# 현재 운전조건에 따라 변하는 값은 unloading(t/h)만 사용한다.
daily_unloading = brand_reference_per_csu

# 직전 화면 갱신 이후의 하역량을 누적한다. 다시 실행하면 처음부터 다시 센다.
accumulation_now = time.time()
accumulation_seconds = max(
    0.0,
    accumulation_now - st.session_state.last_accumulation_time,
)
st.session_state.actual_unloaded_tons += (
    st.session_state.last_unloading_rate * accumulation_seconds / 3600.0
)
st.session_state.last_accumulation_time = accumulation_now
st.session_state.last_unloading_rate = unloading if conveyor_running else 0.0
actual_unloaded = st.session_state.actual_unloaded_tons


# 4. 추천 하역률 및 추천 근거
st.markdown("#### 추천 하역률")
if not running:
    st.info(
        "시뮬레이션 실행 전입니다. '시뮬레이션 실행'을 누르면 "
        "선택한 브랜드 기준의 참고 하역률이 표시됩니다."
    )
else:
    sim_chute_count = active_conditions["chute_count"]
    sim_chute_minutes = active_conditions["chute_minutes"]
    sim_chute_average = sim_chute_minutes / sim_chute_count if sim_chute_count > 0 else 0.0
    safe_sim_brand_label = html.escape(sim_cargo_brand or "미입력")
    if sim_has_history:
        reco_badge = "가상 조건 기반 참고값"
        reco_brand_line = (
            f"기준 브랜드: {safe_sim_brand_label} · 최근 2년 평균 "
            f"{brand_reference_daily:,} T/D · 총 {brand_total_tons:,}t "
            "(집계 원본 재검증 필요)"
        )
    else:
        reco_badge = "이력 부족 · 전체 평균 기준 참고값"
        reco_brand_line = (
            f"기준 브랜드: {safe_sim_brand_label} · 브랜드 실적 없음 → "
            f"전체 평균 {OVERALL_AVERAGE_DAILY_RATE:,} T/D 기준"
        )
    if sim_chute_count > 0:
        reco_chute_line = (
            f"막힘 조건(가상값): {sim_chute_count}회 · 누적 {sim_chute_minutes:,.0f}분 · "
            f"건당 평균 {sim_chute_average:.1f}분 → 이번 추천 수치에는 반영하지 않음"
        )
    else:
        reco_chute_line = "막힘 조건(가상값): 막힘 없음 → 이번 추천 수치에는 반영하지 않음"
    st.markdown(
        '<div class="reco-card">'
        f'<span class="reco-badge">{reco_badge}</span>'
        '<div class="reco-label">추천 하역률 (참고)</div>'
        f'<div class="reco-value">{unloading:,.0f}<span>t/h</span></div>'
        '<ul class="reco-basis">'
        f"<li>{reco_brand_line}</li>"
        f"<li>{reco_chute_line}</li>"
        "<li>산출 방식: 브랜드별 발표용 운전값을 기존 시뮬레이션 식에 넣은 결과입니다. "
        "실제 막힘 이력으로 학습·검증한 추천이 아닙니다.</li>"
        "</ul>"
        "</div>",
        unsafe_allow_html=True,
    )


animation_state = "running" if running else "paused"
cycle_seconds = max(0.62, 3.1 - bucket_speed * 0.024)
boom_cycle_seconds = max(0.55, 3.0 - boom_speed * 0.023)
feeder_cycle_seconds = max(0.55, 3.0 - feeder_speed * 0.023)
gantry_cycle_seconds = max(0.55, 3.0 - gantry_speed * 0.023)
boom_animation_state = "running" if conveyor_running and boom_speed > 0 else "paused"
feeder_animation_state = "running" if conveyor_running and feeder_speed > 0 else "paused"
gantry_animation_state = "running" if conveyor_running and gantry_speed > 0 else "paused"
boom_luff_state = "running" if running else "paused"
be_depth_offset = round((digging_depth - 60) * 0.35, 1)

status_text = "시뮬레이션 실행 중" if running else "시뮬레이션 대기"
status_color = "#2bd477" if running else "#ffad42"

safe_cargo_brand = html.escape(sim_cargo_brand or "미입력")

digital_twin_html = f"""
<!doctype html>
<html lang="ko">
<head>
<meta charset="utf-8">
<style>
*{{box-sizing:border-box}}
html,body{{margin:0;background:#04121d;font-family:Arial,'Malgun Gothic',sans-serif;color:#eef7fb}}
.scene{{position:relative;height:690px;overflow:hidden;border:1px solid #28546d;border-radius:14px;
background:radial-gradient(circle at 54% 38%,rgba(31,93,124,.22),transparent 38%),
linear-gradient(#071c2c 0 72%,#08283a 72% 82%,#0a1720 82%);box-shadow:inset 0 0 70px #0008}}
.grid{{position:absolute;inset:0;opacity:.16;background-image:linear-gradient(#4f789733 1px,transparent 1px),
linear-gradient(90deg,#4f789733 1px,transparent 1px);background-size:36px 36px}}
.topline{{position:absolute;left:20px;right:20px;top:16px;display:flex;justify-content:space-between;z-index:5}}
.route{{font-size:12px;color:#b5cddb;letter-spacing:.03em;white-space:nowrap;
display:flex;align-items:center;gap:10px;overflow-x:auto;min-width:0;padding:8px 0}}
.route span{{flex:0 0 auto}} .route-arrow{{color:#ffad42;font-size:18px;font-weight:800}}
.route-title{{color:#83a9bd;margin-right:6px}}
.state{{padding:8px 15px;border:1px solid {status_color};border-radius:18px;color:{status_color};
background:#061b29dd;font-weight:800}}
.panel{{position:absolute;z-index:5;width:156px;padding:13px;border:1px solid #29516a;border-radius:9px;
background:linear-gradient(#0a2639ee,#061925ee);box-shadow:0 8px 24px #0006}}
.left{{left:16px;top:73px}} .right{{right:16px;top:73px}}
.k{{font-size:10px;color:#82a8bd;margin-top:9px}} .v{{font-size:18px;font-weight:850;margin:3px 0 9px}}
.good{{color:#51e993}} .accent{{color:#ffad42}} .decision{{font-size:11px;line-height:1.45;color:#70eaa1}}
.machine{{position:absolute;left:160px;right:160px;top:56px;width:calc(100% - 320px);height:550px}}
.steel{{fill:url(#steel);stroke:#132e1d;stroke-width:3}} .steel2{{fill:url(#steel2);stroke:#132e1d;stroke-width:3}}
.truss{{fill:none;stroke:#557a58;stroke-width:7;stroke-linecap:round}}
.cable{{fill:none;stroke:#879ba5;stroke-width:2.2}}
.deck{{fill:#182f3b;stroke:#486779;stroke-width:2}}
.cargo{{fill:none;stroke:#ef861c;stroke-width:7;stroke-linecap:round;stroke-dasharray:11 12;
animation:flow {cycle_seconds}s linear infinite;animation-play-state:{animation_state}}}
.cargo-sm{{fill:none;stroke:#ef861c;stroke-width:7;stroke-linecap:round;stroke-dasharray:11 12;
animation:flow {cycle_seconds}s linear infinite;animation-play-state:{animation_state}}}
.boom-cargo{{animation-duration:{boom_cycle_seconds}s;animation-play-state:{boom_animation_state}}}
.feeder-cargo{{animation-duration:{feeder_cycle_seconds}s;animation-play-state:{feeder_animation_state}}}
.gantry-cargo{{animation-duration:{gantry_cycle_seconds}s;animation-play-state:{gantry_animation_state}}}
.drop{{fill:none;stroke:#ef861c;stroke-width:7;stroke-linecap:round;stroke-dasharray:11 12;
animation:fall .62s linear infinite;animation-play-state:{animation_state}}}
.boom-drop{{animation-duration:{max(0.35, boom_cycle_seconds * 0.35)}s;animation-play-state:{boom_animation_state}}}
.feeder-drop{{animation-duration:{max(0.35, feeder_cycle_seconds * 0.35)}s;animation-play-state:{feeder_animation_state}}}
.gantry-drop{{animation-duration:{max(0.35, gantry_cycle_seconds * 0.35)}s;animation-play-state:{gantry_animation_state}}}
.bucket{{fill:url(#gold);stroke:#633800;stroke-width:2}}
.bucketset{{offset-path:path("M344 480 L344 128 A31 31 0 0 1 406 128 L406 490 C446 550 358 588 330 542 Q302 514 344 480 Z");
offset-anchor:0px 0px;offset-rotate:auto 90deg;
animation:bucketLoop {cycle_seconds * 8:.3f}s linear infinite;animation-play-state:{animation_state}}}
.chain{{fill:none;stroke:#182820;stroke-width:17;stroke-linejoin:round}}
.chain-link{{fill:none;stroke:#9caf97;stroke-width:3;stroke-dasharray:5 12}}
.direction{{fill:none;stroke:#ef861c;stroke-width:7;stroke-linecap:round;marker-end:url(#direction-arrow)}}
.be-depth{{transform:translateY({be_depth_offset}px);
animation:digDepth 4.5s ease-in-out infinite;animation-play-state:{boom_luff_state}}}
.lbl{{fill:#061725eF;stroke:#6d8998;stroke-width:1}} .txt{{fill:#f3f8fa;font-size:11px;font-weight:700}}
@keyframes flow{{to{{stroke-dashoffset:-92}}}}
@keyframes fall{{to{{stroke-dashoffset:-64}}}}
@keyframes bucketLoop{{from{{offset-distance:0%}}to{{offset-distance:100%}}}}
@keyframes digDepth{{0%,100%{{transform:translateY({be_depth_offset}px)}}
50%{{transform:translateY({be_depth_offset + 24}px)}}}}
.bottom{{position:absolute;left:176px;right:176px;bottom:13px;display:grid;grid-template-columns:repeat(6,1fr);gap:8px}}
.tile{{padding:10px 12px;border:1px solid #29516a;border-radius:8px;background:#071d2ddd}}
.tn{{font-size:9px;color:#82a8bd}} .tv{{font-size:17px;font-weight:850;margin-top:3px}}
</style>
</head>
<body>
<div class="scene">
<div class="grid"></div>
<div class="topline"><div class="route" aria-label="원료 이송 흐름도">
<span class="route-title">원료 이송 흐름도</span><span>선창(Ship Hold)</span><span class="route-arrow">→</span>
<span>BE/Bucket Elevator</span><span class="route-arrow">→</span><span>BOOM BC</span><span class="route-arrow">→</span>
<span>FEEDER BC</span><span class="route-arrow">→</span><span>GANTRY BC</span><span class="route-arrow">→</span><span>A801</span></div>
<div class="state">● {status_text}</div></div>

<div class="panel left">
  <div class="k">시뮬레이션 상태</div><div class="v">{"실행 중" if running else "대기"}</div>
  <div class="k">화물 브랜드</div><div class="v">{safe_cargo_brand}</div>
  <div class="k">브랜드 기준 하역량 (CSU 1대·12h)</div><div class="v">{brand_reference_per_csu:,.0f} t</div>
  <div class="k">하역량</div><div class="v" id="scene-rate">{unloading:,.0f} t/h</div>
  <div class="k">브랜드 기준 일 하역량</div><div class="v" id="scene-dayrate">{daily_unloading:,.0f} t/day</div>
  <div class="k">누적 하역량 (시뮬레이션)</div><div class="v" id="actual-unloaded">{actual_unloaded:.1f} t</div>
  <div class="k">호퍼 로드셀</div><div class="v accent">{hopper_load:.1f} t</div>
  <div class="k">{loadcell_status}</div>
</div>
<div class="panel right">
  <div class="k">시뮬레이션 설정</div><div class="v good">가상 조건</div>
  <div class="k">버켓 속도</div><div class="v">{bucket_speed} %</div>
  <div class="k">디깅 깊이 / 버켓 적재율</div>
  <div class="v">{digging_depth} / {bucket_fill_rate} %</div>
  <div class="k">BOOM / FEEDER / GANTRY</div>
  <div class="v">{boom_speed} / {feeder_speed} / {gantry_speed} %</div>
  <div class="k">비고</div><div class="decision">브랜드별 발표용 운전값 기준 · 실제 계측값이 아닙니다</div>
</div>

<svg class="machine" viewBox="0 0 1400 620" preserveAspectRatio="xMidYMid meet">
<defs>
 <marker id="direction-arrow" viewBox="0 0 10 10" refX="8" refY="5" markerUnits="userSpaceOnUse" markerWidth="13" markerHeight="13" orient="auto-start-reverse">
  <path d="M0 0 L10 5 L0 10 Z" fill="#ef861c"/>
 </marker>
 <linearGradient id="steel" x1="0" y1="0" x2="1" y2="1">
  <stop offset="0" stop-color="#173b25"/><stop offset=".28" stop-color="#57784d"/>
  <stop offset=".5" stop-color="#98a67b"/><stop offset=".72" stop-color="#4a754a"/>
  <stop offset="1" stop-color="#142f1f"/>
 </linearGradient>
 <linearGradient id="steel2"><stop stop-color="#294d31"/><stop offset=".5" stop-color="#66825a"/>
  <stop offset="1" stop-color="#203e29"/></linearGradient>
 <linearGradient id="gold"><stop stop-color="#7a4200"/><stop offset=".5" stop-color="#e39518"/>
  <stop offset="1" stop-color="#714000"/></linearGradient>
 <linearGradient id="hull" x1="0" y1="0" x2="0" y2="1"><stop stop-color="#394c57"/>
  <stop offset="1" stop-color="#111c23"/></linearGradient>
</defs>

<!-- Bulk carrier -->
<path d="M0 480 L365 480 L420 510 L386 570 L72 570 L18 535 Z" fill="url(#hull)" stroke="#0b1217" stroke-width="4"/>
<path d="M52 550 L391 550 L382 570 L72 570 Z" fill="#7e2928"/>
<rect x="148" y="438" width="220" height="43" fill="#13191d" stroke="#5c6970" stroke-width="4"/>
<path d="M153 477 Q182 440 214 472 Q250 431 286 472 Q327 439 366 477Z" fill="#875126"/>
<rect x="25" y="390" width="74" height="90" fill="#d4dde1" stroke="#52616a" stroke-width="3"/>
<rect x="35" y="372" width="54" height="22" fill="#dbe4e8" stroke="#52616a" stroke-width="3"/>
<rect x="45" y="410" width="12" height="10" fill="#20465c"/><rect x="64" y="410" width="12" height="10" fill="#20465c"/>
<rect x="108" y="402" width="27" height="78" fill="#414b51"/><rect x="108" y="392" width="27" height="18" fill="#af3b34"/>
<text x="205" y="530" fill="#edf4f7" font-size="18" font-weight="bold"
      letter-spacing="2">NICKEL</text>

<g class="be-depth">
<!-- BE DRIVE / vertical BE / curved BE DIGGING closed bucket circuit -->
<path d="M326 157 L422 157 L422 490 L433 526 Q424 573 371 575 Q329 574 312 537 L315 504 L326 480 Z" class="steel"/>
<path d="M317 86 L428 86 L452 118 L430 170 L326 170 L305 137Z" class="steel"/>
<circle cx="375" cy="128" r="30" fill="#17241d" stroke="#87988a" stroke-width="5"/>
<circle cx="375" cy="128" r="12" fill="#84928a"/>
<circle cx="375" cy="535" r="29" fill="#17241d" stroke="#87988a" stroke-width="5"/>
<circle cx="375" cy="535" r="11" fill="#84928a"/>
<path d="M344 480 L344 128 A31 31 0 0 1 406 128 L406 490 C446 550 358 588 330 542 Q302 514 344 480 Z" class="chain"/>
<path d="M344 480 L344 128 A31 31 0 0 1 406 128 L406 490 C446 550 358 588 330 542 Q302 514 344 480 Z" class="chain-link"/>
<g class="bucketset" style="animation-delay:-{cycle_seconds * 8 * 0 / 18:.3f}s"><path d="M-16 -8 H14 L11 8 Q0 18 -13 10 Z" class="bucket"/></g>
<g class="bucketset" style="animation-delay:-{cycle_seconds * 8 * 1 / 18:.3f}s"><path d="M-16 -8 H14 L11 8 Q0 18 -13 10 Z" class="bucket"/></g>
<g class="bucketset" style="animation-delay:-{cycle_seconds * 8 * 2 / 18:.3f}s"><path d="M-16 -8 H14 L11 8 Q0 18 -13 10 Z" class="bucket"/></g>
<g class="bucketset" style="animation-delay:-{cycle_seconds * 8 * 3 / 18:.3f}s"><path d="M-16 -8 H14 L11 8 Q0 18 -13 10 Z" class="bucket"/></g>
<g class="bucketset" style="animation-delay:-{cycle_seconds * 8 * 4 / 18:.3f}s"><path d="M-16 -8 H14 L11 8 Q0 18 -13 10 Z" class="bucket"/></g>
<g class="bucketset" style="animation-delay:-{cycle_seconds * 8 * 5 / 18:.3f}s"><path d="M-16 -8 H14 L11 8 Q0 18 -13 10 Z" class="bucket"/></g>
<g class="bucketset" style="animation-delay:-{cycle_seconds * 8 * 6 / 18:.3f}s"><path d="M-16 -8 H14 L11 8 Q0 18 -13 10 Z" class="bucket"/></g>
<g class="bucketset" style="animation-delay:-{cycle_seconds * 8 * 7 / 18:.3f}s"><path d="M-16 -8 H14 L11 8 Q0 18 -13 10 Z" class="bucket"/></g>
<g class="bucketset" style="animation-delay:-{cycle_seconds * 8 * 8 / 18:.3f}s"><path d="M-16 -8 H14 L11 8 Q0 18 -13 10 Z" class="bucket"/></g>
<g class="bucketset" style="animation-delay:-{cycle_seconds * 8 * 9 / 18:.3f}s"><path d="M-16 -8 H14 L11 8 Q0 18 -13 10 Z" class="bucket"/></g>
<g class="bucketset" style="animation-delay:-{cycle_seconds * 8 * 10 / 18:.3f}s"><path d="M-16 -8 H14 L11 8 Q0 18 -13 10 Z" class="bucket"/></g>
<g class="bucketset" style="animation-delay:-{cycle_seconds * 8 * 11 / 18:.3f}s"><path d="M-16 -8 H14 L11 8 Q0 18 -13 10 Z" class="bucket"/></g>
<g class="bucketset" style="animation-delay:-{cycle_seconds * 8 * 12 / 18:.3f}s"><path d="M-16 -8 H14 L11 8 Q0 18 -13 10 Z" class="bucket"/></g>
<g class="bucketset" style="animation-delay:-{cycle_seconds * 8 * 13 / 18:.3f}s"><path d="M-16 -8 H14 L11 8 Q0 18 -13 10 Z" class="bucket"/></g>
<g class="bucketset" style="animation-delay:-{cycle_seconds * 8 * 14 / 18:.3f}s"><path d="M-16 -8 H14 L11 8 Q0 18 -13 10 Z" class="bucket"/></g>
<g class="bucketset" style="animation-delay:-{cycle_seconds * 8 * 15 / 18:.3f}s"><path d="M-16 -8 H14 L11 8 Q0 18 -13 10 Z" class="bucket"/></g>
<g class="bucketset" style="animation-delay:-{cycle_seconds * 8 * 16 / 18:.3f}s"><path d="M-16 -8 H14 L11 8 Q0 18 -13 10 Z" class="bucket"/></g>
<g class="bucketset" style="animation-delay:-{cycle_seconds * 8 * 17 / 18:.3f}s"><path d="M-16 -8 H14 L11 8 Q0 18 -13 10 Z" class="bucket"/></g>
<!-- Single cargo centerline; mechanical bucket circuit remains unchanged -->
<path d="M350 550 Q400 575 400 535 Q400 505 375 480 L375 160 Q405 160 442 195" class="cargo"/>
<path d="M309 413 L309 388" class="direction"/>

<!-- BE rotary mechanism -->
<ellipse cx="438" cy="181" rx="48" ry="15" class="steel2"/>
<rect x="421" y="169" width="68" height="34" rx="5" class="steel2"/>
</g>

<!-- BOOM and BOOM BC -->
<path d="M414 171 L1010 179 L1005 231 L414 220Z" class="steel"/>
<path d="M1005 179 L1200 132 L1210 174 L1005 231Z" class="steel"/>
<path d="M435 195 L761 195" class="cargo boom-cargo"/>
<path d="M495 211 L520 211" class="direction"/>

<!-- Forestay -->
<path d="M735 177 L760 25 L786 177" class="truss"/>
<path d="M760 30 L420 177 M760 30 L1155 149" class="truss"/>

<!-- Central slew structure -->
<path d="M710 220 L808 220 L828 392 L695 392Z" class="steel"/>
<ellipse cx="760" cy="220" rx="68" ry="19" class="steel2"/>
<ellipse cx="761" cy="389" rx="76" ry="21" class="steel2"/>

<!-- Visible BOOM BC vertical drop to FEEDER BC -->
<path d="M761 195 L761 430" class="drop boom-drop"/>
<path d="M790 292 L790 317" class="direction"/>

<!-- Gantry frame -->
<path d="M686 382 L730 382 L681 555 L635 555Z" class="steel"/>
<path d="M817 382 L861 382 L912 555 L866 555Z" class="steel"/>
<path d="M690 397 L880 536 M845 397 L655 536" class="truss"/>

<!-- FEEDER BC -->
<path d="M690 405 L1053 405 L1068 453 L674 453Z" class="steel2"/>
<path d="M761 430 L938 430" class="cargo-sm feeder-cargo"/>
<path d="M938 430 L938 513" class="drop feeder-drop"/>
<path d="M971 417 L996 417" class="direction"/>

<!-- GANTRY BC -->
<rect x="720" y="490" width="470" height="46" rx="3" class="steel2"/>
<path d="M938 513 L1176 513" class="cargo-sm gantry-cargo"/>
<path d="M1040 500 L1065 500" class="direction"/>
<rect x="745" y="536" width="13" height="42" fill="#466d49"/>
<rect x="1148" y="536" width="13" height="42" fill="#466d49"/>
<path d="M1176 513 L1176 574" class="drop gantry-drop"/>
<path d="M1200 536 L1200 554" class="direction"/>
<!-- TRAVEL and land BC -->
<rect x="620" y="548" width="112" height="24" class="steel2"/>
<rect x="842" y="548" width="112" height="24" class="steel2"/>
<circle cx="648" cy="579" r="15" fill="#1b2427"/><circle cx="695" cy="579" r="15" fill="#1b2427"/>
<circle cx="870" cy="579" r="15" fill="#1b2427"/><circle cx="917" cy="579" r="15" fill="#1b2427"/>
<rect x="1155" y="555" width="220" height="37" class="deck"/>
<path d="M1176 574 L1360 574" class="cargo-sm gantry-cargo"/>
<path d="M1270 586 L1295 586" class="direction"/>

<!-- labels -->
<g><rect x="205" y="74" width="96" height="26" rx="4" class="lbl"/><text x="219" y="92" class="txt">BE DRIVE</text></g>
<path d="M350 339 L340 339" stroke="#7d98a7" stroke-width="1.5"/>
<g><rect x="286" y="326" width="54" height="26" rx="4" class="lbl"/><text x="303" y="344" class="txt">BE</text></g>
<path d="M440 535 L460 535" stroke="#7d98a7" stroke-width="1.5"/>
<g><rect x="460" y="522" width="100" height="26" rx="4" class="lbl"/><text x="470" y="540" class="txt">BE DIGGING</text></g>
<g><rect x="585" y="180" width="90" height="26" rx="4" class="lbl"/><text x="599" y="198" class="txt">BOOM BC</text></g>
<g><rect x="805" y="410" width="104" height="26" rx="4" class="lbl"/><text x="817" y="428" class="txt">FEEDER BC</text></g>
<g><rect x="895" y="494" width="105" height="26" rx="4" class="lbl"/><text x="907" y="512" class="txt">GANTRY BC</text></g>
<g><rect x="750" y="562" width="78" height="25" rx="4" class="lbl"/><text x="765" y="580" class="txt">TRAVEL</text></g>
<g><rect x="1250" y="526" width="82" height="26" rx="4" class="lbl"/><text x="1273" y="544" class="txt">A801</text></g>
</svg>

<div class="bottom">
 <div class="tile"><div class="tn">버켓 모터 부하</div><div class="tv">{motor_load:.1f} %</div></div>
 <div class="tile"><div class="tn">버켓 토크</div><div class="tv">{bucket_torque:.1f} %</div></div>
 <div class="tile"><div class="tn">호퍼 로드셀</div><div class="tv">{hopper_load:.1f} t</div></div>
 <div class="tile"><div class="tn">하역량</div><div class="tv" id="bottom-rate">{unloading:,.0f} t/h</div></div>
 <div class="tile"><div class="tn">브랜드 기준 일 하역량</div><div class="tv" id="bottom-dayrate">{daily_unloading:,.0f} t/day</div></div>
 <div class="tile"><div class="tn">누적 하역량 (시뮬레이션)</div><div class="tv" id="actual-bottom">{actual_unloaded:.1f} t</div></div>
</div>
</div>
<script>
let sceneActual={actual_unloaded:.6f};
let scenePrevious=Date.now();
const sceneBaseRate={unloading:.6f};
const sceneFixedDaily={brand_reference_per_csu:.6f};
window.setInterval(()=>{{
 const now=Date.now();
 const seconds=Math.max(0,(now-scenePrevious)/1000);
 scenePrevious=now;
 const sceneRate=sceneBaseRate;
 sceneActual+=sceneRate*seconds/3600;
 const value=sceneActual.toFixed(1)+" t";
 const rateValue=Math.round(sceneRate).toLocaleString()+" t/h";
 const dayValue=Math.round(sceneFixedDaily).toLocaleString()+" t/day";
 const left=document.getElementById("actual-unloaded");
 const bottom=document.getElementById("actual-bottom");
 const leftRate=document.getElementById("scene-rate");
 const leftDay=document.getElementById("scene-dayrate");
 const bottomRate=document.getElementById("bottom-rate");
 const bottomDay=document.getElementById("bottom-dayrate");
 if(left) left.textContent=value;
 if(bottom) bottom.textContent=value;
 if(leftRate) leftRate.textContent=rateValue;
 if(leftDay) leftDay.textContent=dayValue;
 if(bottomRate) bottomRate.textContent=rateValue;
 if(bottomDay) bottomDay.textContent=dayValue;
}},1000);
</script>
</body>
</html>
"""

components.html(digital_twin_html, height=710, scrolling=False)

conveyor_state_text = "시뮬레이션 실행 중" if running else "시뮬레이션 대기"
conveyor_state_class = "on" if running else "wait"
conveyor_initial = {
    "bs": boom_speed if conveyor_running else 0,
    "bml": boom_motor_load,
    "bmt": boom_torque,
    "fs": feeder_speed if conveyor_running else 0,
    "fml": feeder_motor_load,
    "fmt": feeder_torque,
    "gs": gantry_speed if conveyor_running else 0,
    "gml": gantry_motor_load,
    "gmt": gantry_torque,
}

live_data_html = f"""
<!doctype html><html lang="ko"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<style>
*{{box-sizing:border-box}}body{{margin:0;background:transparent;color:#f2f8fc;
font-family:Arial,"Malgun Gothic",sans-serif}}
h2{{font-size:21px;margin:0 0 6px;display:flex;flex-wrap:wrap;align-items:center;gap:6px 12px}}
.state{{font-size:12px;font-weight:800;padding:3px 10px;border-radius:12px;border:1px solid}}
.state.on{{color:#2bd477;border-color:#2bd477;background:#0a3a29}}
.state.wait{{color:#ffad42;border-color:#ffad42;background:#3a2a0a}}
.note{{font-size:12px;color:#a9c8d9;margin:0 0 8px}}
.tbl{{border:1px solid #29546d;border-radius:9px;overflow:hidden;
background:linear-gradient(180deg,#0a263a,#061827)}}
table{{width:100%;border-collapse:separate;border-spacing:0;table-layout:fixed}}
th,td{{padding:10px 14px;border-bottom:1px solid #1f4259}}
thead th{{font-size:13px;font-weight:800;color:#d6e9f4;background:#0e3048;
text-align:right;line-height:1.3}}
thead th:first-child,tbody th{{text-align:left}}
tbody th{{font-size:15px;font-weight:850;color:#fff}}
td{{font-size:22px;font-weight:850;color:#fff;text-align:right;
font-variant-numeric:tabular-nums}}
tbody tr:nth-child(even) th,tbody tr:nth-child(even) td{{background:#0b2b42}}
tbody tr:last-child th,tbody tr:last-child td{{border-bottom:0}}
@media (max-width:560px){{
 h2{{font-size:17px}}
 th,td{{padding:8px 6px}}
 thead th{{font-size:11px}}
 tbody th{{font-size:12px}}
 td{{font-size:17px}}
}}
</style></head><body>
<div id="wrap">
<h2>컨베이어 실시간 운전 데이터 <span class="state {conveyor_state_class}">{conveyor_state_text}</span></h2>
<div class="note">시뮬레이션 값이며 실제 설비 계측값이 아닙니다.</div>
<div class="tbl"><table>
<colgroup><col style="width:28%"><col><col><col></colgroup>
<thead><tr><th>설비</th><th>벨트 속도 (%)</th><th>모터 부하 (%)</th><th>토크 (%)</th></tr></thead>
<tbody>
<tr><th scope="row">BOOM BC</th><td id="bs">{conveyor_initial['bs']:.1f}</td><td id="bml">{conveyor_initial['bml']:.1f}</td><td id="bmt">{conveyor_initial['bmt']:.1f}</td></tr>
<tr><th scope="row">FEEDER BC</th><td id="fs">{conveyor_initial['fs']:.1f}</td><td id="fml">{conveyor_initial['fml']:.1f}</td><td id="fmt">{conveyor_initial['fmt']:.1f}</td></tr>
<tr><th scope="row">GANTRY BC</th><td id="gs">{conveyor_initial['gs']:.1f}</td><td id="gml">{conveyor_initial['gml']:.1f}</td><td id="gmt">{conveyor_initial['gmt']:.1f}</td></tr>
</tbody></table></div>
</div>
<script>
const live={str(running).lower()};
const bb={bucket_speed},bd={digging_depth},bo={boom_speed},fe={feeder_speed},ga={gantry_speed};
const brandFactor={brand_performance_factor:.6f};
const rateCalibration={UNLOADING_RATE_CALIBRATION_FACTOR:.6f};
const rateLimit={brand_reference_hourly * 1.08:.6f};
const C=(v,a,b)=>Math.max(a,Math.min(b,v)), put=(id,v)=>document.getElementById(id).textContent=v;
function tick(){{
 const p=Date.now()/3000,sw=Math.sin(p),lw=Math.sin(p*.73+1.2);
 let b=Math.round(C(bb+sw*3,30,90));
 let bs=Math.round(C(bo+sw*2,35,100));
 let fs=Math.round(C(fe+lw*3,35,100));
 let gs=Math.round(C(ga+(sw+lw)*1.5,35,100));
 let depth=Math.round(C(bd-lw*5,20,95));
 let fill=Math.round(C(18+depth*.92-b*.08,15,100));
 let hp=Math.min(50,fill*.43+b*.045-(fs-fe)*.08);
 let u=hp*b*.86*(fs/Math.max(1,fe))*brandFactor*rateCalibration;
 if(u>rateLimit){{
   b=Math.max(30,b-4);depth=Math.max(20,depth-6);
   fill=Math.round(C(18+depth*.92-b*.08,15,100));fs=Math.min(100,fs+2);
   hp=Math.min(50,fill*.43+b*.045-(fs-fe)*.08);
   u=hp*b*.86*(fs/Math.max(1,fe))*brandFactor*rateCalibration;
 }}
 const bml=Math.min(100,7+bs*.42+u/900),bmt=Math.min(100,6+bs*.35);
 const fml=Math.min(100,10+fs*.48+hp*.40),fmt=Math.min(100,8+fs*.40+hp*.50);
 const gml=Math.min(100,7+gs*.42),gmt=Math.min(100,6+gs*.35);
 put("bs",bs.toFixed(1));put("bml",bml.toFixed(1));put("bmt",bmt.toFixed(1));
 put("fs",fs.toFixed(1));put("fml",fml.toFixed(1));put("fmt",fmt.toFixed(1));
 put("gs",gs.toFixed(1));put("gml",gml.toFixed(1));put("gmt",gmt.toFixed(1));
}}
function fit(){{
 try{{
  if(window.frameElement)
   window.frameElement.style.height=(document.getElementById("wrap").offsetHeight+4)+"px";
 }}catch(e){{}}
}}
if(live){{tick();window.setInterval(tick,1000);}}
fit();window.addEventListener("resize",fit);
</script></body></html>"""
components.html(live_data_html, height=300, scrolling=False)


st.caption(
    "데모용 디지털 트윈입니다. 실제 설비 적용 전에는 현장 계측값과 제어 한계값으로 보정해야 합니다."
)

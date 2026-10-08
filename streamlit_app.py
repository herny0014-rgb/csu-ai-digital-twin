import html
import csv
import io
import math
import time
from datetime import datetime, timedelta, timezone

import streamlit as st
import streamlit.components.v1 as components


KST = timezone(timedelta(hours=9), name="KST")


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
if "training_records" not in st.session_state:
    st.session_state.training_records = []
if "recording_enabled" not in st.session_state:
    st.session_state.recording_enabled = False
if "last_record_time" not in st.session_state:
    st.session_state.last_record_time = 0.0


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
                 min-height:78px; margin-bottom:.45rem;}
    .brand {position:static; grid-column:1; justify-self:start; margin-top:.45rem;
            color:#54aef2; font-size:1.2rem; font-weight:900;
            letter-spacing:.08em; white-space:nowrap;}
    .title-wrap {grid-column:2; text-align:center; min-width:520px;}
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
    </style>
    <div class="app-header">
      <div class="brand" translate="no">POSCO FLOW</div>
      <div class="title-wrap">
        <div class="page-title">CSU AI 하역 디지털 트윈</div>
        <div class="page-sub" translate="no">CSU · AI 하역 디지털 트윈</div>
      </div>
    </div>
    """,
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


mode_col, start_col, stop_col, speed_col, material_col, cargo_col = st.columns(
    [1.05, 0.85, 0.85, 1.25, 1.25, 1.25]
)

with mode_col:
    mode = st.radio("운전 모드", ["수동", "AI 자동"], horizontal=True)

selected_brand_for_controls = st.session_state.get("selected_brand", "직접 입력")
active_ai_profile = BRAND_AI_PROFILES.get(selected_brand_for_controls, DEFAULT_AI_PROFILE)
if "bucket_speed_control" not in st.session_state:
    st.session_state.bucket_speed_control = 65
if "digging_depth_control" not in st.session_state:
    st.session_state.digging_depth_control = 65
if mode == "AI 자동":
    st.session_state.bucket_speed_control = active_ai_profile["bucket"]
    st.session_state.digging_depth_control = active_ai_profile["depth"]
with start_col:
    st.write("")
    if st.button("▶ 조업 착수", use_container_width=True):
        st.session_state.csu_running = True
        st.session_state.actual_unloaded_tons = 0.0
        st.session_state.last_accumulation_time = time.time()
        st.session_state.last_unloading_rate = 0.0
with stop_col:
    st.write("")
    if st.button("■ 조업 정지", use_container_width=True):
        st.session_state.csu_running = False
with speed_col:
    manual_speed = st.slider(
        "버켓 속도 (%)", 0, 100,
        disabled=(mode == "AI 자동"), key="bucket_speed_control"
    )
with material_col:
    manual_digging_depth = st.slider(
        "디깅 깊이 (%)", 0, 100,
        disabled=(mode == "AI 자동"), key="digging_depth_control"
    )
with cargo_col:
    ship_cargo = st.number_input(
        "선박 적재 화물량 (t)",
        min_value=1_000,
        max_value=200_000,
        value=55_000,
        step=100,
    )

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
brand_total_tons, brand_reference_daily = BRAND_UNLOADING_STATS.get(
    selected_brand,
    (0, OVERALL_AVERAGE_DAILY_RATE),
)
brand_reference_hourly = brand_reference_daily / 24
brand_reference_per_csu = brand_reference_daily / REFERENCE_CSU_COUNT
brand_performance_factor = brand_reference_daily / OVERALL_AVERAGE_DAILY_RATE
brand_ai_profile = BRAND_AI_PROFILES.get(selected_brand, DEFAULT_AI_PROFILE)

with brand_info_col:
    if selected_brand == "직접 입력":
        st.info(
            "직접 입력 브랜드는 전체 평균 19,114 T/D, "
            "CSU 1대 12시간 기준 9,557톤으로 계산합니다."
        )
    else:
        st.info(
            f"최근 2년 실적 · 총 {brand_total_tons:,}t · "
            f"24h 기준 {brand_reference_daily:,} T/D · "
            f"CSU 1대 12h 기준 {brand_reference_per_csu:,.0f}톤"
        )

st.markdown("#### 컨베이어 벨트 속도 제어")
if "boom_speed_control" not in st.session_state:
    st.session_state.boom_speed_control = 80
if "feeder_speed_control" not in st.session_state:
    st.session_state.feeder_speed_control = 75
if "gantry_speed_control" not in st.session_state:
    st.session_state.gantry_speed_control = 80
if mode == "AI 자동":
    st.session_state.boom_speed_control = brand_ai_profile["boom"]
    st.session_state.feeder_speed_control = brand_ai_profile["feeder"]
    st.session_state.gantry_speed_control = brand_ai_profile["gantry"]

boom_col, feeder_col, gantry_col = st.columns(3)
with boom_col:
    manual_boom_speed = st.slider(
        "BOOM BC 벨트 속도 (%)", 0, 100,
        disabled=(mode == "AI 자동"), key="boom_speed_control"
    )
with feeder_col:
    manual_feeder_speed = st.slider(
        "FEEDER BC 벨트 속도 (%)", 0, 100,
        disabled=(mode == "AI 자동"), key="feeder_speed_control"
    )
with gantry_col:
    manual_gantry_speed = st.slider(
        "GANTRY BC 벨트 속도 (%)", 0, 100,
        disabled=(mode == "AI 자동"), key="gantry_speed_control"
    )

st.markdown("#### 사행·편적 감지 조건")
misalignment_signal = st.slider(
    "사행·편적 감지 신호 (%)",
    0,
    100,
    15,
    help="현재는 데모 입력값이며, 실제 적용 시 좌·우 사행센서와 편적 계측값으로 대체합니다.",
)


def calculate_ai_speed(material: int) -> tuple[int, str]:
    """Demo controller using simulated load, torque, and hopper feedback."""
    trial_speed = 52.0 + material * 0.38
    trial_load = 16.0 + trial_speed * 0.66 + material * 0.14
    trial_torque = 14.0 + trial_speed * 0.58 + material * 0.17
    trial_hopper = material * 0.43 + trial_speed * 0.045

    if trial_hopper >= 41:
        return max(30, int(trial_speed - 14)), "호퍼 중량 상승 감지 · 버켓 감속"
    if trial_load >= 82:
        return max(30, int(trial_speed - 11)), "모터 부하 상승 감지 · 버켓 감속"
    if trial_torque >= 76:
        return max(30, int(trial_speed - 8)), "토크 상승 감지 · 버켓 감속"
    if trial_load < 58 and trial_hopper < 32:
        return min(90, int(trial_speed + 6)), "설비 여유 확인 · 하역량 증대"
    return min(90, max(30, int(trial_speed))), "부하·토크·호퍼 안정 · 현재 속도 유지"


if mode == "AI 자동":
    digging_depth = brand_ai_profile["depth"]
    bucket_speed = brand_ai_profile["bucket"]
    preliminary_fill = int(
        max(15, min(100, 18 + digging_depth * 0.92 - bucket_speed * 0.08))
    )
    if preliminary_fill >= 80:
        digging_depth = max(20, digging_depth - 8)
        boom_action = "버켓 적재율 상승 · 붐 UP"
    elif preliminary_fill <= 55:
        digging_depth = min(95, digging_depth + 7)
        boom_action = "버켓 적재율 부족 · 붐 DOWN"
    else:
        boom_action = "버켓 적재율 안정 · 붐 위치 유지"
    bucket_fill_rate = int(
        max(15, min(100, 18 + digging_depth * 0.92 - bucket_speed * 0.08))
    )
    material_supply = bucket_fill_rate
    boom_speed = brand_ai_profile["boom"]
    feeder_speed = brand_ai_profile["feeder"]
    gantry_speed = brand_ai_profile["gantry"]
    profile_name = selected_brand if selected_brand != "직접 입력" else "전체 평균"
    ai_decision = (
        f"{profile_name} 과거 하역특성 분석 · {boom_action} · "
        f"추천속도 BE {bucket_speed}% / BOOM {boom_speed}% / "
        f"FEEDER {feeder_speed}% / GANTRY {gantry_speed}% · "
        f"CSU 1대 12h 기준 {brand_reference_per_csu:,.0f}톤 반영"
    )
else:
    digging_depth = manual_digging_depth
    bucket_speed = manual_speed
    bucket_fill_rate = int(
        max(0, min(100, 18 + digging_depth * 0.92 - bucket_speed * 0.08))
    )
    material_supply = bucket_fill_rate
    boom_speed = manual_boom_speed
    feeder_speed = manual_feeder_speed
    gantry_speed = manual_gantry_speed
    ai_decision = "작업자 설정 속도로 운전"

if mode == "AI 자동":
    st.markdown("#### 🤖 브랜드별 AI 최적 운전 추천")
    rec_1, rec_2, rec_3, rec_4, rec_5 = st.columns(5)
    rec_1.metric("버켓 속도", f"{bucket_speed}%")
    rec_2.metric("BOOM BC", f"{boom_speed}%")
    rec_3.metric("FEEDER BC", f"{feeder_speed}%")
    rec_4.metric("GANTRY BC", f"{gantry_speed}%")
    rec_5.metric("디깅 깊이", f"{digging_depth}%")
    st.caption(
        f"{profile_name} 최근 2년 하역실적을 반영한 발표용 추천값입니다. "
        "실제 적용 시 현장 계측 데이터 학습으로 보정합니다."
    )

# 사행 위험도는 감지 신호, 버켓 적재율, 컨베이어 간 속도 편차를 함께 반영한다.
speed_imbalance = abs(boom_speed - feeder_speed) + abs(feeder_speed - gantry_speed)
misalignment_risk = int(
    max(
        0,
        min(
            100,
            misalignment_signal * 0.80
            + speed_imbalance * 0.85
            + max(0, bucket_fill_rate - 72) * 0.65,
        ),
    )
)

if misalignment_risk >= 80:
    misalignment_level = "위험"
elif misalignment_risk >= 55:
    misalignment_level = "주의"
else:
    misalignment_level = "정상"

preventive_action = "현재 속도 유지"
if mode == "AI 자동" and misalignment_risk >= 80:
    bucket_speed = max(25, bucket_speed - 12)
    boom_speed = max(25, boom_speed - 8)
    feeder_speed = max(25, feeder_speed - 10)
    gantry_speed = max(25, gantry_speed - 8)
    preventive_action = "투입량 급감속 · 전 BC 감속 · 안전 인터록 대기"
    ai_decision += (
        f" · 사행 위험 {misalignment_risk}% → 예방제어 "
        f"{bucket_speed}/{boom_speed}/{feeder_speed}/{gantry_speed}%"
    )
elif mode == "AI 자동" and misalignment_risk >= 55:
    bucket_speed = max(30, bucket_speed - 6)
    boom_speed = max(30, boom_speed - 4)
    feeder_speed = max(30, feeder_speed - 6)
    gantry_speed = max(30, gantry_speed - 4)
    preventive_action = "버켓 투입량 감소 · 컨베이어 단계 감속"
    ai_decision += (
        f" · 사행 주의 {misalignment_risk}% → 예방 감속 "
        f"{bucket_speed}/{boom_speed}/{feeder_speed}/{gantry_speed}%"
    )
elif mode == "수동" and misalignment_risk >= 55:
    preventive_action = "작업자 확인 및 감속 권고"

if mode == "AI 자동" and misalignment_risk >= 55:
    bucket_fill_rate = int(
        max(15, min(100, 18 + digging_depth * 0.92 - bucket_speed * 0.08))
    )
    material_supply = bucket_fill_rate

if "previous_bucket_speed" not in st.session_state:
    st.session_state.previous_bucket_speed = bucket_speed
if "conveyor_flush_deadline" not in st.session_state:
    st.session_state.conveyor_flush_deadline = None

previous_bucket_speed = st.session_state.previous_bucket_speed

if (
    st.session_state.csu_running
    and mode == "수동"
    and bucket_speed == 0
    and previous_bucket_speed > 0
):
    st.session_state.conveyor_flush_deadline = time.time() + 180

if bucket_speed > 0 or not st.session_state.csu_running:
    st.session_state.conveyor_flush_deadline = None

flush_deadline = st.session_state.conveyor_flush_deadline
flush_remaining = max(0, int(flush_deadline - time.time())) if flush_deadline else 0
flushing = (
    st.session_state.csu_running
    and bucket_speed == 0
    and flush_deadline is not None
    and flush_remaining > 0
)
running = st.session_state.csu_running and bucket_speed > 0
conveyor_running = running or flushing
st.session_state.previous_bucket_speed = bucket_speed

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
    loadcell_status = "로드셀 측정 중 · 하역량 연동"
elif flushing:
    remaining_ratio = flush_remaining / 180
    hopper_load = min(
        50.0,
        (material_supply * 0.43 + previous_bucket_speed * 0.045)
        * remaining_ratio,
    )
    unloading = (
        hopper_load
        * feeder_speed
        * 0.72
        * brand_performance_factor
        * UNLOADING_RATE_CALIBRATION_FACTOR
        if boom_speed > 0 and feeder_speed > 0 and gantry_speed > 0
        else 0.0
    )
    motor_load = bucket_torque = 0.0
    boom_motor_load = min(100.0, 8 + boom_speed * 0.45) if boom_speed > 0 else 0.0
    boom_torque = min(100.0, 6 + boom_speed * 0.35) if boom_speed > 0 else 0.0
    feeder_motor_load = (
        min(100.0, 10 + feeder_speed * 0.48 + hopper_load * 0.40)
        if feeder_speed > 0 else 0.0
    )
    feeder_torque = (
        min(100.0, 8 + feeder_speed * 0.40 + hopper_load * 0.50)
        if feeder_speed > 0 else 0.0
    )
    gantry_motor_load = min(100.0, 7 + gantry_speed * 0.42) if gantry_speed > 0 else 0.0
    gantry_torque = min(100.0, 6 + gantry_speed * 0.35) if gantry_speed > 0 else 0.0
    loadcell_status = "벨트 잔량 배출 중"
else:
    unloading = motor_load = bucket_torque = hopper_load = 0.0
    boom_motor_load = boom_torque = 0.0
    feeder_motor_load = feeder_torque = 0.0
    gantry_motor_load = gantry_torque = 0.0
    loadcell_status = "로드셀 대기"

estimated_hours = ship_cargo / unloading if unloading > 0 else 0.0
# 최근 2년 브랜드 실적을 CSU 1대·12시간 기준으로 환산한 고정 비교값이다.
# 현재 운전조건에 따라 변하는 값은 unloading(t/h)만 사용한다.
daily_unloading = brand_reference_per_csu

# 직전 화면 갱신 이후의 하역량을 누적한다. 정지 후에도 누적값은 유지된다.
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

if running:
    st.success(
        f"🟢 조업 중 · {mode} · 버켓 속도 {bucket_speed}% · "
        f"{loadcell_status} · AI 판단: {ai_decision}"
    )
elif flushing:
    st.warning(
        f"🟠 버켓 정지 · 컨베이어 잔량 처리 중 · "
        f"{flush_remaining // 60:02d}:{flush_remaining % 60:02d} 후 자동 정지"
    )
else:
    st.error("🔴 조업 정지 · 시뮬레이터 정지")


def render_flush_countdown() -> None:
    deadline = st.session_state.conveyor_flush_deadline
    if deadline is None:
        return

    remaining = max(0, int(deadline - time.time()))
    if remaining <= 0:
        st.session_state.conveyor_flush_deadline = None
        st.session_state.csu_running = False
        st.rerun()

    st.info(
        f"⏳ 컨베이어 잔량 처리 남은 시간 "
        f"{remaining // 60:02d}:{remaining % 60:02d} · 완료 후 자동 정지"
    )


render_flush_countdown()


def render_ai_live_control() -> None:
    """Show stable closed-loop control values."""
    if mode != "AI 자동":
        st.caption("수동 모드 · 작업자가 각 설비 속도를 직접 설정합니다.")
        return

    if not running:
        st.info("🤖 AI 자동제어 대기 · 조업 착수 후 실시간 속도 보정을 시작합니다.")
        return

    live_html = f"""
<!doctype html>
<html lang="ko">
<head>
<meta charset="utf-8">
<style>
*{{box-sizing:border-box}} body{{margin:0;background:transparent;color:#eef8ff;
font-family:Arial,"Malgun Gothic",sans-serif}}
.title{{font-size:18px;font-weight:850;margin:0 0 10px}}
.grid{{display:grid;grid-template-columns:repeat(9,1fr);gap:8px}}
.card{{min-height:70px;padding:10px 12px;border:1px solid #28536e;border-radius:9px;
background:linear-gradient(180deg,#0a263a,#061827)}}
.name{{font-size:10px;color:#8eb4c9}} .value{{margin-top:7px;font-size:20px;font-weight:850}}
.decision{{margin-top:9px;padding:9px 12px;border:1px solid #27795a;border-radius:8px;
background:#08372f;color:#75f2ac;font-size:12px;font-weight:750}}
.decision.warn{{border-color:#d99120;background:#4a3109;color:#ffd06b}}
</style>
</head>
<body>
<div class="title">🤖 AI 실시간 자동제어</div>
<div class="grid">
 <div class="card"><div class="name">버켓 속도</div><div class="value" id="bucket"></div></div>
 <div class="card"><div class="name">디깅 깊이</div><div class="value" id="depth"></div></div>
 <div class="card"><div class="name">버켓 적재율</div><div class="value" id="fill"></div></div>
 <div class="card"><div class="name">BOOM BC</div><div class="value" id="boom"></div></div>
 <div class="card"><div class="name">FEEDER BC</div><div class="value" id="feeder"></div></div>
 <div class="card"><div class="name">GANTRY BC</div><div class="value" id="gantry"></div></div>
 <div class="card"><div class="name">실시간 하역량</div><div class="value" id="rate"></div></div>
 <div class="card"><div class="name">브랜드 기준 일 하역량</div><div class="value" id="dayrate"></div></div>
 <div class="card"><div class="name">실제 누적 하역량</div><div class="value" id="actualrate"></div></div>
</div>
<div class="decision" id="decision"></div>
<script>
const baseBucket={bucket_speed}, baseDepth={digging_depth};
const baseBoom={boom_speed}, baseFeeder={feeder_speed};
const baseGantry={gantry_speed}, supply={material_supply};
const brandFactor={brand_performance_factor:.6f};
const rateCalibration={UNLOADING_RATE_CALIBRATION_FACTOR:.6f};
 const fixedDaily={brand_reference_per_csu:.6f};
const rateLimit={brand_reference_hourly * 1.08:.6f};
let actualTons={actual_unloaded:.6f}, previousTick=Date.now();
function clamp(v,a,b){{return Math.max(a,Math.min(b,v));}}
function update(){{
 const currentTick=Date.now();
 const elapsedSeconds=Math.max(0,(currentTick-previousTick)/1000);
 previousTick=currentTick;
 const phase=Date.now()/3000, sw=Math.sin(phase), lw=Math.sin(phase*.73+1.2);
 let bucket=Math.round(clamp(baseBucket+sw*3,30,90));
 let depth=Math.round(clamp(baseDepth-lw*5,20,95));
 let fill=Math.round(clamp(18+depth*.92-bucket*.08,15,100));
 const boom=Math.round(clamp(baseBoom+sw*2,35,100));
 let feeder=Math.round(clamp(baseFeeder+lw*3,35,100));
 const gantry=Math.round(clamp(baseGantry+(sw+lw)*1.5,35,100));
 let hopper=Math.min(50,fill*.43+bucket*.045-(feeder-baseFeeder)*.08);
 let rate=hopper*bucket*.86*(feeder/Math.max(1,baseFeeder))*brandFactor*rateCalibration;
 let overLimit=rate>rateLimit;
 if(overLimit){{
   bucket=Math.max(30,bucket-4);
   depth=Math.max(20,depth-6);
   fill=Math.round(clamp(18+depth*.92-bucket*.08,15,100));
   feeder=Math.min(100,feeder+2);
   hopper=Math.min(50,fill*.43+bucket*.045-(feeder-baseFeeder)*.08);
   rate=hopper*bucket*.86*(feeder/Math.max(1,baseFeeder))*brandFactor*rateCalibration;
 }}
 const load=Math.min(100,16+bucket*.66+fill*.14);
 let reason="부하 안정 → 최적 하역량 유지";
 if(overLimit) reason="⚠ 하역량 기준 초과 → 붐 UP·버켓 감속·FEEDER BC 자동제어 진행";
 else if(hopper>=40){{depth=Math.max(20,depth-3);reason="호퍼 중량 상승 → 붐 UP·FEEDER 증속";}}
 else if(load>=80) reason="BE DRIVE 부하 상승 → 버켓 속도 미세 감속";
 else if(hopper<30){{depth=Math.min(95,depth+3);reason="버켓 적재율 부족 → 붐 DOWN·디깅 깊이 증가";}}
 document.getElementById("bucket").textContent=bucket+" %";
 document.getElementById("depth").textContent=depth+" %";
 document.getElementById("fill").textContent=fill+" %";
 document.getElementById("boom").textContent=boom+" %";
 document.getElementById("feeder").textContent=feeder+" %";
 document.getElementById("gantry").textContent=gantry+" %";
 document.getElementById("rate").textContent=Math.round(rate).toLocaleString()+" t/h";
 document.getElementById("dayrate").textContent=Math.round(fixedDaily).toLocaleString()+" t/day";
 actualTons+=rate*elapsedSeconds/3600;
 document.getElementById("actualrate").textContent=actualTons.toFixed(1)+" t";
 const decision=document.getElementById("decision");
 decision.className=overLimit?"decision warn":"decision";
 decision.textContent="AI 판단: "+reason+" · BE DRIVE 부하 "+load.toFixed(1)+"%";
}}
update(); window.setInterval(update,1000);
</script>
</body>
</html>
"""
    components.html(live_html, height=175, scrolling=False)


render_ai_live_control()


st.subheader("⚠️ 사행·편적 AI 예방감시")
risk_1, risk_2, risk_3, risk_4 = st.columns(4)
risk_1.metric("사행 위험도", f"{misalignment_risk} %")
risk_2.metric("위험 등급", misalignment_level)
risk_3.metric("감지 신호", f"{misalignment_signal} %")
risk_4.metric("AI 예방조치", preventive_action)

if misalignment_level == "위험":
    st.error(
        f"🔴 사행 위험 {misalignment_risk}% · {preventive_action} · "
        "현장 안전 인터록과 운전자 확인이 우선입니다."
    )
elif misalignment_level == "주의":
    st.warning(f"🟡 사행 주의 {misalignment_risk}% · {preventive_action}")
else:
    st.success(f"🟢 사행 정상 {misalignment_risk}% · 편적 상태 안정")


animation_state = "running" if running else "paused"
cycle_seconds = max(0.62, 3.1 - bucket_speed * 0.024)
boom_cycle_seconds = max(0.55, 3.0 - boom_speed * 0.023)
feeder_cycle_seconds = max(0.55, 3.0 - feeder_speed * 0.023)
gantry_cycle_seconds = max(0.55, 3.0 - gantry_speed * 0.023)
boom_animation_state = "running" if conveyor_running and boom_speed > 0 else "paused"
feeder_animation_state = "running" if conveyor_running and feeder_speed > 0 else "paused"
gantry_animation_state = "running" if conveyor_running and gantry_speed > 0 else "paused"
boom_luff_state = "running" if mode == "AI 자동" and running else "paused"
be_depth_offset = round((digging_depth - 60) * 0.35, 1)

flush_stop_script = ""
if flushing:
    flush_stop_script = f"""
<script>
window.setTimeout(() => {{
  const twin = document.querySelector(".twin");
  if (twin) twin.classList.add("flush-complete");
}}, {max(0, flush_remaining) * 1000});
</script>
"""
status_text = "조업 중" if running else ("잔량 처리 중" if flushing else "조업 정지")
status_color = "#2bd477" if running else ("#ffad42" if flushing else "#ef5b5b")

safe_mode = html.escape(mode)
safe_decision = html.escape(ai_decision)
safe_cargo_brand = html.escape(cargo_brand.strip() or "미입력")

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
.flush-complete .cargo,
.flush-complete .cargo-sm,
.flush-complete .drop,
.flush-complete .bucketset{{animation-play-state:paused!important}}
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
  <div class="k">운전 모드</div><div class="v">{safe_mode}</div>
  <div class="k">화물 브랜드</div><div class="v">{safe_cargo_brand}</div>
  <div class="k">브랜드 기준 하역량 (CSU 1대·12h)</div><div class="v">{brand_reference_per_csu:,.0f} t</div>
  <div class="k">선박 적재 화물량</div><div class="v">{ship_cargo:,.0f} t</div>
  <div class="k">하역량</div><div class="v" id="scene-rate">{unloading:,.0f} t/h</div>
  <div class="k">브랜드 기준 일 하역량</div><div class="v" id="scene-dayrate">{daily_unloading:,.0f} t/day</div>
  <div class="k">실제 누적 하역량</div><div class="v" id="actual-unloaded">{actual_unloaded:.1f} t</div>
  <div class="k">예상 하역시간</div><div class="v">{estimated_hours:.1f} h</div>
  <div class="k">호퍼 로드셀</div><div class="v accent">{hopper_load:.1f} t</div>
  <div class="k">{loadcell_status}</div>
</div>
<div class="panel right">
  <div class="k">AI CONTROL</div><div class="v good">{safe_mode}</div>
  <div class="k">버켓 속도</div><div class="v">{bucket_speed} %</div>
  <div class="k">디깅 깊이 / 버켓 적재율</div>
  <div class="v">{digging_depth} / {bucket_fill_rate} %</div>
  <div class="k">BOOM / FEEDER / GANTRY</div>
  <div class="v">{boom_speed} / {feeder_speed} / {gantry_speed} %</div>
  <div class="k">AI 판단</div><div class="decision">{safe_decision}</div>
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
 <div class="tile"><div class="tn">실제 누적 하역량</div><div class="tv" id="actual-bottom">{actual_unloaded:.1f} t</div></div>
</div>
</div>
<script>
let sceneActual={actual_unloaded:.6f};
let scenePrevious=Date.now();
const sceneBaseRate={unloading:.6f};
const sceneManual={str(mode == "수동" and running).lower()};
const sceneFixedDaily={brand_reference_per_csu:.6f};
window.setInterval(()=>{{
 const now=Date.now();
 const seconds=Math.max(0,(now-scenePrevious)/1000);
 scenePrevious=now;
 const phase=now/3000;
 const sceneRate=sceneBaseRate*(sceneManual ? 1+Math.sin(phase)*.025+Math.sin(phase*.71+1.1)*.012 : 1);
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
{flush_stop_script}
</body>
</html>
"""

components.html(digital_twin_html, height=710, scrolling=False)

if running:
    live_data_html = f"""
<!doctype html><html lang="ko"><head><meta charset="utf-8">
<style>
*{{box-sizing:border-box}}body{{margin:0;background:transparent;color:#f2f8fc;
font-family:Arial,"Malgun Gothic",sans-serif}}
h2{{font-size:21px;margin:0 0 12px}}h3{{font-size:15px;margin:13px 0 8px}}
.grid6{{display:grid;grid-template-columns:repeat(6,1fr);gap:10px}}
.grid3{{display:grid;grid-template-columns:repeat(3,1fr);gap:10px}}
.card{{min-height:70px;padding:11px;border:1px solid #29546d;border-radius:9px;
background:linear-gradient(180deg,#0a263a,#061827)}}
.name{{font-size:10px;color:#91b4c8}}.value{{font-size:21px;font-weight:850;margin-top:7px}}
</style></head><body>
<h2>실시간 운전 데이터</h2>
<div class="grid6">
 <div class="card"><div class="name">하역량</div><div class="value" id="u"></div></div>
 <div class="card"><div class="name">브랜드 기준 일 하역량</div><div class="value" id="ud"></div></div>
 <div class="card"><div class="name">실제 누적 하역량</div><div class="value" id="ua"></div></div>
 <div class="card"><div class="name">버켓 모터 부하</div><div class="value" id="bl"></div></div>
 <div class="card"><div class="name">버켓 토크</div><div class="value" id="bt"></div></div>
 <div class="card"><div class="name">호퍼 로드셀</div><div class="value" id="hp"></div></div>
</div>
<h2 style="margin-top:18px">컨베이어 실시간 운전 데이터</h2>
<h3>BOOM BC</h3><div class="grid3">
 <div class="card"><div class="name">BOOM BC 벨트 속도</div><div class="value" id="bs"></div></div>
 <div class="card"><div class="name">BOOM BC 모터 부하</div><div class="value" id="bml"></div></div>
 <div class="card"><div class="name">BOOM BC 토크</div><div class="value" id="bmt"></div></div>
</div>
<h3>FEEDER BC</h3><div class="grid3">
 <div class="card"><div class="name">FEEDER BC 벨트 속도</div><div class="value" id="fs"></div></div>
 <div class="card"><div class="name">FEEDER BC 모터 부하</div><div class="value" id="fml"></div></div>
 <div class="card"><div class="name">FEEDER BC 토크</div><div class="value" id="fmt"></div></div>
</div>
<h3>GANTRY BC</h3><div class="grid3">
 <div class="card"><div class="name">GANTRY BC 벨트 속도</div><div class="value" id="gs"></div></div>
 <div class="card"><div class="name">GANTRY BC 모터 부하</div><div class="value" id="gml"></div></div>
 <div class="card"><div class="name">GANTRY BC 토크</div><div class="value" id="gmt"></div></div>
</div>
<script>
const bb={bucket_speed},bd={digging_depth},bo={boom_speed},fe={feeder_speed},ga={gantry_speed};
const brandFactor={brand_performance_factor:.6f};
const rateCalibration={UNLOADING_RATE_CALIBRATION_FACTOR:.6f};
const aiMode={str(mode == "AI 자동").lower()};
const fixedDaily={brand_reference_per_csu:.6f};
const rateLimit={brand_reference_hourly * 1.08:.6f};
const C=(v,a,b)=>Math.max(a,Math.min(b,v)), put=(id,v)=>document.getElementById(id).textContent=v;
let accumulated={actual_unloaded:.6f},previous=Date.now();
function tick(){{
 const now=Date.now(),elapsed=Math.max(0,(now-previous)/1000);previous=now;
 const p=Date.now()/3000,sw=Math.sin(p),lw=Math.sin(p*.73+1.2);
 let b=aiMode?Math.round(C(bb+sw*3,30,90)):bb;
 let bs=aiMode?Math.round(C(bo+sw*2,35,100)):bo;
 let fs=aiMode?Math.round(C(fe+lw*3,35,100)):fe;
 let gs=aiMode?Math.round(C(ga+(sw+lw)*1.5,35,100)):ga;
 let depth=aiMode?Math.round(C(bd-lw*5,20,95)):bd;
 let fill=Math.round(C(18+depth*.92-b*.08,15,100));
 let hp=Math.min(50,fill*.43+b*.045-(fs-fe)*.08);
 let u=hp*b*.86*(fs/Math.max(1,fe))*brandFactor*rateCalibration;
 if(!aiMode) u*=1+sw*.025+lw*.012;
 if(aiMode && u>rateLimit){{
   b=Math.max(30,b-4);depth=Math.max(20,depth-6);
   fill=Math.round(C(18+depth*.92-b*.08,15,100));fs=Math.min(100,fs+2);
   hp=Math.min(50,fill*.43+b*.045-(fs-fe)*.08);
   u=hp*b*.86*(fs/Math.max(1,fe))*brandFactor*rateCalibration;
 }}
 const bl=Math.min(100,16+b*.66+fill*.14),bt=Math.min(100,14+b*.58+fill*.18);
 const bml=Math.min(100,7+bs*.42+u/900),bmt=Math.min(100,6+bs*.35);
 const fml=Math.min(100,10+fs*.48+hp*.40),fmt=Math.min(100,8+fs*.40+hp*.50);
 const gml=Math.min(100,7+gs*.42),gmt=Math.min(100,6+gs*.35);
 accumulated+=u*elapsed/3600;
 put("u",Math.round(u).toLocaleString()+" t/h");put("ud",Math.round(fixedDaily).toLocaleString()+" t/day");
 put("ua",accumulated.toFixed(1)+" t");
 put("bl",bl.toFixed(1)+" %");
 put("bt",bt.toFixed(1)+" %");put("hp",hp.toFixed(1)+" t");
 put("bs",bs+" %");put("bml",bml.toFixed(1)+" %");put("bmt",bmt.toFixed(1)+" %");
 put("fs",fs+" %");put("fml",fml.toFixed(1)+" %");put("fmt",fmt.toFixed(1)+" %");
 put("gs",gs+" %");put("gml",gml.toFixed(1)+" %");put("gmt",gmt.toFixed(1)+" %");
}}
tick();window.setInterval(tick,1000);
</script></body></html>"""
    components.html(live_data_html, height=520, scrolling=False)
else:
    st.subheader("실시간 운전 데이터")
    metric_1, metric_2, metric_3, metric_4, metric_5, metric_6 = st.columns(6)
    metric_1.metric("하역량", f"{unloading:,.0f} t/h")
    metric_2.metric("브랜드 기준 일 하역량", f"{daily_unloading:,.0f} t/day")
    metric_3.metric("실제 누적 하역량", f"{actual_unloaded:.1f} t")
    metric_4.metric("버켓 모터 부하", f"{motor_load:.1f} %")
    metric_5.metric("버켓 토크", f"{bucket_torque:.1f} %")
    metric_6.metric("호퍼 로드셀", f"{hopper_load:.1f} t")

    st.subheader("컨베이어 실시간 운전 데이터")
    st.markdown("##### BOOM BC")
    boom_1, boom_2, boom_3 = st.columns(3)
    boom_1.metric("BOOM BC 벨트 속도", f"{boom_speed if conveyor_running else 0} %")
    boom_2.metric("BOOM BC 모터 부하", f"{boom_motor_load:.1f} %")
    boom_3.metric("BOOM BC 토크", f"{boom_torque:.1f} %")

    st.markdown("##### FEEDER BC")
    feeder_1, feeder_2, feeder_3 = st.columns(3)
    feeder_1.metric("FEEDER BC 벨트 속도", f"{feeder_speed if conveyor_running else 0} %")
    feeder_2.metric("FEEDER BC 모터 부하", f"{feeder_motor_load:.1f} %")
    feeder_3.metric("FEEDER BC 토크", f"{feeder_torque:.1f} %")

    st.markdown("##### GANTRY BC")
    gantry_1, gantry_2, gantry_3 = st.columns(3)
    gantry_1.metric("GANTRY BC 벨트 속도", f"{gantry_speed if conveyor_running else 0} %")
    gantry_2.metric("GANTRY BC 모터 부하", f"{gantry_motor_load:.1f} %")
    gantry_3.metric("GANTRY BC 토크", f"{gantry_torque:.1f} %")


def make_training_record(excellent: bool = False) -> dict[str, object]:
    """현재 디지털 트윈 상태를 AI 학습용 한 행으로 만든다."""
    now = time.time()
    wave = math.sin(now / 3.0)
    slow_wave = math.sin(now / 4.7 + 1.1)
    live_rate = unloading * (1.0 + wave * 0.025 + slow_wave * 0.012) if running else 0.0
    live_hopper = max(0.0, hopper_load + wave * 0.35) if running else 0.0

    return {
        "기록시각": datetime.now(KST).strftime("%Y-%m-%d %H:%M:%S"),
        "데이터출처": "디지털 트윈 자동기록",
        "조업일자": datetime.now(KST).strftime("%Y-%m-%d"),
        "화물브랜드": cargo_brand or "미입력",
        "운전모드": mode,
        "조업상태": "조업 중" if running else "조업 정지",
        "우수운전": "Y" if excellent else "N",
        "버켓속도_pct": round(bucket_speed + (wave * 2 if mode == "AI 자동" and running else 0), 1),
        "디깅깊이_pct": round(digging_depth - (slow_wave * 3 if mode == "AI 자동" and running else 0), 1),
        "버켓적재율_pct": round(bucket_fill_rate + (slow_wave * 1.5 if running else 0), 1),
        "BE모터부하_pct": round(motor_load + (wave * 0.6 if running else 0), 1),
        "BE토크_pct": round(bucket_torque + (slow_wave * 0.6 if running else 0), 1),
        "BOOM_BC속도_pct": boom_speed if conveyor_running else 0,
        "BOOM_BC모터부하_pct": round(boom_motor_load, 1),
        "BOOM_BC토크_pct": round(boom_torque, 1),
        "FEEDER_BC속도_pct": feeder_speed if conveyor_running else 0,
        "FEEDER_BC모터부하_pct": round(feeder_motor_load, 1),
        "FEEDER_BC토크_pct": round(feeder_torque, 1),
        "GANTRY_BC속도_pct": gantry_speed if conveyor_running else 0,
        "GANTRY_BC모터부하_pct": round(gantry_motor_load, 1),
        "GANTRY_BC토크_pct": round(gantry_torque, 1),
        "호퍼로드셀_t": round(live_hopper, 2),
        "실시간하역량_tph": round(live_rate, 1),
        "브랜드기준하역량_12h_t": round(brand_reference_per_csu, 1),
        "실제누적하역량_t": round(actual_unloaded, 2),
        "사행감지신호_pct": misalignment_signal,
        "사행위험도_pct": misalignment_risk,
        "사행위험등급": misalignment_level,
        "AI예방조치": preventive_action,
        "AI판단": ai_decision,
    }


def records_to_csv(records: list[dict[str, object]]) -> bytes:
    """엑셀에서 한글이 깨지지 않는 UTF-8 BOM CSV를 만든다."""
    if not records:
        return b""
    fieldnames: list[str] = []
    seen: set[str] = set()
    for record in records:
        for field in record:
            if field not in seen:
                fieldnames.append(field)
                seen.add(field)
    buffer = io.StringIO(newline="")
    writer = csv.DictWriter(buffer, fieldnames=fieldnames)
    writer.writeheader()
    writer.writerows(records)
    return ("\ufeff" + buffer.getvalue()).encode("utf-8")


def render_company_operation_entry() -> None:
    """회사에서 측정한 실제 조업 결과를 학습자료로 추가한다."""
    with st.expander("🏭 회사 실제 운전 데이터 입력", expanded=True):
        st.caption(
            "실제 계측값을 아는 항목만 입력하고, 확인하지 못한 값은 0으로 두면 됩니다. "
            "CSU 1호기를 저장한 뒤 2호기를 선택해 다시 저장하면 두 호기 자료가 각각 누적됩니다. "
            "값이 바뀔 때마다 다시 저장하면 시간순 학습자료가 됩니다."
        )

        with st.form("company_operation_form", clear_on_submit=False):
            basic_1, basic_2, basic_3, basic_4 = st.columns(4)
            with basic_1:
                actual_date = st.date_input(
                    "조업일자",
                    value=datetime.now(KST).date(),
                )
            with basic_2:
                actual_csu = st.radio(
                    "CSU 호기",
                    ["CSU 1호기", "CSU 2호기"],
                    horizontal=True,
                )
            with basic_3:
                actual_shift = st.selectbox("근무 구분", ["주간", "야간"])
            with basic_4:
                actual_brand = st.text_input(
                    "화물 브랜드",
                    value="",
                    placeholder="예: POYA",
                )

            result_1, result_2, result_3, result_4 = st.columns(4)
            with result_1:
                scheduled_hours = st.number_input(
                    "계획 작업시간 (h)", 1.0, 24.0, 12.0, 0.5
                )
            with result_2:
                downtime_minutes = st.number_input(
                    "라인 정지시간 (분)", 0, 1_440, 0, 5
                )
            with result_3:
                stop_count = st.number_input("라인 정지 횟수", 0, 100, 0, 1)
            with result_4:
                actual_tons = st.number_input(
                    "실제 하역량 (t)", 0.0, 100_000.0, 0.0, 100.0
                )

            stop_1, stop_2 = st.columns([2.0, 1.0])
            with stop_1:
                stop_reason = st.selectbox(
                    "주요 정지 사유",
                    [
                        "정지 없음",
                        "컨베이어 사행",
                        "편적",
                        "과부하",
                        "막힘",
                        "설비 고장",
                        "선박 사정",
                        "작업 대기",
                        "기타",
                    ],
                )
            with stop_2:
                actual_excellent = st.checkbox("우수 운전 사례")

            st.markdown("##### BE DRIVE 실제 계측값")
            be_1, be_2, be_3, be_4 = st.columns(4)
            with be_1:
                actual_bucket_speed = st.number_input("버켓 속도 (%)", 0.0, 100.0, 0.0, 1.0)
            with be_2:
                actual_be_current = st.number_input("BE 전류 (A)", 0.0, 5_000.0, 0.0, 1.0)
            with be_3:
                actual_be_load = st.number_input("BE 모터 부하 (%)", 0.0, 100.0, 0.0, 1.0)
            with be_4:
                actual_be_torque = st.number_input("BE 토크 (%)", 0.0, 100.0, 0.0, 1.0)

            st.markdown("##### 호퍼 및 컨베이어 실제 계측값")
            line_1, line_2, line_3, line_4 = st.columns(4)
            with line_1:
                actual_hopper = st.number_input("호퍼 로드셀 (t)", 0.0, 100.0, 0.0, 0.5)
            with line_2:
                actual_boom_speed = st.number_input("BOOM BC 속도 (%)", 0.0, 100.0, 0.0, 1.0)
            with line_3:
                actual_boom_load = st.number_input("BOOM BC 부하 (%)", 0.0, 100.0, 0.0, 1.0)
            with line_4:
                actual_boom_torque = st.number_input("BOOM BC 토크 (%)", 0.0, 100.0, 0.0, 1.0)

            line_5, line_6, line_7 = st.columns(3)
            with line_5:
                actual_feeder_speed = st.number_input("FEEDER BC 속도 (%)", 0.0, 100.0, 0.0, 1.0)
            with line_6:
                actual_feeder_load = st.number_input("FEEDER BC 부하 (%)", 0.0, 100.0, 0.0, 1.0)
            with line_7:
                actual_feeder_torque = st.number_input("FEEDER BC 토크 (%)", 0.0, 100.0, 0.0, 1.0)

            line_8, line_9, line_10 = st.columns(3)
            with line_8:
                actual_gantry_speed = st.number_input("GANTRY BC 속도 (%)", 0.0, 100.0, 0.0, 1.0)
            with line_9:
                actual_gantry_load = st.number_input("GANTRY BC 부하 (%)", 0.0, 100.0, 0.0, 1.0)
            with line_10:
                actual_gantry_torque = st.number_input("GANTRY BC 토크 (%)", 0.0, 100.0, 0.0, 1.0)

            actual_note = st.text_area(
                "운전 특이사항",
                placeholder="예: A801 사행 경보로 25분 정지 후 벨트 속도 조정",
            )
            save_actual = st.form_submit_button(
                "입력값 적용 및 실제 운전 데이터 저장",
                use_container_width=True,
            )

        st.caption(
            "계측값이 바뀌면 값을 수정한 뒤 다시 저장하세요. "
            "저장할 때마다 해당 CSU 호기와 저장시각이 별도 행으로 누적됩니다."
        )

        if save_actual:
            effective_hours = max(0.0, scheduled_hours - downtime_minutes / 60.0)
            gross_rate = actual_tons / scheduled_hours if scheduled_hours > 0 else 0.0
            net_rate = actual_tons / effective_hours if effective_hours > 0 else 0.0
            availability = effective_hours / scheduled_hours * 100 if scheduled_hours > 0 else 0.0
            normalized_brand = actual_brand.strip() or "미입력"
            matched_brand = next(
                (
                    name
                    for name in BRAND_UNLOADING_STATS
                    if name.casefold() == normalized_brand.casefold()
                ),
                None,
            )
            actual_brand_daily = (
                BRAND_UNLOADING_STATS[matched_brand][1]
                if matched_brand
                else OVERALL_AVERAGE_DAILY_RATE
            )

            actual_record = {
                "기록시각": datetime.now(KST).strftime("%Y-%m-%d %H:%M:%S"),
                "데이터출처": "회사 실제 운전 입력",
                "조업일자": actual_date.strftime("%Y-%m-%d"),
                "CSU호기": actual_csu,
                "근무구분": actual_shift,
                "화물브랜드": normalized_brand,
                "운전모드": "실제 조업",
                "조업상태": "근무 실적 저장",
                "우수운전": "Y" if actual_excellent else "N",
                "계획작업시간_h": round(scheduled_hours, 2),
                "라인정지시간_min": downtime_minutes,
                "라인정지횟수": stop_count,
                "주요정지사유": stop_reason,
                "실가동시간_h": round(effective_hours, 2),
                "설비가동률_pct": round(availability, 1),
                "근무시간기준하역률_tph": round(gross_rate, 1),
                "실가동기준하역률_tph": round(net_rate, 1),
                "버켓속도_pct": actual_bucket_speed,
                "BE전류_A": actual_be_current,
                "BE모터부하_pct": actual_be_load,
                "BE토크_pct": actual_be_torque,
                "BOOM_BC속도_pct": actual_boom_speed,
                "BOOM_BC모터부하_pct": actual_boom_load,
                "BOOM_BC토크_pct": actual_boom_torque,
                "FEEDER_BC속도_pct": actual_feeder_speed,
                "FEEDER_BC모터부하_pct": actual_feeder_load,
                "FEEDER_BC토크_pct": actual_feeder_torque,
                "GANTRY_BC속도_pct": actual_gantry_speed,
                "GANTRY_BC모터부하_pct": actual_gantry_load,
                "GANTRY_BC토크_pct": actual_gantry_torque,
                "호퍼로드셀_t": actual_hopper,
                "실시간하역량_tph": round(net_rate, 1),
                "브랜드기준하역량_12h_t": round(actual_brand_daily / REFERENCE_CSU_COUNT, 1),
                "실제누적하역량_t": round(actual_tons, 1),
                "AI예방조치": "실제 운전자료 분석 대기",
                "AI판단": "회사 실제 운전 데이터",
                "운전특이사항": actual_note.strip(),
            }
            st.session_state.training_records.append(actual_record)
            st.success(
                f"실제 운전자료를 저장했습니다 · {normalized_brand} · "
                f"{actual_tons:,.0f}톤 · 가동률 {availability:.1f}% · "
                f"실가동 하역률 {net_rate:,.0f} t/h"
            )


@st.fragment(run_every=5)
def render_training_recorder() -> None:
    st.subheader("🧠 AI 학습용 데이터 수집")
    st.info(
        "5초 자동 수집은 디지털 트윈의 버켓·컨베이어 속도, 모터 부하·토크, "
        "호퍼 로드셀, 하역량, 사행 위험도와 AI 판단을 저장합니다. "
        "회사 실제 계측값은 값이 바뀔 때마다 위 입력 화면에서 저장 버튼을 눌러 기록합니다. "
        "모든 값은 임시 세션에 저장되므로 작업 종료 전에 반드시 CSV를 다운로드하세요."
    )
    start_record, stop_record, mark_excellent, clear_record = st.columns(4)

    with start_record:
        if st.button("● 데이터 수집 시작", use_container_width=True):
            st.session_state.recording_enabled = True
            st.session_state.last_record_time = 0.0
    with stop_record:
        if st.button("■ 데이터 수집 종료", use_container_width=True):
            st.session_state.recording_enabled = False
    with mark_excellent:
        if st.button(
            "★ 우수 운전 표시",
            use_container_width=True,
            disabled=not running,
        ):
            st.session_state.training_records.append(make_training_record(excellent=True))
            st.success("현재 운전상태를 우수 운전 사례로 저장했습니다.")
    with clear_record:
        if st.button("수집 데이터 초기화", use_container_width=True):
            st.session_state.training_records = []
            st.session_state.last_record_time = 0.0

    record_now = time.time()
    if (
        st.session_state.recording_enabled
        and running
        and record_now - st.session_state.last_record_time >= 4.5
    ):
        st.session_state.training_records.append(make_training_record())
        st.session_state.last_record_time = record_now

    record_count = len(st.session_state.training_records)
    excellent_count = sum(
        row.get("우수운전") == "Y" for row in st.session_state.training_records
    )
    status_text = "수집 중 · 5초 간격 임시 저장" if st.session_state.recording_enabled else "수집 대기"

    csu_1_count = sum(
        row.get("CSU호기") == "CSU 1호기" for row in st.session_state.training_records
    )
    csu_2_count = sum(
        row.get("CSU호기") == "CSU 2호기" for row in st.session_state.training_records
    )
    info_1, info_2, info_3, info_4, info_5 = st.columns(5)
    info_1.metric("디지털 트윈 수집", status_text)
    info_2.metric("CSU 1호기 실제자료", f"{csu_1_count:,}건")
    info_3.metric("CSU 2호기 실제자료", f"{csu_2_count:,}건")
    info_4.metric("전체 수집 데이터", f"{record_count:,}건")
    info_5.metric("우수 운전 사례", f"{excellent_count:,}건")

    if st.session_state.recording_enabled and not running:
        st.warning("조업 착수 후 데이터 자동 기록이 시작됩니다.")

    st.download_button(
        "⬇ AI 학습 데이터 CSV 다운로드",
        data=records_to_csv(st.session_state.training_records),
        file_name=f"CSU_AI_학습데이터_{datetime.now(KST):%Y%m%d_%H%M}.csv",
        mime="text/csv",
        use_container_width=True,
        disabled=record_count == 0,
    )


render_company_operation_entry()
render_training_recorder()

st.caption(
    "데모용 디지털 트윈입니다. 실제 설비 적용 전에는 현장 계측값과 제어 한계값으로 보정해야 합니다."
)

import html
import math
import time

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


mode_col, start_col, stop_col, speed_col, material_col, cargo_col = st.columns(
    [1.05, 0.85, 0.85, 1.25, 1.25, 1.25]
)

with mode_col:
    mode = st.radio("운전 모드", ["수동", "AI 자동"], horizontal=True)
with start_col:
    st.write("")
    if st.button("▶ 조업 착수", use_container_width=True):
        st.session_state.csu_running = True
with stop_col:
    st.write("")
    if st.button("■ 조업 정지", use_container_width=True):
        st.session_state.csu_running = False
with speed_col:
    manual_speed = st.slider(
        "버켓 속도 (%)", 0, 100, 65, disabled=(mode == "AI 자동")
    )
with material_col:
    manual_digging_depth = st.slider(
        "디깅 깊이 (%)", 0, 100, 65, disabled=(mode == "AI 자동")
    )
with cargo_col:
    ship_cargo = st.number_input(
        "선박 적재 화물량 (t)",
        min_value=1_000,
        max_value=200_000,
        value=55_000,
        step=100,
    )

brand_col, brand_space = st.columns([1.5, 4.5])
with brand_col:
    cargo_brand = st.text_input(
        "화물 브랜드 (니켈)",
        value="",
        placeholder="브랜드명 입력",
        max_chars=40,
    )

st.markdown("#### 컨베이어 벨트 속도 제어")
boom_col, feeder_col, gantry_col = st.columns(3)
with boom_col:
    manual_boom_speed = st.slider(
        "BOOM BC 벨트 속도 (%)", 0, 100, 80, disabled=(mode == "AI 자동")
    )
with feeder_col:
    manual_feeder_speed = st.slider(
        "FEEDER BC 벨트 속도 (%)", 0, 100, 75, disabled=(mode == "AI 자동")
    )
with gantry_col:
    manual_gantry_speed = st.slider(
        "GANTRY BC 벨트 속도 (%)", 0, 100, 80, disabled=(mode == "AI 자동")
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
    digging_depth = 62
    preliminary_fill = int(
        max(15, min(100, 18 + digging_depth * 0.92 - manual_speed * 0.08))
    )
    bucket_speed, ai_decision = calculate_ai_speed(preliminary_fill)
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
    boom_speed = min(100, max(35, bucket_speed + 8))
    feeder_speed = min(100, max(35, bucket_speed + (12 if bucket_fill_rate >= 70 else 5)))
    gantry_speed = min(100, max(35, feeder_speed + 5))
    ai_decision += (
        f" · {boom_action} · BC 속도 자동 조정 "
        f"{boom_speed}/{feeder_speed}/{gantry_speed}%"
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
        hopper_load * bucket_speed * feeder_discharge_coefficient
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
        hopper_load * feeder_speed * 0.72
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
daily_unloading = unloading * 24

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
.grid{{display:grid;grid-template-columns:repeat(8,1fr);gap:8px}}
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
 <div class="card"><div class="name">예상 일 하역량</div><div class="value" id="dayrate"></div></div>
</div>
<div class="decision" id="decision"></div>
<script>
const baseBucket={bucket_speed}, baseDepth={digging_depth};
const baseBoom={boom_speed}, baseFeeder={feeder_speed};
const baseGantry={gantry_speed}, supply={material_supply};
function clamp(v,a,b){{return Math.max(a,Math.min(b,v));}}
function update(){{
 const phase=Date.now()/3000, sw=Math.sin(phase), lw=Math.sin(phase*.73+1.2);
 let bucket=Math.round(clamp(baseBucket+sw*3,30,90));
 let depth=Math.round(clamp(baseDepth-lw*5,20,95));
 let fill=Math.round(clamp(18+depth*.92-bucket*.08,15,100));
 const boom=Math.round(clamp(baseBoom+sw*2,35,100));
 let feeder=Math.round(clamp(baseFeeder+lw*3,35,100));
 const gantry=Math.round(clamp(baseGantry+(sw+lw)*1.5,35,100));
 let hopper=Math.min(50,fill*.43+bucket*.045-(feeder-baseFeeder)*.08);
 let rate=hopper*bucket*.86*(feeder/Math.max(1,baseFeeder));
 let overLimit=rate>2400;
 if(overLimit){{
   bucket=Math.max(30,bucket-4);
   depth=Math.max(20,depth-6);
   fill=Math.round(clamp(18+depth*.92-bucket*.08,15,100));
   feeder=Math.min(100,feeder+2);
   hopper=Math.min(50,fill*.43+bucket*.045-(feeder-baseFeeder)*.08);
   rate=hopper*bucket*.86*(feeder/Math.max(1,baseFeeder));
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
 document.getElementById("dayrate").textContent=Math.round(rate*24).toLocaleString()+" t/day";
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
.route{{font-size:12px;color:#83a9bd;letter-spacing:.03em}}
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
.cargo-sm{{fill:none;stroke:#ed8a20;stroke-width:5;stroke-linecap:round;stroke-dasharray:7 9;
animation:flow {cycle_seconds}s linear infinite;animation-play-state:{animation_state}}}
.boom-cargo{{animation-duration:{boom_cycle_seconds}s;animation-play-state:{boom_animation_state}}}
.feeder-cargo{{animation-duration:{feeder_cycle_seconds}s;animation-play-state:{feeder_animation_state}}}
.gantry-cargo{{animation-duration:{gantry_cycle_seconds}s;animation-play-state:{gantry_animation_state}}}
.drop{{fill:none;stroke:#ff982e;stroke-width:7;stroke-linecap:round;stroke-dasharray:5 11;
animation:fall .62s linear infinite;animation-play-state:{animation_state}}}
.boom-drop{{animation-duration:{max(0.35, boom_cycle_seconds * 0.35)}s;animation-play-state:{boom_animation_state}}}
.feeder-drop{{animation-duration:{max(0.35, feeder_cycle_seconds * 0.35)}s;animation-play-state:{feeder_animation_state}}}
.gantry-drop{{animation-duration:{max(0.35, gantry_cycle_seconds * 0.35)}s;animation-play-state:{gantry_animation_state}}}
.bucket{{fill:url(#gold);stroke:#633800;stroke-width:2}}
.bucketset{{animation:lift {cycle_seconds}s linear infinite;animation-play-state:{animation_state}}}
.be-depth{{transform:translateY({be_depth_offset}px);
animation:digDepth 4.5s ease-in-out infinite;animation-play-state:{boom_luff_state}}}
.flush-complete .cargo,
.flush-complete .cargo-sm,
.flush-complete .drop,
.flush-complete .bucketset{{animation-play-state:paused!important}}
.lbl{{fill:#061725eF;stroke:#6d8998;stroke-width:1}} .txt{{fill:#f3f8fa;font-size:11px;font-weight:700}}
@keyframes flow{{to{{stroke-dashoffset:-92}}}}
@keyframes fall{{to{{stroke-dashoffset:64}}}}
@keyframes lift{{from{{transform:translateY(110px)}}to{{transform:translateY(-55px)}}}}
@keyframes digDepth{{0%,100%{{transform:translateY({be_depth_offset}px)}}
50%{{transform:translateY({be_depth_offset + 24}px)}}}}
.bottom{{position:absolute;left:176px;right:176px;bottom:13px;display:grid;grid-template-columns:repeat(5,1fr);gap:8px}}
.tile{{padding:10px 12px;border:1px solid #29516a;border-radius:8px;background:#071d2ddd}}
.tn{{font-size:9px;color:#82a8bd}} .tv{{font-size:17px;font-weight:850;margin-top:3px}}
</style>
</head>
<body>
<div class="scene">
<div class="grid"></div>
<div class="topline"><div class="route">화물창 → BE → BOOM BC → FEEDER BC → GANTRY BC → A801</div>
<div class="state">● {status_text}</div></div>

<div class="panel left">
  <div class="k">운전 모드</div><div class="v">{safe_mode}</div>
  <div class="k">화물 브랜드</div><div class="v">{safe_cargo_brand}</div>
  <div class="k">선박 적재 화물량</div><div class="v">{ship_cargo:,.0f} t</div>
  <div class="k">하역량</div><div class="v">{unloading:,.0f} t/h</div>
  <div class="k">예상 일 하역량</div><div class="v">{daily_unloading:,.0f} t/day</div>
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
<!-- BE DIGGING / MIDDLE / TOP -->
<path d="M345 480 L418 480 L440 530 Q410 578 355 557 L320 518Z" class="steel"/>
<circle cx="350" cy="538" r="12" fill="#17231c" stroke="#87978b" stroke-width="3"/>
<circle cx="400" cy="548" r="12" fill="#17231c" stroke="#87978b" stroke-width="3"/>
<path d="M350 160 L414 160 L420 490 L354 490Z" class="steel"/>
<path d="M317 86 L428 86 L452 118 L430 170 L326 170 L305 137Z" class="steel"/>
<circle cx="375" cy="128" r="26" fill="#17241d" stroke="#87988a" stroke-width="5"/>
<path d="M367 162 L367 480" stroke="#4b6254" stroke-width="5"/>
<g class="bucketset">
 <path d="M344 205H387L382 231Q365 242 349 230Z" class="bucket"/>
 <path d="M344 263H387L382 289Q365 300 349 288Z" class="bucket"/>
 <path d="M344 321H387L382 347Q365 358 349 346Z" class="bucket"/>
 <path d="M344 379H387L382 405Q365 416 349 404Z" class="bucket"/>
 <path d="M344 437H387L382 463Q365 474 349 462Z" class="bucket"/>
</g>

<!-- BE rotary mechanism -->
<ellipse cx="438" cy="181" rx="48" ry="15" class="steel2"/>
<rect x="421" y="169" width="68" height="34" rx="5" class="steel2"/>
</g>

<!-- BOOM and BOOM BC -->
<path d="M414 171 L1010 179 L1005 231 L414 220Z" class="steel"/>
<path d="M1005 179 L1200 132 L1210 174 L1005 231Z" class="steel"/>
<path d="M435 195 L761 195" class="cargo boom-cargo"/>

<!-- Forestay -->
<path d="M735 177 L760 25 L786 177" class="truss"/>
<path d="M760 30 L420 177 M760 30 L1155 149" class="truss"/>

<!-- Central slew structure -->
<path d="M710 220 L808 220 L828 392 L695 392Z" class="steel"/>
<ellipse cx="760" cy="220" rx="68" ry="19" class="steel2"/>
<ellipse cx="761" cy="389" rx="76" ry="21" class="steel2"/>

<!-- Visible BOOM BC vertical drop to FEEDER BC -->
<path d="M748 224 L748 404" class="drop boom-drop"/>
<path d="M761 224 L761 404" class="drop boom-drop"/>
<path d="M774 224 L774 404" class="drop boom-drop"/>

<!-- Gantry frame -->
<path d="M686 382 L730 382 L681 555 L635 555Z" class="steel"/>
<path d="M817 382 L861 382 L912 555 L866 555Z" class="steel"/>
<path d="M690 397 L880 536 M845 397 L655 536" class="truss"/>

<!-- FEEDER BC -->
<path d="M690 405 L1053 405 L1068 453 L674 453Z" class="steel2"/>
<path d="M708 430 L1042 430" class="cargo-sm feeder-cargo"/>
<path d="M932 443 L932 490" class="drop feeder-drop"/>
<path d="M945 443 L945 490" class="drop feeder-drop"/>

<!-- GANTRY BC -->
<rect x="720" y="490" width="470" height="46" rx="3" class="steel2"/>
<path d="M737 513 L1172 513" class="cargo-sm gantry-cargo"/>
<rect x="745" y="536" width="13" height="42" fill="#466d49"/>
<rect x="1148" y="536" width="13" height="42" fill="#466d49"/>
<path d="M1170 522 L1170 555" class="drop gantry-drop"/>
<path d="M1183 522 L1183 555" class="drop gantry-drop"/>
<!-- TRAVEL and land BC -->
<rect x="620" y="548" width="112" height="24" class="steel2"/>
<rect x="842" y="548" width="112" height="24" class="steel2"/>
<circle cx="648" cy="579" r="15" fill="#1b2427"/><circle cx="695" cy="579" r="15" fill="#1b2427"/>
<circle cx="870" cy="579" r="15" fill="#1b2427"/><circle cx="917" cy="579" r="15" fill="#1b2427"/>
<rect x="1155" y="555" width="220" height="37" class="deck"/>
<path d="M1168 574 L1360 574" class="cargo-sm gantry-cargo"/>

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
 <div class="tile"><div class="tn">하역량</div><div class="tv">{unloading:,.0f} t/h</div></div>
 <div class="tile"><div class="tn">예상 일 하역량</div><div class="tv">{daily_unloading:,.0f} t/day</div></div>
</div>
</div>
{flush_stop_script}
</body>
</html>
"""

components.html(digital_twin_html, height=710, scrolling=False)

if mode == "AI 자동" and running:
    live_data_html = f"""
<!doctype html><html lang="ko"><head><meta charset="utf-8">
<style>
*{{box-sizing:border-box}}body{{margin:0;background:transparent;color:#f2f8fc;
font-family:Arial,"Malgun Gothic",sans-serif}}
h2{{font-size:21px;margin:0 0 12px}}h3{{font-size:15px;margin:13px 0 8px}}
.grid5{{display:grid;grid-template-columns:repeat(5,1fr);gap:10px}}
.grid3{{display:grid;grid-template-columns:repeat(3,1fr);gap:10px}}
.card{{min-height:70px;padding:11px;border:1px solid #29546d;border-radius:9px;
background:linear-gradient(180deg,#0a263a,#061827)}}
.name{{font-size:10px;color:#91b4c8}}.value{{font-size:21px;font-weight:850;margin-top:7px}}
</style></head><body>
<h2>실시간 운전 데이터</h2>
<div class="grid5">
 <div class="card"><div class="name">하역량</div><div class="value" id="u"></div></div>
 <div class="card"><div class="name">예상 일 하역량</div><div class="value" id="ud"></div></div>
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
const C=(v,a,b)=>Math.max(a,Math.min(b,v)), put=(id,v)=>document.getElementById(id).textContent=v;
function tick(){{
 const p=Date.now()/3000,sw=Math.sin(p),lw=Math.sin(p*.73+1.2);
 let b=Math.round(C(bb+sw*3,30,90)),bs=Math.round(C(bo+sw*2,35,100));
 let fs=Math.round(C(fe+lw*3,35,100)),gs=Math.round(C(ga+(sw+lw)*1.5,35,100));
 let depth=Math.round(C(bd-lw*5,20,95));
 let fill=Math.round(C(18+depth*.92-b*.08,15,100));
 let hp=Math.min(50,fill*.43+b*.045-(fs-fe)*.08);
 let u=hp*b*.86*(fs/Math.max(1,fe));
 if(u>2400){{
   b=Math.max(30,b-4);depth=Math.max(20,depth-6);
   fill=Math.round(C(18+depth*.92-b*.08,15,100));fs=Math.min(100,fs+2);
   hp=Math.min(50,fill*.43+b*.045-(fs-fe)*.08);
   u=hp*b*.86*(fs/Math.max(1,fe));
 }}
 const bl=Math.min(100,16+b*.66+fill*.14),bt=Math.min(100,14+b*.58+fill*.18);
 const bml=Math.min(100,7+bs*.42+u/900),bmt=Math.min(100,6+bs*.35);
 const fml=Math.min(100,10+fs*.48+hp*.40),fmt=Math.min(100,8+fs*.40+hp*.50);
 const gml=Math.min(100,7+gs*.42),gmt=Math.min(100,6+gs*.35);
 put("u",Math.round(u).toLocaleString()+" t/h");put("ud",Math.round(u*24).toLocaleString()+" t/day");
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
    metric_1, metric_2, metric_3, metric_4, metric_5 = st.columns(5)
    metric_1.metric("하역량", f"{unloading:,.0f} t/h")
    metric_2.metric("예상 일 하역량", f"{daily_unloading:,.0f} t/day")
    metric_3.metric("버켓 모터 부하", f"{motor_load:.1f} %")
    metric_4.metric("버켓 토크", f"{bucket_torque:.1f} %")
    metric_5.metric("호퍼 로드셀", f"{hopper_load:.1f} t")

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

st.caption(
    "데모용 디지털 트윈입니다. 실제 설비 적용 전에는 현장 계측값과 제어 한계값으로 보정해야 합니다."
)

import html

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
    material_supply = st.slider("원료 공급 조건 (%)", 0, 100, 75)
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
    bucket_speed, ai_decision = calculate_ai_speed(material_supply)
    boom_speed = min(100, max(35, bucket_speed + 8))
    feeder_speed = min(100, max(35, bucket_speed + (12 if material_supply >= 70 else 5)))
    gantry_speed = min(100, max(35, feeder_speed + 5))
    ai_decision += (
        f" · BC 속도 자동 조정 "
        f"{boom_speed}/{feeder_speed}/{gantry_speed}%"
    )
else:
    bucket_speed = manual_speed
    boom_speed = manual_boom_speed
    feeder_speed = manual_feeder_speed
    gantry_speed = manual_gantry_speed
    ai_decision = "작업자 설정 속도로 운전"

running = st.session_state.csu_running and bucket_speed > 0

if running:
    # 호퍼 로드셀의 측정 중량을 먼저 산출하고,
    # 교정된 피더 배출계수를 적용해 순간 하역량을 계산한다.
    hopper_load = min(50.0, material_supply * 0.43 + bucket_speed * 0.045)
    feeder_discharge_coefficient = 0.86
    unloading = hopper_load * bucket_speed * feeder_discharge_coefficient
    motor_load = min(100.0, 16 + bucket_speed * 0.66 + material_supply * 0.14)
    bucket_torque = min(100.0, 14 + bucket_speed * 0.58 + material_supply * 0.17)
    boom_motor_load = min(100.0, 12 + boom_speed * 0.55 + material_supply * 0.12)
    boom_torque = min(100.0, 10 + boom_speed * 0.45 + material_supply * 0.14)
    feeder_motor_load = min(100.0, 15 + feeder_speed * 0.58 + hopper_load * 0.50)
    feeder_torque = min(100.0, 12 + feeder_speed * 0.50 + hopper_load * 0.65)
    gantry_motor_load = min(100.0, 10 + gantry_speed * 0.52 + unloading / 100)
    gantry_torque = min(100.0, 9 + gantry_speed * 0.45 + unloading / 120)
    loadcell_status = "로드셀 측정 중 · 하역량 연동"
else:
    unloading = motor_load = bucket_torque = hopper_load = 0.0
    boom_motor_load = boom_torque = 0.0
    feeder_motor_load = feeder_torque = 0.0
    gantry_motor_load = gantry_torque = 0.0
    loadcell_status = "로드셀 대기"

estimated_hours = ship_cargo / unloading if unloading > 0 else 0.0

if running:
    st.success(
        f"🟢 조업 중 · {mode} · 버켓 속도 {bucket_speed}% · "
        f"{loadcell_status} · AI 판단: {ai_decision}"
    )
else:
    st.error("🔴 조업 정지 · 시뮬레이터 정지")


animation_state = "running" if running else "paused"
cycle_seconds = max(0.62, 3.1 - bucket_speed * 0.024)
boom_cycle_seconds = max(0.55, 3.0 - boom_speed * 0.023)
feeder_cycle_seconds = max(0.55, 3.0 - feeder_speed * 0.023)
gantry_cycle_seconds = max(0.55, 3.0 - gantry_speed * 0.023)
status_text = "조업 중" if running else "조업 정지"
status_color = "#2bd477" if running else "#ef5b5b"

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
.boom-cargo{{animation-duration:{boom_cycle_seconds}s}}
.feeder-cargo{{animation-duration:{feeder_cycle_seconds}s}}
.gantry-cargo{{animation-duration:{gantry_cycle_seconds}s}}
.drop{{fill:none;stroke:#ff982e;stroke-width:7;stroke-linecap:round;stroke-dasharray:5 11;
animation:fall .62s linear infinite;animation-play-state:{animation_state}}}
.boom-drop{{animation-duration:{max(0.35, boom_cycle_seconds * 0.35)}s}}
.feeder-drop{{animation-duration:{max(0.35, feeder_cycle_seconds * 0.35)}s}}
.gantry-drop{{animation-duration:{max(0.35, gantry_cycle_seconds * 0.35)}s}}
.bucket{{fill:url(#gold);stroke:#633800;stroke-width:2}}
.bucketset{{animation:lift {cycle_seconds}s linear infinite;animation-play-state:{animation_state}}}
.lbl{{fill:#061725eF;stroke:#6d8998;stroke-width:1}} .txt{{fill:#f3f8fa;font-size:11px;font-weight:700}}
@keyframes flow{{to{{stroke-dashoffset:-92}}}}
@keyframes fall{{to{{stroke-dashoffset:64}}}}
@keyframes lift{{from{{transform:translateY(110px)}}to{{transform:translateY(-55px)}}}}
.bottom{{position:absolute;left:176px;right:176px;bottom:13px;display:grid;grid-template-columns:repeat(4,1fr);gap:8px}}
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
  <div class="k">예상 하역시간</div><div class="v">{estimated_hours:.1f} h</div>
  <div class="k">호퍼 로드셀</div><div class="v accent">{hopper_load:.1f} t</div>
  <div class="k">{loadcell_status}</div>
</div>
<div class="panel right">
  <div class="k">AI CONTROL</div><div class="v good">{safe_mode}</div>
  <div class="k">버켓 속도</div><div class="v">{bucket_speed} %</div>
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

<!-- BOOM and BOOM BC -->
<path d="M414 171 L1010 179 L1005 231 L414 220Z" class="steel"/>
<path d="M1005 179 L1200 132 L1210 174 L1005 231Z" class="steel"/>
<path d="M435 195 L761 184" class="cargo boom-cargo"/>

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
</div>
</div>
</body>
</html>
"""

components.html(digital_twin_html, height=710, scrolling=False)

st.subheader("실시간 운전 데이터")
metric_1, metric_2, metric_3, metric_4 = st.columns(4)
metric_1.metric("하역량", f"{unloading:,.0f} t/h")
metric_2.metric("버켓 모터 부하", f"{motor_load:.1f} %")
metric_3.metric("버켓 토크", f"{bucket_torque:.1f} %")
metric_4.metric("호퍼 로드셀", f"{hopper_load:.1f} t")

st.subheader("컨베이어 실시간 운전 데이터")

st.markdown("##### BOOM BC")
boom_1, boom_2, boom_3 = st.columns(3)
boom_1.metric("BOOM BC 벨트 속도", f"{boom_speed if running else 0} %")
boom_2.metric("BOOM BC 모터 부하", f"{boom_motor_load:.1f} %")
boom_3.metric("BOOM BC 토크", f"{boom_torque:.1f} %")

st.markdown("##### FEEDER BC")
feeder_1, feeder_2, feeder_3 = st.columns(3)
feeder_1.metric("FEEDER BC 벨트 속도", f"{feeder_speed if running else 0} %")
feeder_2.metric("FEEDER BC 모터 부하", f"{feeder_motor_load:.1f} %")
feeder_3.metric("FEEDER BC 토크", f"{feeder_torque:.1f} %")

st.markdown("##### GANTRY BC")
gantry_1, gantry_2, gantry_3 = st.columns(3)
gantry_1.metric("GANTRY BC 벨트 속도", f"{gantry_speed if running else 0} %")
gantry_2.metric("GANTRY BC 모터 부하", f"{gantry_motor_load:.1f} %")
gantry_3.metric("GANTRY BC 토크", f"{gantry_torque:.1f} %")

st.caption(
    "데모용 디지털 트윈입니다. 실제 설비 적용 전에는 현장 계측값과 제어 한계값으로 보정해야 합니다."
)

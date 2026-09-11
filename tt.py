"""
MIL-STD-810H Temperature & Humidity Accelerated Life Testing (ALT) Dashboard
Based on Method 501.7 (High Temp), Method 507.6 (Humidity), and Method 520.5
"""

import streamlit as st
import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from scipy.special import gamma

st.set_page_config(
    page_title="MIL-STD-810H 온·습도 수명 예측 분석기",
    page_icon="🌡️",
    layout="wide"
)

st.title("🌡️ MIL-STD-810H 기반 온·습도 복합 환경 가속수명(ALT) 설계기")
st.caption("MIL-STD-810H 기후 설계 유형(A1, A2, B3) 기준 LCEP 실운용 조건과 챔버 시험 조건 간 Peck/Arrhenius 수명 모델링")

# ---------------------------------------------------------
# Sidebar: MIL-STD-810H 기후 카테고리 프리셋 및 시험 조건 설정
# ---------------------------------------------------------
with st.sidebar:
    st.header("🌍 1. 실운용 LCEP 기후 조건 (MIL-STD-810H)")
    climatic_preset = st.selectbox(
        "기후 설계 카테고리 (Table C-I)",
        ["사용자 정의 (Custom)", "Basic Hot (A2) [30~43°C, 44~14%RH]", "Hot Dry (A1) [32~49°C, 8~3%RH]", "Hot Humid (B3) [31~41°C, 88~59%RH]"]
    )
    
    if "A2" in climatic_preset:
        t_field_init, rh_field_init = 43.0, 30.0
    elif "A1" in climatic_preset:
        t_field_init, rh_field_init = 49.0, 8.0
    elif "B3" in climatic_preset:
        t_field_init, rh_field_init = 41.0, 80.0
    else:
        t_field_init, rh_field_init = 25.0, 50.0

    t_field = st.number_input("실운용 기준 온도 (°C)", value=float(t_field_init), step=1.0)
    rh_field = st.slider("실운용 기준 습도 (%RH)", 1, 100, int(rh_field_init))

    st.markdown("---")
    st.header("🧪 2. 챔버 가속 시험 조건 (Method 501.7 / 507.6)")
    t_test = st.number_input("시험 챔버 온도 (°C)", value=85.0, step=1.0, help="Method 501.7 고온 시험 조건")
    rh_test = st.slider("시험 챔버 습도 (%RH)", 1, 100, 85, help="Method 507.6 습도 시험 조건 (THB/Damp Heat)")

    st.markdown("---")
    st.header("📐 3. 물리 모델 공학 파라미터")
    Ea = st.number_input("활성화 에너지 Ea (eV)", value=0.70, step=0.05, help="반응 속도론: 전자/전기 0.6~0.8 eV, 절연체 열화 0.7~0.9 eV")
    n_rh = st.number_input("Peck 습도 반응 지수 (n)", value=2.7, step=0.1, help="습도 반응 가속 지수: 통상 2.5 ~ 3.0")

# ---------------------------------------------------------
# 가속계수 수식 연산 (Peck & Arrhenius Model)
# ---------------------------------------------------------
k_B = 8.617333262145e-5  # Boltzmann constant (eV/K)
t_field_k = t_field + 273.15
t_test_k = t_test + 273.15

# 온도 가속계수
AF_temp = np.exp((Ea / k_B) * ((1.0 / t_field_k) - (1.0 / t_test_k)))

# 습도 가속계수
AF_rh = (rh_test / max(rh_field, 1.0)) ** n_rh

# 복합 총 가속계수
AF_total = AF_temp * AF_rh

# ---------------------------------------------------------
# 상단 KPI 카드 지표
# ---------------------------------------------------------
c1, c2, c3, c4 = st.columns(4)
with c1:
    st.metric("온도 가속계수 (AF_Temp)", f"{AF_temp:,.1f} 배", help="Arrhenius Model")
with c2:
    st.metric("습도 가속계수 (AF_RH)", f"{AF_rh:,.1f} 배", help="Peck Power Law Model")
with c3:
    st.metric("🔥 온·습도 복합 가속계수", f"{AF_total:,.1f} 배", delta=f"{AF_total:,.0f}x 시간 단축")
with c4:
    test_100hr_equivalent = (100.0 * AF_total) / (24.0 * 365.0)
    st.metric("시험 100시간 환산 수명", f"{test_100hr_equivalent:.1f} 년", delta="24시간 연속 운용 기준")

st.markdown("---")

# ---------------------------------------------------------
# 탭 구성
# ---------------------------------------------------------
tab_profile, tab_matrix, tab_weibull = st.tabs([
    "⏱️ 시험시간 설계 및 프로파일 비교",
    "🗺️ 온·습도 가속 등고선 매트릭스",
    "📈 와이블(Weibull) 수명 곡선 & B10 산출"
])

# ---------------------------------------------------------
# TAB 1: 시험시간 설계 및 프로파일 비교
# ---------------------------------------------------------
with tab_profile:
    st.subheader("1. 목표 보증 수명에 따른 필수 챔버 시험시간 산출")
    
    col_p1, col_p2 = st.columns([1, 1])
    with col_p1:
        target_years = st.slider("목표 실사용 보증 기간 (년)", 1, 20, 5)
        operating_hours_per_day = st.number_input("일일 장비 가동 시간 (hr/day)", value=8.0, min_value=1.0, max_value=24.0)
        
        required_field_hours = target_years * 365 * operating_hours_per_day
        required_test_hours = required_field_hours / AF_total
        required_test_days = required_test_hours / 24.0
        
        st.write("##### 계산 결과 요약")
        res_table = pd.DataFrame({
            "항목": ["실운용 목표 수명", "복합 가속계수 (AF)", "필수 챔버 시험시간", "필수 시험일수"],
            "수치": [f"{required_field_hours:,.0f} 시간 ({target_years}년)", f"{AF_total:,.1f} 배", f"{required_test_hours:,.1f} 시간", f"{required_test_days:,.1f} 일"]
        })
        st.table(res_table)
        st.info(f"👉 챔버에서 **{required_test_hours:,.0f}시간({required_test_days:.1f}일)** 동안 연속 시험 시, 실사용 {target_years}년 수명을 동등하게 입증할 수 있습니다.")

    with col_p2:
        # 시험 온도 상승에 따른 필요 시험시간 감소 추이
        temp_sweep = np.linspace(t_field + 15, 95.0, 30)
        test_hours_sweep = []
        for t_val in temp_sweep:
            t_val_k = t_val + 273.15
            af_t = np.exp((Ea / k_B) * ((1.0 / t_field_k) - (1.0 / t_val_k)))
            af_tot = af_t * AF_rh
            test_hours_sweep.append(required_field_hours / af_tot)

        fig_time = px.line(x=temp_sweep, y=test_hours_sweep,
                           labels={"x": "시험 챔버 온도 (°C)", "y": "필요 시험 시간 (Hours)"},
                           title=f"챔버 온도 상향에 따른 시험 시간 단축 곡선 (RH={rh_test}%)")
        fig_time.add_vline(x=t_test, line_dash="dash", line_color="red", annotation_text=f"설정 시험온도: {t_test}°C ({required_test_hours:.1f}hr)")
        fig_time.update_layout(template="plotly_white", height=340)
        st.plotly_chart(fig_time, use_container_width=True)

# ---------------------------------------------------------
# TAB 2: 온·습도 가속 등고선 매트릭스
# ---------------------------------------------------------
with tab_matrix:
    st.subheader("2. 시험 챔버 온도 vs 습도 복합 가속계수 히트맵")
    st.caption("시험실 장비 사양에 맞추어 최적의 시험 가속 포인트를 선정하기 위한 민감도 맵입니다.")

    sweep_temps = np.linspace(50.0, 95.0, 8)
    sweep_rhs = np.linspace(50, 95, 8)

    z_af = []
    for rh_v in sweep_rhs:
        row = []
        af_rh_local = (rh_v / max(rh_field, 1.0)) ** n_rh
        for t_v in sweep_temps:
            t_v_k = t_v + 273.15
            af_t_local = np.exp((Ea / k_B) * ((1.0 / t_field_k) - (1.0 / t_v_k)))
            row.append(round(af_t_local * af_rh_local, 1))
        z_af.append(row)

    fig_heat = px.imshow(
        z_af,
        x=[f"{t:.0f}°C" for t in sweep_temps],
        y=[f"{rh:.0f}%" for rh in sweep_rhs],
        labels=dict(x="시험 온도", y="시험 상대습도", color="가속계수 (AF)"),
        color_continuous_scale="YlOrRd",
        text_auto=True
    )
    fig_heat.update_layout(title="온·습도 조합별 가속계수(AF) 등고선", height=420)
    st.plotly_chart(fig_heat, use_container_width=True)

# ---------------------------------------------------------
# TAB 3: 와이블 수명 곡선 & B10 산출
# ---------------------------------------------------------
with tab_weibull:
    st.subheader("3. 와이블(Weibull) 분포 기반 수명 예측 및 신뢰도 곡선")
    
    col_w1, col_w2, col_w3 = st.columns(3)
    with col_w1:
        weibull_beta = st.slider("와이블 형상모수 (β)", min_value=0.8, max_value=4.0, value=2.2, step=0.1,
                                 help="β > 1: 온·습도 침투 및 부식에 의한 마모형 고장 메커니즘")
    with col_w2:
        test_eta = st.number_input("시험 기준 특성수명 (η_test, Hours)", value=500.0, step=50.0)
    with col_w3:
        target_reliability = st.slider("목표 신뢰도 R(t) (%)", min_value=50.0, max_value=99.0, value=90.0, step=1.0)

    # 필드 환산 특성수명 및 수명 지표 계산
    field_eta = test_eta * AF_total
    r_dec = target_reliability / 100.0
    b_life_field = field_eta * ((-np.log(r_dec)) ** (1.0 / weibull_beta))
    mttf_field = field_eta * gamma(1.0 + (1.0 / weibull_beta))

    col_m1, col_m2, col_m3 = st.columns(3)
    with col_m1:
        st.metric("실사용 환산 특성수명 (η_field)", f"{field_eta:,.0f} 시간", delta=f"{field_eta/(24*365):.1f} 년")
    with col_m2:
        st.metric(f"B{int((1-r_dec)*100)} 보증 수명 (R={target_reliability}%)", f"{b_life_field:,.0f} 시간", delta=f"{b_life_field/(24*365):.1f} 년")
    with col_m3:
        st.metric("실사용 평균고장시간 (MTTF)", f"{mttf_field:,.0f} 시간", delta=f"{mttf_field/(24*365):.1f} 년")

    st.markdown("---")
    
    # 신뢰도 및 고장률 곡선 시각화
    t_span = np.linspace(0, field_eta * 1.6, 300)
    R_curve = np.exp(- (t_span / field_eta) ** weibull_beta)
    F_curve = 1.0 - R_curve

    fig_rel = go.Figure()
    fig_rel.add_trace(go.Scatter(x=t_span / (24 * 365), y=R_curve, mode="lines", name="신뢰도 R(t)", line=dict(color="#2563EB", width=3)))
    fig_rel.add_trace(go.Scatter(x=t_span / (24 * 365), y=F_curve, mode="lines", name="누적불량률 F(t)", line=dict(color="#DC2626", dash="dash")))
    fig_rel.add_trace(go.Scatter(
        x=[b_life_field / (24 * 365)], y=[r_dec], mode="markers+text",
        marker=dict(color="orange", size=10),
        text=[f"B{int((1-r_dec)*100)}: {b_life_field/(24*365):.1f}년"],
        textposition="bottom right",
        name=f"목표 R={target_reliability}%"
    ))
    fig_rel.update_layout(title="실운용 기간에 따른 신뢰도 R(t) 감쇠 곡선", xaxis_title="운용 연수 (Years)", yaxis_title="확률 (0 ~ 1.0)", template="plotly_white", height=380)
    st.plotly_chart(fig_rel, use_container_width=True)
"""
MIL-DTL-901E Shock Engineering & SRF Mathematical Calculator Dashboard
Implements Appendix A (Shock Response Frequency) and Test Classification Rules
"""

import streamlit as st
import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

st.set_page_config(
    page_title="MIL-DTL-901E 함정 충격 수학적 계산기",
    page_icon="⚓",
    layout="wide"
)

st.title("⚓ MIL-DTL-901E 함정 고충격(H.I.) 수학적 계산 및 수명 해석기")
st.caption("규격서 Appendix A의 비선형 마운트 SRF 연산, FSP 질량비 판정 및 다축 반복 충격 누적 피로 계산")

# ---------------------------------------------------------
# Sidebar: 규격 기준 시험 조건 및 장비 제원 입력
# ---------------------------------------------------------
with st.sidebar:
    st.header("📋 1. 장비 및 시험 기본 정보")
    equip_weight = st.number_input("시험 장비 중량 (lbs)", value=450.0, step=10.0)
    fixture_weight = st.number_input("치구(Fixture) 중량 (lbs)", value=120.0, step=10.0)
    total_weight = equip_weight + fixture_weight
    st.info(f"총 중량(Total Test Weight): **{total_weight:,.1f} lbs**")

    # 시험기 범주 판정 (3.1.2)
    if total_weight <= 550:
        suggested_machine = "Lightweight Shock Machine (LWSM)"
    elif total_weight <= 7400:
        suggested_machine = "Medium Weight Shock Machine (MWSM)"
    else:
        suggested_machine = "Floating Shock Platform (Heavyweight FSP)"
    st.success(f"👉 권장 시험기: **{suggested_machine}**")

    st.markdown("---")
    st.header("🧮 2. Appendix A 마운트 파라미터")
    f_rated = st.number_input("정격 진동 절연 주파수 frated (Hz)", value=8.0, step=0.5)
    w_rated = st.number_input("마운트 개당 정격 하중 Wrated (lbs)", value=150.0, step=10.0)
    num_mounts = st.number_input("설치 마운트 수량 (개)", value=4, step=1, min_value=1)
    
    # 마운트 개당 실제 하중
    w_act = equip_weight / num_mounts
    st.caption(f"마운트 1개당 작용 하중 (Wact): {w_act:.1f} lbs")

    c_A = st.number_input("이선형 꺾임 변위 cA (스너버 간극, inch)", value=0.125, step=0.025)
    beta_A = st.number_input("강성비 beta_A (k2 / k1, 고강성/저강성 비)", value=25.0, step=1.0)
    
    # Table A-I 기준 충격 초기속도 V0 자동 추천
    if total_weight < 300:
        v0_def = 120.0
    elif total_weight <= 550:
        v0_def = 85.0
    elif total_weight < 2000:
        v0_def = 75.0
    elif total_weight < 4000:
        v0_def = 85.0
    else:
        v0_def = 120.0
        
    v0_input = st.number_input("초기 충격 속도 V0 (in/sec, Table A-I)", value=float(v0_def), step=5.0)

# ---------------------------------------------------------
# Appendix A 수학적 연산 로직 (SRF 산출)
# ---------------------------------------------------------
# Step e: 선형 영역 주파수 fA
f_A = f_rated * np.sqrt(w_rated / w_act)
g_inch = 386.088  # in/sec^2

# Step f: 저강성 영역 강성 k1A (lbs/in)
k1_A = ((2 * np.pi * f_A) ** 2 * w_act) / g_inch
k2_A = k1_A * beta_A

# 무차원 인수 산출 (2*pi*fA*cA / V0)
arg_sin = (2.0 * np.pi * f_A * c_A) / v0_input

if arg_sin >= 1.0:
    st.error("입력 변수 오류: 변위(cA) 또는 주파수가 초기속도(V0) 대비 너무 큽니다. 스너버가 충격 영역에 도달하지 못합니다.")
    st.stop()

# Equation (3): alpha_A
numerator_alpha = 2.0 * np.pi * f_A * c_A
denominator_alpha = np.sqrt(beta_A) * v0_input * np.sqrt(1.0 - (arg_sin ** 2))
alpha_A = np.arctan(numerator_alpha / denominator_alpha)

# Equation (1): SRF_Curve_A
term1 = np.arcsin(arg_sin)
term2 = (np.pi - 2.0 * alpha_A) / (2.0 * np.sqrt(beta_A))
SRF_calc = (f_A * (np.pi / 2.0)) / (term1 + term2)

# 물리 파생치 계산
max_disp_inch = c_A + (v0_input / (2 * np.pi * SRF_calc))  # 최대 충격 변위 추정
peak_accel_g = (v0_input * (2 * np.pi * SRF_calc)) / g_inch  # 피크 충격 가속도(G)

# ---------------------------------------------------------
# 탭 구성
# ---------------------------------------------------------
tab_srf, tab_fsp, tab_fatigue = st.tabs([
    "🎯 마운트 SRF 및 Class 판정 (Appendix A)", 
    "🚢 FSP 바지선 & DSF 질량비 계산", 
    "💥 충격 가속도 & 반복 피로 수명 해석"
])

# ---------------------------------------------------------
# TAB 1: 마운트 SRF 및 Class 판정
# ---------------------------------------------------------
with tab_srf:
    st.subheader("1. Appendix A 이선형(Bi-linear) 마운트 충격 응답 주파수")
    
    col_r1, col_r2, col_r3, col_r4 = st.columns(4)
    with col_r1:
        st.metric("선형 진동 주파수 (fA)", f"{f_A:.2f} Hz")
    with col_r2:
        st.metric("비선형 충격주파수 (SRF)", f"{SRF_calc:.2f} Hz")
    with col_r3:
        st.metric("피크 충격 가속도", f"{peak_accel_g:.1f} G")
    with col_r4:
        st.metric("최대 압축 변위", f"{max_disp_inch:.3f} inch")

    st.markdown("---")
    
    # Class I 판정 (규격 3.1.6.1.b: SRF > 37 Hz 시 Class I 시험 가능)
    col_verdict1, col_verdict2 = st.columns([1, 1])
    with col_verdict1:
        st.write("##### 📌 규격 기준 Class 판정 (3.1.6.1.b / 3.1.6.4.c)")
        if SRF_calc > 37.0:
            st.success(f"**판정: SRF ({SRF_calc:.1f} Hz) > 37 Hz**\n\n"
                       "해당 장비는 LDCID(제한변위 절연장치)로 인정되어, 기술기관 승인 시 "
                       "**Class I (비격리/고정 장착) 시험 요건으로 시험 가능**합니다.")
        else:
            st.warning(f"**판정: SRF ({SRF_calc:.1f} Hz) ≤ 37 Hz**\n\n"
                       "일반 탄성 마운트로 분류됩니다. **Class II(격리 장착)** 시험 절차를 준수해야 하며, "
                       "데크 장착 장비의 경우 DSF 또는 DSSM(Deck Simulating) 시험이 필수적입니다.")

        st.markdown(r"""
        **산출 수식 (Eq. 1 & Eq. 3):**
        $$SRF = \frac{f_A \left(\frac{\pi}{2}\right)}{\sin^{-1}\left(\frac{2\pi f_A c_A}{V_0}\right) + \frac{\pi - 2\alpha_A}{2\sqrt{\beta_A}}}$$
        """)

    with col_verdict2:
        # cA 변화에 따른 SRF 민감도 곡선
        c_sweep = np.linspace(0.02, 0.4, 40)
        srf_sweep = []
        for c_val in c_sweep:
            arg = (2.0 * np.pi * f_A * c_val) / v0_input
            if arg < 1.0:
                num = 2.0 * np.pi * f_A * c_val
                den = np.sqrt(beta_A) * v0_input * np.sqrt(1.0 - arg**2)
                alp = np.arctan(num / den)
                srf_val = (f_A * (np.pi / 2.0)) / (np.arcsin(arg) + (np.pi - 2.0 * alp)/(2.0 * np.sqrt(beta_A)))
                srf_sweep.append(srf_val)
            else:
                srf_sweep.append(np.nan)

        fig_srf = px.line(x=c_sweep, y=srf_sweep, labels={"x": "스너버 간극 cA (inch)", "y": "SRF (Hz)"},
                          title="스너버 간극(cA) 변화에 따른 SRF 변화 곡선")
        fig_srf.add_hline(y=37.0, line_dash="dash", line_color="red", annotation_text="37 Hz (Class I 경계)")
        fig_srf.add_vline(x=c_A, line_dash="dot", line_color="blue", annotation_text=f"현재 cA: {c_A} in")
        fig_srf.update_layout(template="plotly_white", height=320)
        st.plotly_chart(fig_srf, use_container_width=True)

# ---------------------------------------------------------
# TAB 2: FSP 바지선 & DSF 질량비 계산
# ---------------------------------------------------------
with tab_fsp:
    st.subheader("2. Floating Shock Platform (FSP) 탑재 한계 및 DSF 질량비 검증")
    
    col_b1, col_b2 = st.columns(2)
    with col_b1:
        barge_type = st.selectbox("FSP 플랫폼 선택 (3.1.2.c)", ["Standard FSP (28-ft)", "EFSP (Extended)", "IFSP (Intermediate)", "LFSP (Large)"])
        
        if barge_type == "Standard FSP (28-ft)":
            fsp_limit = 2500 * (28 - 4)  # 60,000 lbs
        elif barge_type == "EFSP (Extended)":
            fsp_limit = 100000.0
        elif barge_type == "IFSP (Intermediate)":
            fsp_limit = 250000.0
        else:
            fsp_limit = 400000.0
            
        st.metric(f"{barge_type} 최대 허용 하중", f"{fsp_limit:,.0f} lbs")
        st.write(f"현재 총 하중 비율: **{(total_weight / fsp_limit * 100):.1f}%** ({total_weight:,.0f} / {fsp_limit:,.0f} lbs)")

    with col_b2:
        st.write("##### DSF 질량비 판정 (3.1.8.5.1.3)")
        dsf_target_freq = st.selectbox("DSF 타겟 고유진동수", ["25 Hz (Class I/선체)", "14 Hz (표준 데크)", "8 Hz (항모 저주파 데크)"])
        dsf_modal_mass = st.number_input("DSF 모달/유효 질량 (lbs)", value=5000.0, step=500.0)
        
        # 질량비 계산
        mass_ratio = dsf_modal_mass / max(equip_weight, 1.0)
        
        req_ratio = 2.0 if "25 Hz" in dsf_target_freq else (5.0 if "14 Hz" in dsf_target_freq else 10.0)
        
        st.metric("실제 질량비 (DSF : 장비)", f"{mass_ratio:.2f} : 1", delta=f"요구 기준 {req_ratio:.1f}:1")
        if mass_ratio >= req_ratio:
            st.success(f"✅ 규격 충족: 요구 질량비({req_ratio:.1f}:1)를 만족합니다.")
        else:
            st.error(f"❌ 규격 미달: 추가 밸러스트(Ballast)를 증망하여 최소 {req_ratio * equip_weight:,.0f} lbs 이상의 DSF 유효질량을 확보해야 합니다.")

# ---------------------------------------------------------
# TAB 3: 충격 가속도 & 반복 피로 수명 해석
# ---------------------------------------------------------
with tab_fatigue:
    st.subheader("3. 복수 충격 타격에 따른 누적 손상 및 피로 수명 계산")
    st.caption("MIL-DTL-901E 규격 시험 일정(Group I, II, III 및 Shot 1~4) 동안 부품이 받는 충격 피로 누적치(Miner's Rule) 평가")

    col_fat1, col_fat2 = st.columns(2)
    with col_fat1:
        sigma_uts = st.number_input("구조재료 인장강도 (UTS, MPa)", value=450.0, step=25.0)
        sigma_yield = st.number_input("구조재료 항복강도 (Yield, MPa)", value=310.0, step=25.0)
        fatigue_exp_b = st.slider("Basquin 피로 기울기 지수 (-b)", min_value=0.05, max_value=0.20, value=0.10, step=0.01)
        
        # 충격 시 발생하는 환산 등가응력 (가속도에 비례)
        stress_per_g = st.number_input("1G 당 구조 발생 응력 (MPa/G)", value=4.5, step=0.5)
        calc_shock_stress = peak_accel_g * stress_per_g
        st.metric("단발 충격 시 피크 응력", f"{calc_shock_stress:.1f} MPa",
                  delta=f"항복응력 대비 {(calc_shock_stress/sigma_yield*100):.1f}%")

    with col_fat2:
        # 시험 시리즈별 타격 수 정의
        total_blows = st.number_input("규격 시험 총 타격/Shot 횟수", value=9, min_value=1, max_value=30, step=1,
                                      help="LWSM 기본 9회(축당 3회), MWSM 통상 6~9회")
        
        # S-N 피로 수명 예측: N_f = 0.5 * (sigma_a / sigma_f')^(1/b)
        sigma_f_prime = sigma_uts * 1.5
        if calc_shock_stress > 0:
            n_fail_cycles = 0.5 * ((calc_shock_stress / sigma_f_prime) ** (-1.0 / fatigue_exp_b))
        else:
            n_fail_cycles = np.inf

        damage_cumulative = total_blows / n_fail_cycles if n_fail_cycles > 0 else 0.0
        
        st.metric("충격 피로 파괴 허용 타격 수 (N_f)", f"{int(n_fail_cycles):,} 회")
        st.metric("누적 피로 손상도 (Miner's Sum D)", f"{damage_cumulative:.4f}",
                  delta="D < 1.0 (안전)" if damage_cumulative < 1.0 else "D ≥ 1.0 (파손 위험)")

        if damage_cumulative < 0.2:
            st.success("✅ 시험 완료 후 구조적 잔여 수명이 충분하며 소성 변형 위험이 낮습니다.")
        elif damage_cumulative < 1.0:
            st.warning("⚠️ 충격 누적 피로가 누적되고 있습니다. 볼트 풀림 및 용접부 비파괴검사(NDT)가 필요합니다.")
        else:
            st.error("❌ 규격 시험 타격 과정 중 피로 균열 또는 영구 변형 파손 가능성이 높습니다. 체결부 보강이 요구됩니다.")
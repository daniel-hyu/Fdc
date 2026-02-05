import streamlit as st
import math
import numpy as np

# --- 1. 핵심 계산 함수들 (로직 유지) ---
def GetMil(dx, dy):
    rad = math.atan2(dx, dy)
    if rad <= 0:
        rad += 2 * math.pi
    return (rad * 3200) / math.pi

def CalDis(dx, dy):
    return math.sqrt(dx * dx + dy * dy)

def GetRad(mils):
    return mils * math.pi / 3200

def GetAlpha(target_range):
    # 물리 모델: y = A - B * arcsin(C * x)
    # 최적화된 계수 적용
    A = 1605.2  
    B = 495.5  
    C = 0.000375 

    max_range = 1 / C
    if target_range > max_range:
        return None # 범위 초과

    try:
        val = min(C * target_range, 1.0)
        elevation = A - B * math.asin(val)
        return round(elevation, 0)
    except ValueError:
        return None

# --- 2. 웹사이트 화면 구성 ---
st.set_page_config(page_title="박격포 FDC 계산기", page_icon="💥")
st.title("💥 박격포 사격제원 계산기")

# 탭을 나눠서 깔끔하게 정리
tab1, tab2 = st.tabs(["📍 최초 제원 산출", "🔧 수정 사격 (오차 수정)"])

# === [탭 1] 최초 제원 산출 ===
with tab1:
    st.header("1. 좌표 입력")
    
    col1, col2 = st.columns(2)
    with col1:
        st.subheader("포 위치 (Mortar)")
        mx = st.number_input("포 E (East)", value=29995.0, step=10.0)
        my = st.number_input("포 N (North)", value=37568.0, step=10.0)
        mz = st.number_input("포 고도 (H)", value=607.0, step=1.0)
        
    with col2:
        st.subheader("표적 위치 (Target)")
        tx = st.number_input("표적 E (East)", value=30584.0, step=10.0)
        ty = st.number_input("표적 N (North)", value=39019.0, step=10.0)
        tz = st.number_input("표적 고도 (H)", value=481.0, step=1.0)

    st.subheader("기준 편각")
    base_theta = st.number_input("최초 편각 입력 (mil)", value=2800.0, step=10.0)

    if st.button("🚀 제원 계산하기", type="primary"):
        # 계산 로직
        dx = tx - mx
        dy = ty - my
        dz = tz - mz

        hordis = CalDis(dx, dy)
        findis = hordis + dz / 2
        mtaz = GetMil(dx, dy)
        alpha = GetAlpha(findis)

        st.divider()
        if alpha is None:
            st.error(f"⚠️ 사거리 초과! (계산 거리: {findis:.1f}m)")
        else:
            c1, c2, c3 = st.columns(3)
            c1.metric("수평 사거리", f"{hordis:.0f} m")
            c2.metric("최종 사거리 (고저차 적용)", f"{findis:.0f} m")
            
            st.success(f"🎯 사격 제원")
            st.write(f"**방위각:** {mtaz:.0f} mil")
            st.write(f"**사각(고각):** {alpha:.0f} mil")
            st.info(f"기준 편각 {base_theta:.0f} mil 사용 시")


# === [탭 2] 수정 사격 ===
with tab2:
    st.header("2. 관측 수정 (OTAZ)")
    
    with st.expander("수정 사격 기초 데이터 입력", expanded=True):
        col_a, col_b = st.columns(2)
        with col_a:
            current_dist = st.number_input("현재 사거리 (m)", value=1500.0)
            current_def = st.number_input("현재 편각 (mil)", value=2800.0)
            current_mtaz = st.number_input("현재 사격 방위각 (mil)", value=3200.0)
        with col_b:
            otaz_val = st.number_input("관측소-표적 방위각 (OTAZ)", value=1400.0)

    st.divider()
    st.subheader("오차 입력 (관측소 기준)")
    
    ec1, ec2 = st.columns(2)
    with ec1:
        # Streamlit은 while 루프 대신 입력값이 바뀌면 즉시 재계산합니다.
        err_x = st.number_input("좌우 오차 (우측+, 좌측-)", value=0.0, step=10.0)
    with ec2:
        err_y = st.number_input("거리 오차 (상향/원+, 하향/근-)", value=0.0, step=50.0)

    if err_x != 0 or err_y != 0:
        # 수정 계산 로직
        rot = current_mtaz - otaz_val # 회전각
        
        errdis = CalDis(err_x, err_y)
        errmil_raw = GetMil(err_x, err_y)
        
        # 회전 변환
        corrected_angle_rad = GetRad(errmil_raw - rot)
        
        corr_dx = errdis * math.sin(corrected_angle_rad) # 포 기준 좌우(m)
        corr_dy = errdis * math.cos(corrected_angle_rad) # 포 기준 거리(m)
        
        # 밀 공식 (좌우 수정)
        d_theta = (corr_dx / current_dist) * 1000
        new_theta = current_def + (d_theta * -1)
        
        # 사거리 수정
        new_dist = current_dist + corr_dy
        new_alpha = GetAlpha(new_dist)
        
        st.divider()
        st.subheader("✅ 수정 제원")
        
        r1, r2, r3 = st.columns(3)
        r1.metric("수정 편각", f"{new_theta:.0f} mil", delta=f"{new_theta-current_def:.0f}")
        r2.metric("수정 사거리", f"{new_dist:.0f} m", delta=f"{corr_dy:.0f}")
        
        if new_alpha is None:
            r3.error("사거리 이탈")
        else:
            r3.metric("수정 사각", f"{new_alpha:.0f} mil")
            
    else:
        st.info("오차 값을 입력하면 수정 제원이 자동으로 계산됩니다.")

import math

# ==========================================
# 1. 핵심 계산 함수들 (Math & Physics)
# ==========================================

def GetMil(dx, dy):
    """좌표 차이(dx, dy)를 입력받아 방위각(mil)을 계산"""
    rad = math.atan2(dx, dy)
    if rad <= 0:
        rad += 2 * math.pi
    return (rad * 3200) / math.pi

def CalDis(dx, dy):
    """피타고라스 정리로 수평 거리 계산"""
    return math.sqrt(dx * dx + dy * dy)

def GetRad(mils):
    """밀(mil)을 라디안(radian)으로 변환"""
    return mils * math.pi / 3200

def GetAlpha(target_range):
    """
    물리 모델(Arcsin)을 사용한 사각(고각) 계산
    y = A - B * arcsin(C * x)
    """
    # [중요] 아까 분석 코드로 구한 최적의 계수들을 여기에 넣으세요!
    A = 1605.2   
    B = 495.5    
    C = 0.000375 

    max_range = 1 / C
    if target_range > max_range:
        return None # 범위 초과 시 None 반환

    try:
        val = min(C * target_range, 1.0)
        elevation = A - B * math.asin(val)
        return round(elevation, 0)
    except ValueError:
        return None

# ==========================================
# 2. 메인 실행 로직
# ==========================================

def main():
    print("=== 박격포 사격 제원 계산기 (FDC) ===")
    
    # 1. 좌표 입력 단계
    M = [0, 0, 0] # 포 위치 [E, N, H]
    T = [0, 0, 0] # 타겟 위치 [E, N, H]

    print("\n[1] 포(Mortar) 좌표 입력 (E, N, H 순서)")
    M[0] = float(input("E 좌표: "))
    M[1] = float(input("N 좌표: "))
    M[2] = float(input("고도(H): "))

    print("\n[2] 표적(Target) 좌표 입력 (E, N, H 순서)")
    T[0] = float(input("E 좌표: "))
    T[1] = float(input("N 좌표: "))
    T[2] = float(input("고도(H): "))

    print("\n[3] 기준 편각 입력")
    theta = float(input("편각(mil): "))

    # 2. 최초 제원 산출
    dx = T[0] - M[0]
    dy = T[1] - M[1]
    dz = T[2] - M[2]

    hordis = CalDis(dx, dy)     # 수평 사거리
    findis = hordis + dz / 2    # 고저차 수정 사거리 (간이 공식)
    mtaz = GetMil(dx, dy)       # 방위각
    alpha = GetAlpha(findis)    # 사각(고각)

    if alpha is None:
        print("\n❌ 오류: 사거리가 유효 범위를 벗어났습니다.")
        return

    print("\n" + "="*30)
    print(f"🎯 최초 사격 제원")
    print(f"수평 사거리 : {hordis:.0f} m")
    print(f"최종 사거리 : {findis:.0f} m")
    print(f"편각       : {theta:.0f} mils")
    print(f"방위각     : {mtaz:.0f} mils")
    print(f"사각(고각)  : {alpha:.0f} mils")
    print("="*30)

    # 3. 수정 사격 루프
    print("\n[4] 수정 사격 (OTAZ 기준)")
    otaz = float(input("관측소-표적 방위각(OTAZ) 입력: "))
    
    # 관측소(OT)와 포목선(GT) 사이의 회전각(Rot) 계산
    rot = mtaz - otaz

    while True:
        print("\n--- 수정값 입력 (종료하려면 'q' 입력) ---")
        inp_x = input("좌우 오차 (우측+, 좌측-): ")
        if inp_x.lower() == 'q': break
        
        inp_y = input("거리 오차 (상향+, 하향-): ")
        if inp_y.lower() == 'q': break

        tempx = float(inp_x)
        tempy = float(inp_y)

        # 수정량 계산 로직 (좌표 회전 변환)
        errdis = CalDis(tempx, tempy)
        errmil_raw = GetMil(tempx, tempy) # 오차의 방향
        
        # 관측소 기준 오차를 포 기준 오차로 회전
        corrected_angle_rad = GetRad(errmil_raw - rot)
        
        # 포 기준 수정량(dx, dy) 분해
        corr_dx = errdis * math.sin(corrected_angle_rad) # 좌우 수정량(m)
        corr_dy = errdis * math.cos(corrected_angle_rad) # 거리 수정량(m)

        # 밀 공식 적용 (W = R * mil / 1000) -> mil = W * 1000 / R
        # 편각 수정 (좌우 오차 수정)
        d_theta = (corr_dx / hordis) * 1000
        theta += (d_theta * -1) # 편각은 반대로 돌려야 하므로 -1 곱함

        # 사거리 수정
        findis += corr_dy
        alpha = GetAlpha(findis)

        if alpha is None:
            print("⚠️ 사거리 이탈! 수정 불가능.")
            continue

        print(f"\n✅ 수정된 제원")
        print(f"편각 : {theta:.0f} mils")
        print(f"사각 : {alpha:.0f} mils (거리: {findis:.0f}m)")

if __name__ == "__main__":
    main()

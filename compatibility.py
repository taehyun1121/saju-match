"""
사주 궁합 점수 계산 모듈
saju-tarot-pro/backend/saju.py의 기둥 계산 로직을 재사용하여
100점 만점 궁합 점수 + 항목별 세부 점수를 산출한다.

점수 구조:
  ① 일간 오행 관계  30점
  ② 일지 합충      30점
  ③ 오행 보완성    25점
  ④ 띠 관계        15점
"""

# ── 기둥 계산 (saju-tarot-pro/backend/saju.py 로직 이식) ──────────────────

CHEONGAN = ["갑","을","병","정","무","기","경","신","임","계"]
JIJI     = ["자","축","인","묘","진","사","오","미","신","유","술","해"]

JEOLGI = {
    1:(6,"축"), 2:(4,"인"), 3:(6,"묘"),  4:(5,"진"),
    5:(6,"사"), 6:(6,"오"), 7:(7,"미"),  8:(7,"신"),
    9:(8,"유"), 10:(8,"술"),11:(7,"해"), 12:(7,"자"),
}

def _month_ji(month, day):
    jeolgi_day, ji = JEOLGI[month]
    if day < jeolgi_day:
        prev = 12 if month == 1 else month - 1
        _, ji = JEOLGI[prev]
    return ji

def _day_pillar(year, month, day):
    y, m = year, month
    if m <= 2:
        y -= 1; m += 12
    A = y // 100
    B = 2 - A + A // 4
    jd = int(365.25*(y+4716)) + int(30.6001*(m+1)) + day + B - 1524
    return CHEONGAN[(jd+6)%10], JIJI[(jd+8)%12]

HOUR_JI_TABLE = [
    (23,1,"자"),(1,3,"축"),(3,5,"인"),(5,7,"묘"),
    (7,9,"진"),(9,11,"사"),(11,13,"오"),(13,15,"미"),
    (15,17,"신"),(17,19,"유"),(19,21,"술"),(21,23,"해"),
]

def _hour_ji(hour):
    if hour >= 23 or hour < 1:
        return "자"
    for s, e, ji in HOUR_JI_TABLE:
        if s <= hour < e:
            return ji
    return "자"

# 월간 산출: 연간 오행 기준 인월(1월) 천간 시작 인덱스
_WOL_GAN_BASE = [2, 4, 6, 8, 0]  # 갑·기, 을·경, 병·신, 정·임, 무·계 순

def _month_gan(yeon_gan: str, wol_ji: str) -> str:
    """연간 + 월지 → 월간 산출 (오호둔법)"""
    yeon_idx = CHEONGAN.index(yeon_gan)
    base = _WOL_GAN_BASE[yeon_idx % 5]
    # 인월(寅=인)부터 1월로 계산
    wol_order = ["인","묘","진","사","오","미","신","유","술","해","자","축"]
    wol_num = wol_order.index(wol_ji) if wol_ji in wol_order else 0
    return CHEONGAN[(base + wol_num) % 10]

def _hour_gan(il_gan: str, si_ji: str) -> str:
    """일간 + 시지 → 시간 산출 (오자원두법)"""
    il_idx = CHEONGAN.index(il_gan)
    base = (il_idx % 5) * 2  # 갑·기=0(갑), 을·경=2(병), 병·신=4(무), 정·임=6(경), 무·계=8(임)
    si_order = ["자","축","인","묘","진","사","오","미","신","유","술","해"]
    si_num = si_order.index(si_ji) if si_ji in si_order else 0
    return CHEONGAN[(base + si_num) % 10]

def get_pillars(year, month, day, hour=None):
    """생년월일시 → (일간, 일지, 연지) 반환 (하위호환)"""
    il_gan, il_ji = _day_pillar(year, month, day)
    yeon_ji = JIJI[(year - 4) % 12]
    return il_gan, il_ji, yeon_ji

def _calc_ohaeng(pillars: dict) -> dict:
    """4주 천간+지지에서 오행 분포 계산"""
    # OHAENG_MAP/JIJI_OHAENG은 아래에 정의돼 있으나 여기선 인라인 사용
    gan_oh = {"갑":"木","을":"木","병":"火","정":"火","무":"土","기":"土","경":"金","신":"金","임":"水","계":"水"}
    ji_oh  = {"자":"水","축":"土","인":"木","묘":"木","진":"土","사":"火","오":"Fire","미":"土","신":"金","유":"金","술":"土","해":"水"}
    ji_oh  = {"자":"水","축":"土","인":"木","묘":"木","진":"土","사":"火","오":"火","미":"土","신":"金","유":"金","술":"土","해":"水"}

    counts = {"木": 0, "火": 0, "土": 0, "金": 0, "水": 0}
    for key, pillar in pillars.items():
        if not pillar:
            continue
        for char_type, lookup in [("gan", gan_oh), ("ji", ji_oh)]:
            ch = pillar.get(char_type)
            if ch and ch in lookup:
                counts[lookup[ch]] += 1

    total = sum(counts.values()) or 1
    lacking = [oh for oh, cnt in counts.items() if cnt == 0]
    dominant = max(counts, key=counts.get)

    return {
        "counts": counts,
        "total": total,
        "lacking": lacking,
        "dominant": dominant,
    }

def get_all_pillars(year, month, day, hour=None):
    """생년월일시 → 사주 4주 전체 + 오행 분석 반환"""
    il_gan, il_ji = _day_pillar(year, month, day)

    # 연주
    yeon_gan = CHEONGAN[(year - 4) % 10]
    yeon_ji  = JIJI[(year - 4) % 12]

    # 월주
    wol_ji  = _month_ji(month, day)
    wol_gan = _month_gan(yeon_gan, wol_ji)

    # 시주
    if hour is not None:
        si_ji  = _hour_ji(hour)
        si_gan = _hour_gan(il_gan, si_ji)
    else:
        si_ji = si_gan = None

    pillars = {
        "yeonju": {"gan": yeon_gan, "ji": yeon_ji},
        "wolju":  {"gan": wol_gan,  "ji": wol_ji},
        "ilju":   {"gan": il_gan,   "ji": il_ji},
        "siju":   {"gan": si_gan,   "ji": si_ji} if si_gan else None,
    }
    return pillars, _calc_ohaeng(pillars)


# ── 오행 데이터 ────────────────────────────────────────────────────────────

# 천간 → 오행
OHAENG_MAP = {
    "갑":"木","을":"木","병":"火","정":"Fire",
    "무":"土","기":"土","경":"金","신":"金","임":"水","계":"水",
}
OHAENG_MAP = {
    "갑":"木","을":"木","병":"火","정":"火",
    "무":"土","기":"土","경":"金","신":"金","임":"水","계":"水",
}

# 지지 → 오행
JIJI_OHAENG = {
    "자":"水","축":"土","인":"木","묘":"木","진":"土","사":"火",
    "오":"火","미":"土","신":"金","유":"金","술":"土","해":"水",
}

# 상생: key가 value를 생함
SANGSAENG = {
    "木":"火","火":"土","土":"金","金":"水","水":"木",
}

# 상극: key가 value를 극함
SANGGEUK = {
    "木":"土","土":"水","水":"火","火":"金","金":"木",
}


# ── 지지 합충형 데이터 ─────────────────────────────────────────────────────

# 지지육합 (쌍)
YUKHAM_PAIRS = [
    {"자","축"},{"인","해"},{"묘","술"},{"진","유"},{"사","신"},{"오","미"},
]

# 지지삼합 (세 지지 중 두 개 이상 겹치면 점수)
SAMHAP_GROUPS = [
    {"인","오","술"},  # 화국
    {"해","묘","미"},  # 목국
    {"신","자","진"},  # 수국
    {"사","유","축"},  # 금국
]

# 지지충 (쌍)
JIJI_CHUNG_PAIRS = [
    {"자","오"},{"축","미"},{"인","신"},{"묘","유"},{"진","술"},{"사","해"},
]

# 지지형 (쌍 — 주요 삼형 중 두 지지 기준)
JIJI_HYUNG_PAIRS = [
    {"인","사"},{"사","신"},{"인","신"},  # 인사신 삼형
    {"축","술"},{"술","미"},{"축","미"},  # 축술미 삼형
    {"자","묘"},                          # 자묘 상형
]

# 띠 삼합
TI_SAMHAP = [
    {"자","진","신"},  # 수국
    {"인","오","술"},  # 화국
    {"사","유","축"},  # 금국
    {"해","묘","미"},  # 목국
]

# 띠 충
TI_CHUNG = [
    {"자","오"},{"축","미"},{"인","신"},{"묘","유"},{"진","술"},{"사","해"},
]

# 띠 육합
TI_YUKHAM = [
    {"자","축"},{"인","해"},{"묘","술"},{"진","유"},{"사","신"},{"오","미"},
]


# ── ① 일간 오행 관계 (30점) ────────────────────────────────────────────────

def score_ilgan_ohaeng(gan1: str, gan2: str) -> dict:
    o1 = OHAENG_MAP.get(gan1, "")
    o2 = OHAENG_MAP.get(gan2, "")

    if o1 == o2:
        score = 16
        relation = "비화(比和)"
        desc = f"같은 오행({o1}) — 동질감이 강하고 경쟁심도 생길 수 있음"
    elif SANGSAENG.get(o1) == o2:
        score = 26
        relation = "상생(相生)"
        desc = f"{o1}이 {o2}를 생함 — 내가 상대를 키워주는 관계"
        # 방향 보너스: o2가 o1을 생하는 방향도 맞으면 +3
        if SANGSAENG.get(o2) == o1:
            score += 3
            desc += " (상호 상생 +보너스)"
    elif SANGSAENG.get(o2) == o1:
        score = 26
        relation = "상생(相生)"
        desc = f"{o2}이 {o1}를 생함 — 상대가 나를 키워주는 관계"
    elif SANGGEUK.get(o1) == o2:
        score = 6
        relation = "상극(相克)"
        desc = f"{o1}이 {o2}를 극함 — 내가 상대에게 압박이 될 수 있음"
    elif SANGGEUK.get(o2) == o1:
        score = 6
        relation = "상극(相克)"
        desc = f"{o2}이 {o1}를 극함 — 상대가 나에게 압박이 될 수 있음"
    else:
        score = 11
        relation = "중립"
        desc = "특별한 상생·상극 없음"

    return {"score": min(score, 30), "relation": relation, "desc": desc,
            "ohaeng1": o1, "ohaeng2": o2}


# ── ② 일지 합충 (30점) ────────────────────────────────────────────────────

def score_ilji(ji1: str, ji2: str) -> dict:
    pair = {ji1, ji2}

    # 삼합 여부 (일지가 속한 삼합 그룹 내에서 상대 일지가 같은 그룹이면)
    for group in SAMHAP_GROUPS:
        if ji1 in group and ji2 in group:
            return {"score": 28, "relation": "지지삼합(三合)",
                    "desc": f"{ji1}·{ji2} 삼합 — 깊은 인연, 에너지가 하나로 모임"}

    # 육합
    if pair in YUKHAM_PAIRS:
        return {"score": 24, "relation": "지지육합(六合)",
                "desc": f"{ji1}·{ji2} 육합 — 자연스럽게 끌리는 안정된 관계"}

    # 충
    if pair in JIJI_CHUNG_PAIRS:
        return {"score": 6, "relation": "지지충(沖)",
                "desc": f"{ji1}·{ji2} 충 — 충격과 변화, 강한 자극의 관계"}

    # 형
    if pair in JIJI_HYUNG_PAIRS:
        return {"score": 4, "relation": "지지형(刑)",
                "desc": f"{ji1}·{ji2} 형 — 마찰과 갈등이 잠재된 관계"}

    return {"score": 15, "relation": "중립",
            "desc": "특별한 합충 없음 — 자연스러운 관계"}


# ── ③ 오행 보완성 (25점) ──────────────────────────────────────────────────

def _count_ohaeng(gan: str, ji: str) -> dict:
    """일간+일지 기준 오행 카운트 (간략: 두 글자만)"""
    counts = {"木":0,"火":0,"土":0,"金":0,"水":0}
    for o in [OHAENG_MAP.get(gan,""), JIJI_OHAENG.get(ji,"")]:
        if o in counts:
            counts[o] += 1
    return counts

def score_ohaeng_complement(
    gan1, ji1, yeonji1,
    gan2, ji2, yeonji2,
) -> dict:
    """
    두 사람의 오행 분포(일간+일지+연지 3글자 기준)를 비교해
    서로 부족한 오행을 채워주는 정도를 점수화한다.
    """
    def counts_from(gan, ji, yeonji):
        c = {"木":0,"火":0,"土":0,"金":0,"水":0}
        for src in [OHAENG_MAP.get(gan,""),
                    JIJI_OHAENG.get(ji,""),
                    JIJI_OHAENG.get(yeonji,"")]:
            if src in c:
                c[src] += 1
        return c

    c1 = counts_from(gan1, ji1, yeonji1)
    c2 = counts_from(gan2, ji2, yeonji2)

    complement_score = 0
    detail = []
    for oh in ["木","火","土","金","水"]:
        a, b = c1[oh], c2[oh]
        if a == 0 and b >= 1:
            complement_score += 4
            detail.append(f"1이 부족한 {oh}을 2가 보완")
        elif b == 0 and a >= 1:
            complement_score += 4
            detail.append(f"2가 부족한 {oh}을 1이 보완")
        elif a == 0 and b == 0:
            complement_score -= 1  # 둘 다 없음
        # 둘 다 있으면 중립

    score = max(5, min(25, 13 + complement_score))
    desc = "·".join(detail) if detail else "오행 분포가 비슷하게 겹침"
    return {"score": score, "desc": desc, "counts1": c1, "counts2": c2}


# ── ④ 띠 관계 (15점) ─────────────────────────────────────────────────────

def score_ti(yeonji1: str, yeonji2: str) -> dict:
    pair = {yeonji1, yeonji2}

    for group in TI_SAMHAP:
        if yeonji1 in group and yeonji2 in group:
            return {"score": 14, "relation": "삼합 띠",
                    "desc": f"{yeonji1}띠·{yeonji2}띠 삼합 — 천생연분에 가까운 띠 궁합"}

    if pair in TI_YUKHAM:
        return {"score": 10, "relation": "육합 띠",
                "desc": f"{yeonji1}띠·{yeonji2}띠 육합 — 서로 잘 맞는 편안한 관계"}

    if pair in TI_CHUNG:
        return {"score": 3, "relation": "충 띠",
                "desc": f"{yeonji1}띠·{yeonji2}띠 충 — 자극적인 관계, 에너지 소모 주의"}

    return {"score": 7, "relation": "중립 띠",
            "desc": "특별한 합충 없음"}


# ── 등급 변환 ─────────────────────────────────────────────────────────────

GRADE_TABLE = [
    (85, "S", "운명적 궁합"),
    (70, "A", "잘 맞는 인연"),
    (55, "B", "노력하면 좋은 관계"),
    (40, "C", "성장형 궁합"),
    (0,  "D", "자극적인 관계"),
]

def get_grade(total: int) -> tuple:
    for threshold, grade, label in GRADE_TABLE:
        if total >= threshold:
            return grade, label
    return "D", "자극적인 관계"


# ── 메인 함수 ─────────────────────────────────────────────────────────────

def calc_compatibility(
    year1: int, month1: int, day1: int, hour1: int | None,
    year2: int, month2: int, day2: int, hour2: int | None,
) -> dict:
    """
    두 사람의 생년월일시로 궁합 점수를 산출한다.

    Args:
        year1~hour1: 첫 번째 사람 (hour=None이면 시간 모름)
        year2~hour2: 두 번째 사람

    Returns:
        {
            "total": int,          # 100점 만점
            "grade": str,          # S/A/B/C/D
            "grade_label": str,    # 등급 설명
            "details": {
                "ilgan_ohaeng": {...},   # ① 30점
                "ilji": {...},           # ② 30점
                "ohaeng_complement": {...},  # ③ 25점
                "ti": {...},             # ④ 15점
            },
            "person1": {"ilgan": str, "ilji": str, "yeonji": str},
            "person2": {"ilgan": str, "ilji": str, "yeonji": str},
        }
    """
    gan1, ji1, yj1 = get_pillars(year1, month1, day1, hour1)
    gan2, ji2, yj2 = get_pillars(year2, month2, day2, hour2)

    r1 = score_ilgan_ohaeng(gan1, gan2)
    r2 = score_ilji(ji1, ji2)
    r3 = score_ohaeng_complement(gan1, ji1, yj1, gan2, ji2, yj2)
    r4 = score_ti(yj1, yj2)

    total = r1["score"] + r2["score"] + r3["score"] + r4["score"]
    grade, grade_label = get_grade(total)

    return {
        "total": total,
        "grade": grade,
        "grade_label": grade_label,
        "details": {
            "ilgan_ohaeng": r1,
            "ilji": r2,
            "ohaeng_complement": r3,
            "ti": r4,
        },
        "person1": {"ilgan": gan1, "ilji": ji1, "yeonji": yj1},
        "person2": {"ilgan": gan2, "ilji": ji2, "yeonji": yj2},
    }


# ── 간단 테스트 ───────────────────────────────────────────────────────────

if __name__ == "__main__":
    result = calc_compatibility(
        1990, 3, 15, 10,   # 사람 1
        1992, 8, 22, None, # 사람 2 (시간 모름)
    )
    print(f"총점: {result['total']}점 ({result['grade']} — {result['grade_label']})")
    print()
    d = result["details"]
    print(f"① 일간 오행  {d['ilgan_ohaeng']['score']:2d}/30  {d['ilgan_ohaeng']['relation']} — {d['ilgan_ohaeng']['desc']}")
    print(f"② 일지 합충  {d['ilji']['score']:2d}/30  {d['ilji']['relation']} — {d['ilji']['desc']}")
    print(f"③ 오행 보완  {d['ohaeng_complement']['score']:2d}/25  {d['ohaeng_complement']['desc']}")
    print(f"④ 띠 관계    {d['ti']['score']:2d}/15  {d['ti']['relation']} — {d['ti']['desc']}")
    print()
    print(f"사람1: 일간={result['person1']['ilgan']} 일지={result['person1']['ilji']} 연지={result['person1']['yeonji']}")
    print(f"사람2: 일간={result['person2']['ilgan']} 일지={result['person2']['ilji']} 연지={result['person2']['yeonji']}")

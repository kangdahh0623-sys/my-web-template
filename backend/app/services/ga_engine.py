#이거나이스
# -*- coding: utf-8 -*-
"""
학생 섭취량/영양 제약 + 예산 + 반복 제약 + 선호도/조합을 반영한 GA
- Django에서 optimize_menu(paths, params)만 호출하면 됨.
- 가능해(예산/반복/영양 모두 충족) 해가 없으면 ANY-best라도 반환하고 summary.warning으로 알림.
"""

import os, re, random
from typing import Optional, List, Dict, Tuple
import numpy as np
import pandas as pd

# ================== 기본 하이퍼/상수 ==================
DAYS_IN_MONTH      = 20
DAILY_SLOTS        = ["rice","soup","side","side","side","snack"]
K_PER_DAY          = len(DAILY_SLOTS)
BUDGET_PER_PERSON  = 5370.0

TARGET_KCAL        = 900.0
KCAL_BAND_FRAC     = 0.10  # 900의 ±10% → 810~990

# 칼로리 기준 매크로 목표/허용범위(비율)
MACRO_TARGET_PCT   = {"carbo":0.60, "protein":0.15, "fat":0.25}
MACRO_BOUNDS       = {"carbo":(0.55,0.65), "protein":(0.07,0.20), "fat":(0.15,0.30)}

# 반복 제약
MAX_REPEAT_PER_MONTH = 2
REPEAT_WINDOW_DAYS   = 5

# 선호/가중치
W_PREF    = 0.5    # 학생 선호
W_COOC    = 0.5    # 메뉴쌍(조합)
W_MICRO_SUM        = 0.5
P_MICRO_SHORTFALL  = 0.5

# 소프트 페널티
P_KCAL      = 10.0
P_MACRO     = 1.0
P_REPEAT    = 0.5
P_BUDGET_TOTAL = 10.0

# 스낵 제약(수요일만 허용)
SNACK_CATEGORY   = "snack"
SNACK_LAMBDA     = 1e6
NULL_SNACK_KEY   = "__null_snack__"
NULL_SNACK_NAME  = "(no snack)"
WEEK_DAYS        = 5
def is_snack_allowed_day(day_index: int) -> bool:
    # 월(0)~금(4) 중 수(2)만, 그리고 4주까지만
    week = day_index // WEEK_DAYS
    return (day_index % WEEK_DAYS == 2) and (week < min(4, (DAYS_IN_MONTH // WEEK_DAYS)))

# 하드컷/페널티 상수
STRICT_BUDGET       = True
HARD_FAIL           = 1e12

# GA 설정
POP_SIZE      = 200
GENERATIONS   = 300
CX_RATE       = 0.10
MUT_RATE      = 0.10
SEED          = 42
random.seed(SEED); np.random.seed(SEED)

# 미크로 영양소
MICRO_COLS = ["vit_a","thiamin","riboflavin","niacin","vit_c","vit_d","calcium","iron"]
MICRO_MIN = {
    "vit_a":   284,
    "thiamin": 0.44,
    "riboflavin": 0.57,
    "vit_c":   33.4,
    "calcium": 300,
    "iron":    4.7,
}
MICRO_SCALE = {k: 1.0 for k in MICRO_COLS}  # 정규화 스케일

# ================== 유틸/로딩 ==================
def read_robust(path: str) -> pd.DataFrame:
    for enc in ("utf-8-sig","cp949","utf-8"):
        try: return pd.read_csv(path, encoding=enc)
        except Exception: pass
    return pd.read_csv(path)

def to_num(x):
    return pd.to_numeric(str(x).replace(",","").strip(), errors="coerce")

def norm_key(s:str)->str:
    if pd.isna(s): return ""
    t = str(s).strip()
    t = re.sub(r"[()\[\]{}]", " ", t)
    t = re.sub(r"\s+", " ", t)
    return t.lower()

def find_col(df:pd.DataFrame, cands:List[str])->str:
    lower = {str(c).lower(): c for c in df.columns}
    for c in cands:
        if c in df.columns: return c
        if c.lower() in lower: return lower[c.lower()]
    raise KeyError(f"열을 찾을 수 없음: {cands} | 가진 컬럼: {list(df.columns)}")

def load_cost(path:str)->pd.DataFrame:
    df = read_robust(path)
    m = find_col(df, ["menu","메뉴"])
    p = find_col(df, ["1인_가격","price_per_person","총원가","total_cost_won","가격","price"])
    out = df.rename(columns={m:"menu_raw", p:"price_per_person"})[["menu_raw","price_per_person"]]
    out["price_per_person"] = out["price_per_person"].map(to_num)
    out["menu_key"] = out["menu_raw"].map(norm_key)
    out = (out.groupby("menu_key", as_index=False)
              .agg(menu=("menu_raw", lambda s: s.iloc[0]),
                   price_per_person=("price_per_person","mean")))
    return out

NUTR_MAP = {
    "kcal":"kcal","carbo":"carbo","protein":"protein","fat":"fat",
    "vitaa":"vit_a","vitac":"vit_c","vitad":"vit_d",
    "thiamin":"thiamin","ribo":"riboflavin","niacin":"niacin",
    "calcium":"calcium","fe":"iron"
}
def load_nutr(path:str)->pd.DataFrame:
    df = read_robust(path)
    m = find_col(df, ["menu","메뉴","음식명","메뉴명"])
    df = df.rename(columns={m:"menu_raw"})
    # 컬럼 표준화
    rename = {}
    for c in df.columns:
        lc = str(c).replace("\ufeff","").strip().lower()
        if lc in NUTR_MAP: rename[c] = NUTR_MAP[lc]
    df = df.rename(columns=rename)
    # 결측 보정
    for k in ["kcal","carbo","protein","fat"] + MICRO_COLS:
        if k not in df.columns: df[k] = np.nan
        df[k] = pd.to_numeric(df[k], errors="coerce")
    df["menu_key"] = df["menu_raw"].map(norm_key)
    out = (df.groupby("menu_key", as_index=False)
             .agg(menu=("menu_raw", lambda s: s.iloc[0]),
                  **{k: (k,"mean") for k in ["kcal","carbo","protein","fat"] + MICRO_COLS}))
    return out

CATEGORY_VALUES = {"rice","soup","side"}  # snack은 별도 관리
def norm_category_label(x: str) -> Optional[str]:
    if x is None or (isinstance(x,float) and np.isnan(x)):
        return None
    s = str(x).strip().lower()
    MAP = {
        "밥":"rice","주식":"rice","라이스":"rice",
        "국":"soup","탕":"soup","찌개":"soup","수프":"soup",
        "soup":"soup","stew":"soup","guk":"soup","jjigae":"soup",
        "반찬":"side","사이드":"side","메인":"side","메인반찬":"side","side":"side",
        "간식":"snack","디저트":"snack","dessert":"snack","snack":"snack",
    }
    return MAP.get(s, s if s in CATEGORY_VALUES or s==SNACK_CATEGORY else None)

def load_category(path: Optional[str]) -> pd.DataFrame:
    if not path or not os.path.exists(path):
        return pd.DataFrame(columns=["menu_key","category"])
    df = read_robust(path)
    m = find_col(df, ["menu","메뉴"])
    c = find_col(df, ["category","카테고리","분류"])
    df = df.rename(columns={m:"menu_raw", c:"category"})
    df["menu_key"] = df["menu_raw"].map(norm_key)
    df["category"] = df["category"].map(norm_category_label)
    df = df[df["category"].isin(CATEGORY_VALUES | {SNACK_CATEGORY})]
    return df[["menu_key","category"]]

def build_candidates(cost_df, nutr_df, cat_df):
    df = cost_df.merge(nutr_df, on="menu_key", how="inner", suffixes=("_c","_n"))
    if cat_df is not None and not cat_df.empty:
        df = df.merge(cat_df, on="menu_key", how="left")
    if "category" not in df.columns:
        df["category"] = np.nan
    df = df.rename(columns={"menu_c":"menu"})
    # 필수 결측 제거 + 미크로 결측 0
    df = df.dropna(subset=["price_per_person","kcal","carbo","protein","fat"])
    for k in MICRO_COLS:
        if k not in df.columns: df[k] = 0.0
        df[k] = df[k].fillna(0.0)
    # 카테고리 존재성 체크
    have = set(df["category"].dropna().unique())
    missing = []
    if "rice" not in have: missing.append("rice")
    if "soup" not in have: missing.append("soup")
    if not (("side" in have) or (SNACK_CATEGORY in have)):
        missing.append("side or snack")
    if missing:
        raise RuntimeError(f"다음 카테고리에 후보가 없습니다: {missing}")
    return df.reset_index(drop=True)

def add_null_snack(cand: pd.DataFrame) -> Tuple[pd.DataFrame, int]:
    mask = (cand["category"] == SNACK_CATEGORY) & (cand["menu_key"] == NULL_SNACK_KEY)
    if mask.any():
        return cand, int(np.flatnonzero(mask)[0])
    row = {
        "menu_key": NULL_SNACK_KEY, "menu": NULL_SNACK_NAME, "category": SNACK_CATEGORY,
        "price_per_person": 0.0, "kcal": 0.0, "carbo": 0.0, "protein": 0.0, "fat": 0.0,
    }
    for k in MICRO_COLS: row[k] = 0.0
    cand2 = pd.concat([cand, pd.DataFrame([row])], ignore_index=True)
    return cand2, len(cand2)-1

def load_student_pref_map(path: str) -> Dict[str, float]:
    df = read_robust(path)
    m = find_col(df, ["menu","메뉴","dish","Dish"])
    df = df.rename(columns={m:"menu_raw"})
    df["menu_key"] = df["menu_raw"].map(norm_key)
    if "Weighted_intake_ratio" not in df.columns:
        raise KeyError("CSV에 Weighted_intake_ratio 열이 없음!")
    s = pd.to_numeric(df["Weighted_intake_ratio"], errors="coerce").fillna(0.0)
    w = s.clip(0.0, 1.0)
    return dict(zip(df["menu_key"], w))

def attach_pref_weight(cand: pd.DataFrame, pref_map: Dict[str,float]) -> pd.DataFrame:
    c = cand.copy()
    c["pref_w"] = c["menu_key"].map(pref_map).fillna(0.0).astype(float)
    return c

def load_cooc_df(path: Optional[str]) -> pd.DataFrame:
    if not path or not os.path.exists(path):
        return pd.DataFrame(columns=["pair","weight"])
    df = read_robust(path)
    normcols = {str(c).replace("\ufeff","").strip().lower(): c for c in df.columns}
    def pick(cands):
        for k in cands:
            if k in normcols: return normcols[k]
        return None
    a_col = pick(["menu1","메뉴1","menu_a","메뉴a","a","first","left"])
    b_col = pick(["menu2","메뉴2","menu_b","메뉴b","b","second","right"])
    w_col = pick(["preference","선호도","weight","가중치","score","점수","선호도점수"])
    if not a_col or not b_col or not w_col:
        raise KeyError(f"쌍 선호도 헤더를 찾지 못함. 현재 컬럼: {list(df.columns)}")
    df = df.rename(columns={a_col:"a_raw", b_col:"b_raw", w_col:"weight"})
    df["a"] = df["a_raw"].map(norm_key)
    df["b"] = df["b_raw"].map(norm_key)
    df["weight"] = pd.to_numeric(df["weight"], errors="coerce")
    df = df[df["a"]!=df["b"]].dropna(subset=["a","b","weight"])
    wmin, wmax = df["weight"].min(), df["weight"].max()
    if (wmax > 1.5) or (wmin < 0):
        df["weight"] = (df["weight"] - wmin) / (wmax - wmin + 1e-9)
    df["pair"] = df.apply(lambda r: tuple(sorted([r["a"], r["b"]])), axis=1)
    df = df.groupby("pair", as_index=False).agg(weight=("weight","mean"))
    return df

def build_cooc_index(cand: pd.DataFrame, cooc_df: pd.DataFrame) -> Dict[Tuple[int,int], float]:
    key_to_idx = {k:i for i,k in enumerate(cand["menu_key"])}
    pairs = {}
    for _, r in cooc_df.iterrows():
        a_key, b_key = r["pair"]
        if a_key in key_to_idx and b_key in key_to_idx:
            ia, ib = sorted([key_to_idx[a_key], key_to_idx[b_key]])
            pairs[(ia, ib)] = float(r["weight"])
    return pairs

# ================== 평가/제약 ==================
def day_metrics(indices: List[int], cand: pd.DataFrame)->Dict[str,float]:
    sub = cand.iloc[indices]
    cost  = float(sub["price_per_person"].sum())
    kcal  = float(sub["kcal"].sum())
    carbo = float(sub["carbo"].sum())
    protein = float(sub["protein"].sum())
    fat   = float(sub["fat"].sum())  # 반드시 포함! (is_feasible_day에서 g-비율 계산)

    # 칼로리 기준 매크로 비중
    prot_kcal = protein * 4.0
    carb_kcal = carbo   * 4.0
    fat_kcal  = fat     * 9.0
    macro_kcal_sum = prot_kcal + carb_kcal + fat_kcal
    pct_den = kcal if kcal > 0 else macro_kcal_sum
    carb_pct_cal = carb_kcal / max(pct_den, 1e-9)
    prot_pct_cal = prot_kcal / max(pct_den, 1e-9)
    fat_pct_cal  = fat_kcal  / max(pct_den, 1e-9)

    # 미크로 정규화 평균
    micros = {k: float(sub[k].sum()) for k in MICRO_COLS}
    micro_norms = []
    for k, v in micros.items():
        scale = max(MICRO_SCALE.get(k, 1.0), 1e-9)
        micro_norms.append(min(v/scale, 1.0))
    micro_norm_mean = float(np.mean(micro_norms)) if micro_norms else 0.0

    d = dict(
        cost=cost, kcal=kcal, carbo=carbo, protein=protein, fat=fat,
        carb_pct_cal=carb_pct_cal, prot_pct_cal=prot_pct_cal, fat_pct_cal=fat_pct_cal,
        micro_norm=micro_norm_mean
    )
    for k, v in micros.items():
        d[f"micro_{k}"] = v
    return d

def is_feasible_day(m: dict) -> bool:
    # 칼로리 밴드
    kcal = float(m.get("kcal", 0.0))
    lo = TARGET_KCAL * (1.0 - KCAL_BAND_FRAC)
    hi = TARGET_KCAL * (1.0 + KCAL_BAND_FRAC)
    if not (lo <= kcal <= hi): return False

    # g-기준 매크로 비율 (칼로리 기준 단백질 상한은 별도)
    c = float(m.get("carbo", 0.0))
    p = float(m.get("protein", 0.0))
    f = float(m.get("fat", 0.0))
    den = c + p + f
    if den <= 0: return False
    carb_g = c/den; prot_g = p/den; fat_g = f/den
    for k, pct in [("carbo",carb_g),("protein",prot_g),("fat",fat_g)]:
        lo_b, hi_b = MACRO_BOUNDS[k]
        if not (lo_b <= pct <= hi_b): return False

    # 단백질 칼로리 비중 < 0.20
    if float(m.get("prot_pct_cal", 0.0)) >= 0.20: return False

    # 미크로 하한
    for k, tgt in MICRO_MIN.items():
        if tgt and float(m.get(f"micro_{k}", 0.0)) < float(tgt):
            return False
    return True

def violates_repeat_limits(ch: np.ndarray) -> bool:
    # 1) 월간 총횟수 제한
    counts = np.bincount(ch, minlength=int(ch.max())+1)
    if np.any(counts > MAX_REPEAT_PER_MONTH): return True
    # 2) 근접 재등장 (일 단위)
    if REPEAT_WINDOW_DAYS > 1:
        days = ch.reshape(DAYS_IN_MONTH, K_PER_DAY)
        last = {}
        for d in range(DAYS_IN_MONTH):
            for idx in days[d].tolist():  # set() 쓰지 않음
                if idx in last and (d - last[idx]) < REPEAT_WINDOW_DAYS:
                    return True
                last[idx] = d
    return False

def is_feasible_chrom(ch: np.ndarray, cand: pd.DataFrame) -> bool:
    if violates_repeat_limits(ch): return False
    # 월 예산
    total_budget = float(BUDGET_PER_PERSON) * float(DAYS_IN_MONTH)
    month_cost = float(cand["price_per_person"].values[ch].sum())
    if month_cost > total_budget: return False
    # 일별 제약
    days = ch.reshape(DAYS_IN_MONTH, K_PER_DAY)
    for d in range(DAYS_IN_MONTH):
        if not is_feasible_day(day_metrics(days[d].tolist(), cand)):
            return False
    return True

def cooc_score(indices: List[int], cooc_pairs: Dict[Tuple[int,int],float])->float:
    if len(indices) < 2 or not cooc_pairs: return 0.0
    s=0.0
    for i in range(len(indices)):
        for j in range(i+1, len(indices)):
            a,b = sorted([indices[i], indices[j]])
            s += cooc_pairs.get((a,b), 0.0)
    return s

def fitness(chrom: np.ndarray, cand: pd.DataFrame, cooc_pairs, NULL_SNACK_IDX:int) -> float:
    days = chrom.reshape(DAYS_IN_MONTH, K_PER_DAY)
    prices = cand["price_per_person"].values
    pref   = cand["pref_w"].values if "pref_w" in cand.columns else np.zeros(len(cand), dtype=float)

    # 월 예산 빠른 하드컷
    if STRICT_BUDGET:
        cost_quick = float(prices[chrom].sum())
        if cost_quick > (BUDGET_PER_PERSON * DAYS_IN_MONTH):
            return -HARD_FAIL

    score = 0.0

    # 반복 벌점
    counts = np.bincount(chrom, minlength=len(cand))
    over_counts = np.maximum(0, counts - MAX_REPEAT_PER_MONTH).sum()
    score -= P_REPEAT * float(over_counts)

    if REPEAT_WINDOW_DAYS > 1:
        last = {}
        rep = 0
        for d in range(DAYS_IN_MONTH):
            for idx in days[d].tolist():
                if idx in last and (d - last[idx]) < REPEAT_WINDOW_DAYS:
                    rep += 1
                last[idx] = d
        score -= P_REPEAT * float(rep)

    month_cost = 0.0
    snack_pen  = 0.0
    lo = TARGET_KCAL * (1.0 - KCAL_BAND_FRAC)
    hi = TARGET_KCAL * (1.0 + KCAL_BAND_FRAC)

    for d in range(DAYS_IN_MONTH):
        idxs = days[d].tolist()
        m = day_metrics(idxs, cand)
        month_cost += float(m.get("cost", 0.0))

        # 하드컷: 단백질 칼로리 비중 < 20%, 칼로리 밴드
        if float(m.get("prot_pct_cal", 0.0)) >= 0.20: return -HARD_FAIL
        k = float(m.get("kcal", 0.0))
        if (k < lo) or (k > hi): return -HARD_FAIL

        # 소프트: 칼로리/매크로 편차, 미크로, 선호/조합
        score -= P_KCAL * (k - TARGET_KCAL) ** 2
        score -= P_MACRO * (
            abs(float(m.get("carb_pct_cal", 0.0)) - MACRO_TARGET_PCT["carbo"]) +
            abs(float(m.get("prot_pct_cal", 0.0)) - MACRO_TARGET_PCT["protein"]) +
            abs(float(m.get("fat_pct_cal",  0.0)) - MACRO_TARGET_PCT["fat"])
        )
        score += W_MICRO_SUM * float(m.get("micro_norm", 0.0))
        shortfalls = []
        for kk in MICRO_COLS:
            tgt = MICRO_MIN.get(kk)
            if tgt:
                val = float(m.get(f"micro_{kk}", 0.0))
                shortfalls.append(max(0.0, (tgt - val) / tgt))
        if shortfalls:
            score -= P_MICRO_SHORTFALL * float(np.mean(shortfalls))

        score += W_COOC * cooc_score(idxs, cooc_pairs)
        score += W_PREF * float(pref[idxs].sum())

        # 스낵 요일 제약
        snack_is_real = (days[d, 5] != NULL_SNACK_IDX)
        snack_pen += 0 if (snack_is_real == is_snack_allowed_day(d)) else 1

    # 월간 벌점: 스낵/예산
    score -= SNACK_LAMBDA * snack_pen
    total_budget = BUDGET_PER_PERSON * DAYS_IN_MONTH
    over = max(0.0, month_cost - total_budget)
    score -= P_BUDGET_TOTAL * (over**2) / (total_budget**2)

    return float(score)

# ================== GA ==================
def cat_index_lists(cand: pd.DataFrame) -> Dict[str, np.ndarray]:
    cat = cand["category"].values
    return {
        "rice":  np.where(cat == "rice")[0],
        "soup":  np.where(cat == "soup")[0],
        "side":  np.where(cat == "side")[0],
        "snack": np.where(cat == SNACK_CATEGORY)[0],
    }

def init_population(cand: pd.DataFrame, cat_idx: Dict[str, np.ndarray], NULL_SNACK_IDX:int) -> np.ndarray:
    pop = np.empty((POP_SIZE, DAYS_IN_MONTH*K_PER_DAY), dtype=int)

    kcal = cand["kcal"].values.astype(float)
    prot = cand["protein"].values.astype(float)
    carb = cand["carbo"].values.astype(float)
    price= cand["price_per_person"].values.astype(float)

    # 밀도 지표
    prot_den = (prot*4.0) / np.maximum(kcal, 1e-9)
    carb_den = (carb*4.0) / np.maximum(kcal, 1e-9)

    # 카테고리별(단백질 비중 낮은 순) + 탄수↑/단백질↓ 강화 리스트
    r_sorted = cat_idx["rice"][np.argsort(prot_den[cat_idx["rice"]])]
    s_sorted = cat_idx["soup"][np.argsort(prot_den[cat_idx["soup"]])]
    side_sorted = cat_idx["side"][np.argsort(prot_den[cat_idx["side"]])]
    side_boost  = cat_idx["side"][np.argsort(-(carb_den[cat_idx["side"]] - prot_den[cat_idx["side"]]))]

    snack_all  = list(cat_idx["snack"])
    snack_real = [i for i in snack_all if i != NULL_SNACK_IDX]

    lo = TARGET_KCAL*(1-KCAL_BAND_FRAC)
    hi = TARGET_KCAL*(1+KCAL_BAND_FRAC)
    target_cost = BUDGET_PER_PERSON
    cost_slack  = 0.20

    # 최근 사용일 기록 (초기해에서도 반복 간격 벌리기)
    last_day_global: Dict[int,int] = {}

    def pick_from(pool, used_today: set, d: int):
        # 최근 REPEAT_WINDOW_DAYS 내 사용 안 한 후보를 우선
        choices = [x for x in pool
                   if x not in used_today and ((x not in last_day_global) or (d - last_day_global[x]) >= REPEAT_WINDOW_DAYS)]
        if not choices:
            choices = [x for x in pool if x not in used_today]  # 백업
        return int(np.random.choice(choices))

    def day_ok(tmp_idx):
        dk = float(kcal[tmp_idx].sum())
        dp = float(prot[tmp_idx].sum())
        if not (lo <= dk <= hi): return False
        if dk <= 0: return False
        if (4.0*dp/dk) >= 0.20: return False
        day_cost = float(price[tmp_idx].sum())
        if abs(day_cost - target_cost) > target_cost*cost_slack: return False
        return True

    for i in range(POP_SIZE):
        genes=[]
        for d in range(DAYS_IN_MONTH):
            tries = 0
            while True:
                tries += 1
                half_r = max(1, len(r_sorted)//2)
                half_s = max(1, len(s_sorted)//2)
                half_side = max(3, len(side_sorted)//2)

                used_today = set()
                r = pick_from(r_sorted[:half_r], used_today, d); used_today.add(r)
                s = pick_from(s_sorted[:half_s], used_today, d); used_today.add(s)
                sides=[]
                for _ in range(3):
                    si = pick_from(side_sorted[:half_side], used_today, d)
                    sides.append(si); used_today.add(si)
                sn = np.random.choice(snack_real) if (snack_real and is_snack_allowed_day(d)) else NULL_SNACK_IDX
                tmp = [r, s, *sides, sn]

                # 빠른 스왑으로 미세조정
                inner = 0
                while inner < 40:
                    inner += 1
                    dk = float(kcal[tmp].sum()); dp = float(prot[tmp].sum())
                    day_cost = float(price[tmp].sum())

                    if dk > 0 and (4.0*dp/dk) >= 0.20:
                        si = 2 + np.argmax(prot[tmp[2:5]])
                        cand_side = pick_from(side_sorted[:min(60, len(side_sorted))], set(tmp), d)
                        tmp[si] = cand_side
                        continue
                    if dk < lo:
                        si = 2 + np.argmin(kcal[tmp[2:5]])
                        cand_side = pick_from(side_boost[:min(80, len(side_boost))], set(tmp), d)
                        tmp[si] = cand_side
                        continue
                    if dk > hi:
                        si = 2 + np.argmax(kcal[tmp[2:5]])
                        cand_side = pick_from(side_sorted[:min(80, len(side_sorted))], set(tmp), d)
                        tmp[si] = cand_side
                        continue
                    if abs(day_cost - target_cost) > target_cost*cost_slack:
                        if day_cost > target_cost:
                            si = 2 + np.argmax(price[tmp[2:5]])
                            cand_side = pick_from(side_sorted[:min(80, len(side_sorted))], set(tmp), d)
                            tmp[si] = cand_side
                        else:
                            si = 2 + np.argmin(price[tmp[2:5]])
                            cand_side = pick_from(side_boost[:min(80, len(side_boost))], set(tmp), d)
                            tmp[si] = cand_side
                        continue
                    break

                if day_ok(tmp) or tries > 80:
                    genes.extend(tmp)
                    # 최종 채택 → 최근사용일 갱신
                    for idx in tmp:
                        last_day_global[idx] = d
                    break

        pop[i] = np.array(genes, dtype=int)
    return pop

def tournament_select(pop: np.ndarray, fits: np.ndarray, t:int=3) -> np.ndarray:
    N = len(pop)
    out = np.empty_like(pop)
    f = np.array(fits, dtype=float)
    f[~np.isfinite(f)] = -1e30
    for i in range(N):
        cand = np.random.randint(0, N, size=t)
        best = cand[np.argmax(f[cand])]
        out[i] = pop[best]
    return out

def crossover_daywise(p1: np.ndarray, p2: np.ndarray):
    if np.random.rand() > CX_RATE: return p1.copy(), p2.copy()
    days_len = p1.size // K_PER_DAY
    if days_len <= 1: return p1.copy(), p2.copy()
    cut_day = np.random.randint(1, days_len)
    cut = cut_day * K_PER_DAY
    return np.concatenate([p1[:cut], p2[cut:]]), np.concatenate([p2[:cut], p1[cut:]])

def mutate_category(ch: np.ndarray, cat_idx: Dict[str, np.ndarray], NULL_SNACK_IDX:int) -> np.ndarray:
    ch = ch.copy()
    snack_all  = list(cat_idx["snack"])
    snack_real = [i for i in snack_all if i != NULL_SNACK_IDX]
    for pos in range(ch.size):
        if np.random.rand() < MUT_RATE:
            slot = DAILY_SLOTS[pos % K_PER_DAY]
            day  = pos // K_PER_DAY
            if slot == "snack":
                ch[pos] = np.random.choice(snack_real) if (snack_real and is_snack_allowed_day(day)) else NULL_SNACK_IDX
            else:
                ch[pos] = np.random.choice(cat_idx[slot])
    return ch

def run_ga(cand, cooc_pairs, NULL_SNACK_IDX):
    cat_idx = cat_index_lists(cand)
    pop = init_population(cand, cat_idx, NULL_SNACK_IDX)
    fits = np.array([fitness(ind, cand, cooc_pairs, NULL_SNACK_IDX) for ind in pop], dtype=float)

    best_i = int(fits.argmax())
    best_any = pop[best_i].copy()
    best_any_fit = float(fits[best_i])

    best_feas, best_feas_fit = (best_any.copy(), best_any_fit) if is_feasible_chrom(best_any, cand) else (None, -np.inf)

    for gen in range(GENERATIONS):
        sel = tournament_select(pop, fits)
        nxt=[]
        for i in range(0, POP_SIZE, 2):
            p1 = sel[i]; p2 = sel[i+1 if i+1<POP_SIZE else 0]
            c1,c2 = crossover_daywise(p1,p2)
            c1 = mutate_category(c1, cat_idx, NULL_SNACK_IDX)
            c2 = mutate_category(c2, cat_idx, NULL_SNACK_IDX)
            nxt.extend([c1,c2])
        pop = np.array(nxt[:POP_SIZE], dtype=int)

        fits = np.array([fitness(ind, cand, cooc_pairs, NULL_SNACK_IDX) for ind in pop], dtype=float)

        # any-best
        cur_best_i = int(fits.argmax())
        if fits[cur_best_i] > best_any_fit:
            best_any_fit = float(fits[cur_best_i]); best_any = pop[cur_best_i].copy()

        # feasible-best
        for i in range(POP_SIZE):
            if fits[i] > best_feas_fit and is_feasible_chrom(pop[i], cand):
                best_feas = pop[i].copy(); best_feas_fit = float(fits[i])

        # 엘리트 보존
        pop[int(fits.argmin())] = (best_feas if best_feas is not None else best_any).copy()

    final = best_feas if best_feas is not None else best_any
    final_fit = best_feas_fit if best_feas is not None else best_any_fit
    return final, final_fit

# ================== Django에서 쓰는 래퍼 ==================
def optimize_menu(paths: dict, params: dict):
    import os
    import numpy as np
    import pandas as pd

    # ✅ global 구문을 괄호 없이 한 줄로
    global DAYS_IN_MONTH, BUDGET_PER_PERSON, TARGET_KCAL
    global MACRO_BOUNDS, MACRO_TARGET_PCT, STRICT_BUDGET
    global W_PREF, P_REPEAT, P_BUDGET_TOTAL, P_MACRO, P_KCAL
    global P_MICRO_SHORTFALL, W_MICRO_SUM, W_COOC, MICRO_SCALE

    # 일수/예산/칼로리
    if "days" in params:         DAYS_IN_MONTH     = int(params["days"])
    if "budget_won" in params:   BUDGET_PER_PERSON = float(params["budget_won"])
    if "target_kcal" in params:  TARGET_KCAL       = float(params["target_kcal"])
    if "STRICT_BUDGET" in params: STRICT_BUDGET    = bool(params["STRICT_BUDGET"])

    # 매크로 범위·목표 (% 입력을 0~1로 변환)
    def _pair(p): return (float(p[0])/100.0, float(p[1])/100.0)
    def _mid(p):  return (float(p[0]) + float(p[1]))/200.0
    _b = dict(MACRO_BOUNDS); _t = dict(MACRO_TARGET_PCT)
    if "carb_range" in params:
        _b["carbo"] = _pair(params["carb_range"]); _t["carbo"] = _mid(params["carb_range"])
    if "prot_range" in params:
        _b["protein"] = _pair(params["prot_range"]); _t["protein"] = _mid(params["prot_range"])
    if "fat_range"  in params:
        _b["fat"]    = _pair(params["fat_range"]);  _t["fat"]    = _mid(params["fat_range"])
    MACRO_BOUNDS, MACRO_TARGET_PCT = _b, _t

    # (선택) 가중치/패널티 튜닝
    W_PREF            = float(params.get("W_PREF",            W_PREF))
    P_REPEAT          = float(params.get("P_REPEAT",          P_REPEAT))
    P_BUDGET_TOTAL    = float(params.get("P_BUDGET_TOTAL",    P_BUDGET_TOTAL))
    P_MACRO           = float(params.get("P_MACRO",           P_MACRO))
    P_KCAL            = float(params.get("P_KCAL",            P_KCAL))
    P_MICRO_SHORTFALL = float(params.get("P_MICRO_SHORTFALL", P_MICRO_SHORTFALL))
    W_MICRO_SUM       = float(params.get("W_MICRO_SUM",       W_MICRO_SUM))
    W_COOC            = float(params.get("W_COOC",            W_COOC))

    # ====== 데이터 로드 ======
    cost = load_cost(paths["price"])
    nutr = load_nutr(paths["nutr"])
    catf = load_category(paths.get("cat"))

    cand = build_candidates(cost, nutr, catf)
    cand, NULL_SNACK_IDX = add_null_snack(cand)

    # 학생 선호도(없으면 0)
    pref_path = paths.get("pref")
    if pref_path and os.path.exists(pref_path):
        try:
            pref_map = load_student_pref_map(pref_path)
            cand = attach_pref_weight(cand, pref_map)
        except Exception:
            cand["pref_w"] = 0.0
    else:
        cand["pref_w"] = 0.0

    # 미크로 스케일(정규화용) 업데이트
    for k in MICRO_COLS:
        if k in cand.columns:
            MICRO_SCALE[k] = max(1e-9, float(cand[k].max()) * K_PER_DAY)

    # 메뉴쌍 선호(없으면 빈 딕셔너리)
    cooc_pairs = {}
    cooc_path = paths.get("cooc")
    if cooc_path and os.path.exists(cooc_path):
        try:
            cooc_df = load_cooc_df(cooc_path)
            cooc_pairs = build_cooc_index(cand, cooc_df)
        except Exception:
            cooc_pairs = {}

    # ====== GA 실행 ======
    best_ch, best_fit = run_ga(cand, cooc_pairs, NULL_SNACK_IDX)
    if best_ch is None:
        raise RuntimeError("해를 찾지 못함")

    # ====== 결과 표 생성 ======
    days = best_ch.reshape(DAYS_IN_MONTH, len(DAILY_SLOTS))
    pref_vec = cand["pref_w"].values if "pref_w" in cand.columns else np.zeros(len(cand))

    rows = []
    for d in range(DAYS_IN_MONTH):
        idxs  = days[d].tolist()
        names = [cand.iloc[i]["menu"] for i in idxs]
        m     = day_metrics(idxs, cand)

        rows.append({
            "day": d+1,
            "rice":  names[0],
            "soup":  names[1],
            "side1": names[2],
            "side2": names[3],
            "side3": names[4],
            "snack": names[5],
            "day_cost":      float(m.get("cost", 0.0)),
            "day_kcal":      float(m.get("kcal", 0.0)),
            "carbo_g":       float(m.get("carbo", 0.0)),
            "protein_g":     float(m.get("protein", 0.0)),
            "carb_pct_cal":  float(m.get("carb_pct_cal", 0.0))*100.0,
            "prot_pct_cal":  float(m.get("prot_pct_cal", 0.0))*100.0,
            "fat_pct_cal":   float(m.get("fat_pct_cal",  0.0))*100.0,
            "day_pref_sum":  float(pref_vec[idxs].sum()),
        })

    plan_df = pd.DataFrame(rows)

    # ====== 요약(합계행 추가 전에 계산!) ======
    days_only = plan_df.copy()
    total_cost = float(pd.to_numeric(days_only["day_cost"], errors="coerce").sum(skipna=True))
    avg_kcal   = float(pd.to_numeric(days_only["day_kcal"], errors="coerce").mean(skipna=True))

    # 하단 합계/평균 행 추가(표시에만 사용)
    sum_row = {
        "day": "합계", "rice":"", "soup":"", "side1":"", "side2":"", "side3":"", "snack":"",
        "day_cost":      total_cost,
        "day_kcal":      avg_kcal,
        "carbo_g":       float(pd.to_numeric(days_only["carbo_g"], errors="coerce").mean(skipna=True)),
        "protein_g":     float(pd.to_numeric(days_only["protein_g"], errors="coerce").mean(skipna=True)),
        "carb_pct_cal":  float(pd.to_numeric(days_only["carb_pct_cal"], errors="coerce").mean(skipna=True)),
        "prot_pct_cal":  float(pd.to_numeric(days_only["prot_pct_cal"], errors="coerce").mean(skipna=True)),
        "fat_pct_cal":   float(pd.to_numeric(days_only["fat_pct_cal"], errors="coerce").mean(skipna=True)),
        "day_pref_sum":  float(pd.to_numeric(days_only["day_pref_sum"], errors="coerce").sum(skipna=True)),
    }
    plan_df = pd.concat([plan_df, pd.DataFrame([sum_row])], ignore_index=True)

    # 가능해(하드 제약 충족) 여부
    feasible = bool(is_feasible_chrom(best_ch, cand))

    summary = {
        "days": int(DAYS_IN_MONTH),
        "budget_won": float(BUDGET_PER_PERSON),
        "target_kcal": float(TARGET_KCAL),
        "macro_bounds": {
            "carbo": tuple(MACRO_BOUNDS["carbo"]),
            "protein": tuple(MACRO_BOUNDS["protein"]),
            "fat": tuple(MACRO_BOUNDS["fat"]),
        },
        "total_cost": total_cost,   # 합계행 포함 금지
        "avg_kcal":   avg_kcal,
        "feasible":   feasible,
        # "best_score": float(best_fit),  # 필요 시 표시
        # "warning": (None if feasible else "가능해 해를 찾지 못해 근사해(ANY-best)를 사용했습니다. 제약 완화/예산 조정/메뉴 확장을 고려하세요."),
    }

    return plan_df, summary


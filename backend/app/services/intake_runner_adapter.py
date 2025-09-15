# backend/app/services/intake_runner_adapter.py
from __future__ import annotations
import os, math, re
from typing import Dict, List, Tuple, Optional
from collections import defaultdict

import numpy as np
import pandas as pd
import cv2
import torch
from ultralytics import YOLO
import torch
from app.core.config import settings


# ==== 네 프로젝트의 상수/스키마와 동일 ====
TRAY_NUM   = 425          # tray 클래스 id
H_CONE     = 4.0
H_CUT      = 2.0
SCHOOL_TRAY_AREA = {
    "상인중학교": 28*22, "동평중학교": 28*22,
    "구암고등학교": 37*29, "영진고등학교": 37*29
}
DEFAULT_TRAY_AREA = 37*29  # cm^2

IMG_EXTS = (".jpg", ".jpeg", ".png", ".bmp", ".tif", ".tiff")
NAME_RE = re.compile(r'^[^_]+_(?P<id>[^_]+)_(?P<date>\d{4,8})_(?P<flag>[abAB])$', re.UNICODE)

# ==== 외부 영양/밀도 사전 (네 경로에 맞춰 환경변수로 주입 가능) ====
from app.vendor.ultralytics_main.meta import food_nutrition_dict, food_density

# ==== YOLO 모델 캐시 (재로딩 방지) ====
_MODEL_CACHE: Dict[str, YOLO] = {}

def _get_model(weights_path: str) -> YOLO:
    wp = os.path.abspath(weights_path)
    m = _MODEL_CACHE.get(wp)
    if m is None:
        m = YOLO(wp)
        _MODEL_CACHE[wp] = m
    return m

def _parse_name_from_path(p: str) -> Tuple[str,str,str]:
    stem = os.path.splitext(os.path.basename(p))[0]
    m = NAME_RE.match(stem)
    if not m: return "", "", ""
    gd = m.groupdict()
    return gd.get("id") or "", gd.get("date") or gd.get("week") or "", (gd.get("flag") or "").lower()

def _area_px_raster(image_hw, polygon_points):
    if polygon_points is None: return 0.0
    poly = np.asarray(polygon_points, dtype=np.int32).reshape(-1, 2)
    if poly.shape[0] < 3: return 0.0
    H, W = image_hw
    mask = np.zeros((H, W), dtype=np.uint8)
    cv2.fillPoly(mask, [poly], 1)
    return float(cv2.countNonZero(mask))

def _frustum_volume(r1, h1, h2):
    if h1 <= 0 or h2 <= 0 or r1 <= 0: return 0.0
    r2 = r1 * (h2 / h1)
    return (1.0/3.0)*math.pi*h2*(r1*r1 + r1*r2 + r2*r2)

def _dict_by_name(names, vols):
    d = defaultdict(float)
    for n, v in zip(names, vols):
        d[n] += float(v)
    return d

@torch.inference_mode()
def _predict_safe(model, img, imgsz=None, conf=None, max_det=None):
    return model.predict(
        source=img,
        imgsz=imgsz or settings.YOLO_IMGSZ,
        conf=conf if conf is not None else settings.YOLO_CONF,
        max_det=max_det or settings.YOLO_MAX_DET,
        device=settings.YOLO_DEVICE,
        half=(settings.YOLO_DEVICE != "cpu"),
        save=False, verbose=False, stream=False, retina_masks=False, augment=False
    )[0]


def _volumes_from_result(res, H, W, real_tray_area, tray_class_id, h_cone=H_CONE, h_cut=H_CUT):
    vols, names = [], []
    if res is None or res.masks is None or res.masks.xy is None or res.boxes is None or res.boxes.cls is None:
        return vols, names

    classes  = res.boxes.cls.cpu().numpy().astype(np.int32)
    masks_xy = res.masks.xy
    names_map = res.names if hasattr(res, "names") else {}

    tray_area_px = 0.0
    try:
        tray_pos = np.where(classes == tray_class_id)[0]
        if len(tray_pos) > 0:
            tray_idx = int(tray_pos[0])
            tray_poly = masks_xy[tray_idx]
            tray_area_px = _area_px_raster((H, W), tray_poly)
    except Exception:
        tray_area_px = 0.0

    if tray_area_px <= 0:
        for i, c in enumerate(classes):
            if int(c) == tray_class_id: continue
            names.append(names_map.get(int(c), str(int(c))))
            vols.append(0.0)
        return vols, names

    for i, c in enumerate(classes):
        if int(c) == tray_class_id: continue
        names.append(names_map.get(int(c), str(int(c))))
        poly = masks_xy[i]
        if poly is None or (isinstance(poly, np.ndarray) and len(poly) < 3):
            vols.append(0.0); continue
        area_px   = _area_px_raster((H, W), poly)
        real_area = (area_px / float(tray_area_px)) * float(real_tray_area)  # cm^2
        radius    = math.sqrt(max(real_area, 0.0) / math.pi)
        vols.append(_frustum_volume(radius, h_cone, h_cut))
    return vols, names

def _nutr_from_grams(dish: str, grams: float) -> Dict[str, float]:
    if grams <= 0: return {}
    nut = food_nutrition_dict.get(dish)
    if nut is None: return {}
    f = grams / 100.0
    kcal, carbo, protein, fat, vitA, thiamine, riboflavin, niacin, vitC, vitD, calcium, iron = [
        f * float(x) for x in nut
    ]
    return {
        "kcal":kcal, "carbo":carbo, "protein":protein, "fat":fat,
        "vitA":vitA, "thiamin":thiamine, "riboflavin":riboflavin, "niacin":niacin,
        "vitC":vitC, "vitD":vitD, "calcium":calcium, "iron":iron
    }

def analyze_pair_with_your_logic(
    before_path: str,
    after_path: str,
    school_name: str,
    weights_path: str,
    imgsz: int = 224,
    conf: float = 0.5,
    max_det: int = 20,
) -> Tuple[pd.DataFrame, Dict[str, float], object, object]:
    """네 per_dish_runner 로직 그대로. 반환값에 res_b/res_a도 함께 넘겨서 시각화에 사용."""
    model = _get_model(weights_path)

    res_b = _predict_safe(model, before_path, imgsz=imgsz, conf=conf, max_det=max_det)
    res_a = _predict_safe(model, after_path,  imgsz=imgsz, conf=conf, max_det=max_det)

    img_b = cv2.imread(before_path); Hb, Wb = (img_b.shape[0], img_b.shape[1]) if img_b is not None else (0,0)
    img_a = cv2.imread(after_path);  Ha, Wa = (img_a.shape[0], img_a.shape[1]) if img_a is not None else (0,0)

    real_area = SCHOOL_TRAY_AREA.get(school_name, DEFAULT_TRAY_AREA)

    b_vols, b_names = _volumes_from_result(res_b, Hb, Wb, real_area, TRAY_NUM, H_CONE, H_CUT)
    a_vols, a_names = _volumes_from_result(res_a, Ha, Wa, real_area, TRAY_NUM, H_CONE, H_CUT)

    b_dict = _dict_by_name(b_names, b_vols)
    a_dict = _dict_by_name(a_names, a_vols)

    pid_b, date_b, _ = _parse_name_from_path(before_path)
    pid_a, date_a, _ = _parse_name_from_path(after_path)
    pid  = pid_b or pid_a
    date = date_b or date_a

    rows = []
    dishes = sorted(set(b_dict) | set(a_dict))
    for dish in dishes:
        bv = float(b_dict.get(dish, 0.0))
        av = float(a_dict.get(dish, 0.0))
        iv = max(bv - av, 0.0)

        den = food_density.get(dish)
        if den is None:
            gb = ga = gi = np.nan
        else:
            gb = bv * den; ga = av * den; gi = iv * den

        leftover_ratio = (av / bv) if bv > 0 else np.nan
        intake_ratio   = (iv / bv) if bv > 0 else np.nan

        nutr = _nutr_from_grams(dish, gi if (isinstance(gi, (int,float)) and not np.isnan(gi)) else 0.0)

        row = {
            "pid": pid, "date": date,
            "before_file": os.path.basename(before_path),
            "after_file":  os.path.basename(after_path),
            "dish": dish,
            "vol_before_cm3": bv,
            "vol_after_cm3":  av,
            "vol_intake_cm3": iv,
            "g_before": gb, "g_after": ga, "g_intake": gi,
            "leftover_ratio": leftover_ratio, "intake_ratio": intake_ratio,
        }
        row.update(nutr)
        rows.append(row)

    df = pd.DataFrame(rows)

    totals: Dict[str, float] = {}
    if not df.empty:
        for k in ["g_intake","kcal","carbo","protein","fat","vitA","thiamin","riboflavin","niacin","vitC","vitD","calcium","iron"]:
            if k in df.columns:
                totals[k] = float(pd.to_numeric(df[k], errors="coerce").sum(skipna=True))

    return df, totals, res_b, res_a


def render_vis(image_path: str, res, out_path: str):
    """간단 박스/라벨 시각화 저장"""
    img = cv2.imread(image_path)
    if img is None or res is None or res.boxes is None:
        return out_path
    boxes = res.boxes.xyxy.cpu().numpy().astype(int)
    cls   = res.boxes.cls.cpu().numpy().astype(int)
    confs = res.boxes.conf.cpu().numpy().astype(float)
    names = res.names if hasattr(res, 'names') else {}
    for i in range(len(cls)):
        x1,y1,x2,y2 = boxes[i]
        name = names.get(int(cls[i]), str(int(cls[i])))
        cv2.rectangle(img, (x1,y1), (x2,y2), (0,255,0), 2)
        cv2.putText(img, f"{name}:{confs[i]:.2f}", (x1, max(20,y1-5)), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0,255,0), 2)
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    cv2.imwrite(out_path, img)
    return out_path

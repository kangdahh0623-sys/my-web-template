# planner/services/intake.py
from __future__ import annotations
import os, math
from dataclasses import dataclass
from typing import Dict, List, Tuple, Optional

import numpy as np
import pandas as pd
from PIL import Image
import cv2

try:
    from ultralytics import YOLO
except Exception:
    YOLO = None

# -------------------- 설정 --------------------
DEFAULT_MODEL_PATH = os.path.join("models", "best.pt")
CLASSES_MAP_PATH   = os.path.join("file", "classes_map.csv")
NUTR_CSV_PATH      = os.path.join("file", "메뉴_영양소.csv")
DENSITY_CSV_PATH   = os.path.join("file", "density.csv")  # optional

TRAY_SIZE_CM = {
    "middle": (28.0, 22.0),  # 가로,세로 (cm)
    "high":   (37.0, 29.0),
}

# -------------------- 데이터 구조 --------------------
@dataclass
class DetectItem:
    class_id: int
    class_name: str
    menu_key: str
    score: float
    polygon: Optional[np.ndarray]  # (N,2) or None if bbox only
    bbox: Tuple[int,int,int,int]   # x1,y1,x2,y2
    area_px: float

@dataclass
class IntakeResult:
    before_df: pd.DataFrame
    after_df: pd.DataFrame
    consumed_df: pd.DataFrame
    totals: Dict[str, float]
    before_vis_path: str
    after_vis_path: str

# -------------------- 유틸 --------------------
def _read_image(path: str) -> np.ndarray:
    img = cv2.imdecode(np.fromfile(path, dtype=np.uint8), cv2.IMREAD_COLOR)
    if img is None:
        img = cv2.cvtColor(np.array(Image.open(path).convert("RGB")), cv2.COLOR_RGB2BGR)
    return img

def _save_image(path: str, img: np.ndarray):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    ext = os.path.splitext(path)[1].lower()
    if ext in (".jpg", ".jpeg"):
        cv2.imencode(".jpg", img, [int(cv2.IMWRITE_JPEG_QUALITY), 92])[1].tofile(path)
    else:
        cv2.imencode(".png", img)[1].tofile(path)

def _load_maps() -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    classes_map = pd.read_csv(CLASSES_MAP_PATH) if os.path.exists(CLASSES_MAP_PATH) else pd.DataFrame()
    nutr = pd.read_csv(NUTR_CSV_PATH)
    dens = pd.read_csv(DENSITY_CSV_PATH) if os.path.exists(DENSITY_CSV_PATH) else pd.DataFrame()
    for df in (classes_map, nutr, dens):
        if df.empty: 
            continue
        df.columns = [c.strip().lower() for c in df.columns]
    return classes_map, nutr, dens

def _norm_key(s: str) -> str:
    import re
    t = str(s).strip().lower()
    t = re.sub(r"[()\[\]{}]", " ", t)
    t = re.sub(r"\s+", " ", t)
    return t

def _menu_key_from(class_id:int, class_name:str, classes_map:pd.DataFrame) -> str:
    if not classes_map.empty:
        if "class_id" in classes_map.columns and "menu_key" in classes_map.columns:
            hit = classes_map.loc[classes_map["class_id"]==class_id]
            if not hit.empty:
                return _norm_key(str(hit.iloc[0]["menu_key"]))
        if "class_name" in classes_map.columns and "menu_key" in classes_map.columns:
            hit = classes_map.loc[classes_map["class_name"].map(lambda x: str(x).lower()) == str(class_name).lower()]
            if not hit.empty:
                return _norm_key(str(hit.iloc[0]["menu_key"]))
    return _norm_key(class_name)  # fallback

def _area_px_to_volume_ml(area_px: float, img_wh: Tuple[int,int], tray_type: str) -> float:
    if area_px <= 0: 
        return 0.0
    W, H = img_wh
    tray_w_cm, tray_h_cm = TRAY_SIZE_CM.get(tray_type, TRAY_SIZE_CM["high"])
    # 간단: 이미지 전체=트레이 면적 가정 → 정확도 개선하려면 트레이 검출/보정 사용
    px_per_cm2 = (W*H) / max(1e-6, (tray_w_cm * tray_h_cm))
    cm2 = area_px / max(1e-6, px_per_cm2)
    assumed_depth_cm = 1.5  # 칸 깊이 가정(프로젝트에 맞춰 조정)
    return cm2 * assumed_depth_cm  # ml ≈ cm^3

def _volume_to_grams(menu_key:str, vol_ml:float, dens_df:pd.DataFrame) -> float:
    if not dens_df.empty and "menu_key" in dens_df.columns and "density_g_per_ml" in dens_df.columns:
        hit = dens_df.loc[dens_df["menu_key"].map(_norm_key) == _norm_key(menu_key)]
        if not hit.empty:
            d = float(hit.iloc[0]["density_g_per_ml"])
            return max(0.0, vol_ml * max(0.1, d))
    return max(0.0, vol_ml * 1.0)  # 기본: 1 g/ml

def _nutr_from_grams(menu_key:str, grams:float, nutr_df:pd.DataFrame) -> Dict[str,float]:
    if grams <= 0: 
        return {}
    df = nutr_df.copy()
    keycol = None
    if "menu_key" in df.columns:
        keycol = "menu_key"
    elif "menu" in df.columns:
        df["menu_key"] = df["menu"].map(_norm_key)
        keycol = "menu_key"
    hit = df.loc[df[keycol].map(_norm_key) == _norm_key(menu_key)] if keycol else pd.DataFrame()
    if hit.empty:
        return {}
    row = hit.iloc[0].to_dict()
    out = {}
    # 데이터 스키마가 100g 기준이라 가정 → grams/100 배수 (필요시 조정)
    for k in ["kcal","carbo","protein","fat","vit_a","thiamin","riboflavin","niacin","vit_c","vit_d","calcium","iron"]:
        if k in row and pd.notna(row[k]):
            try:
                out[k] = float(row[k]) * (grams/100.0)
            except Exception:
                pass
    return out

def run_yolo(image_path: str, model_path: Optional[str]=None, conf:float=0.4, iou:float=0.5) -> Tuple[List[DetectItem], np.ndarray]:
    if YOLO is None:
        raise RuntimeError("Ultralytics가 설치되어 있지 않습니다. 'pip install ultralytics' 후 재시도")
    model = YOLO(model_path or DEFAULT_MODEL_PATH)

    img = _read_image(image_path)
    H, W = img.shape[:2]

    res = model.predict(source=img, conf=conf, iou=iou, verbose=False)[0]
    classes_map, _, _ = _load_maps()

    items: List[DetectItem] = []
    vis = img.copy()

    if getattr(res, "masks", None) is not None and res.masks is not None:
        masks = res.masks.data.cpu().numpy()  # (N,H,W)
        boxes = res.boxes.xyxy.cpu().numpy().astype(int)
        cls   = res.boxes.cls.cpu().numpy().astype(int)
        confs = res.boxes.conf.cpu().numpy().astype(float)
        names = res.names if hasattr(res, 'names') else {}
        for i in range(len(cls)):
            m = (masks[i] > 0.5).astype(np.uint8)
            area = float(m.sum())
            x1,y1,x2,y2 = boxes[i]
            c_id = int(cls[i]); score = float(confs[i])
            c_name = names.get(c_id, str(c_id)) if isinstance(names, dict) else str(c_id)
            menu_key = _menu_key_from(c_id, c_name, classes_map)
            color = (0,255,0)
            cv2.rectangle(vis, (x1,y1), (x2,y2), color, 2)
            cv2.putText(vis, f"{c_name}:{score:.2f}", (x1, max(20,y1-5)), cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 2)
            items.append(DetectItem(c_id, c_name, menu_key, score, None, (x1,y1,x2,y2), area))
    else:
        boxes = res.boxes.xyxy.cpu().numpy().astype(int)
        cls   = res.boxes.cls.cpu().numpy().astype(int)
        confs = res.boxes.conf.cpu().numpy().astype(float)
        names = res.names if hasattr(res, 'names') else {}
        for i in range(len(cls)):
            x1,y1,x2,y2 = boxes[i]
            area = float(max(0, (x2-x1)*(y2-y1)))
            c_id = int(cls[i]); score = float(confs[i])
            c_name = names.get(c_id, str(c_id)) if isinstance(names, dict) else str(c_id)
            menu_key = _menu_key_from(c_id, c_name, classes_map)
            color = (0,255,0)
            cv2.rectangle(vis, (x1,y1), (x2,y2), color, 2)
            cv2.putText(vis, f"{c_name}:{score:.2f}", (x1, max(20,y1-5)), cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 2)
            items.append(DetectItem(c_id, c_name, menu_key, score, None, (x1,y1,x2,y2), area))

    return items, vis

def estimate_intake(before_path: str, after_path: str, tray_type: str = "high",
                    model_path: Optional[str]=None, conf:float=0.4, iou:float=0.5,
                    out_dir: str = "media/intake") -> IntakeResult:
    classes_map, nutr_df, dens_df = _load_maps()

    # BEFORE
    items_b, vis_b = run_yolo(before_path, model_path, conf, iou)
    # AFTER
    items_a, vis_a = run_yolo(after_path, model_path, conf, iou)

    img_b = _read_image(before_path); Wb, Hb = img_b.shape[1], img_b.shape[0]
    img_a = _read_image(after_path);  Wa, Ha = img_a.shape[1], img_a.shape[0]

    def _items_to_df(items: List[DetectItem], W:int, H:int) -> pd.DataFrame:
        rows = []
        for it in items:
            vol_ml = _area_px_to_volume_ml(it.area_px, (W,H), tray_type)
            grams  = _volume_to_grams(it.menu_key, vol_ml, dens_df)
            nutr   = _nutr_from_grams(it.menu_key, grams, nutr_df)
            row = {
                "menu_key": it.menu_key,
                "class_name": it.class_name,
                "score": it.score,
                "area_px": it.area_px,
                "volume_ml": vol_ml,
                "grams": grams,
            }
            row.update(nutr)
            rows.append(row)
        df = pd.DataFrame(rows)
        if not df.empty:
            df = df.groupby(["menu_key","class_name"], as_index=False).sum(numeric_only=True)
        return df

    df_b = _items_to_df(items_b, Wb, Hb)
    df_a = _items_to_df(items_a, Wa, Ha)

    def _consumed(before: pd.DataFrame, after: pd.DataFrame) -> pd.DataFrame:
        cols = sorted(list(set(before.columns) | set(after.columns)))
        for need in ["menu_key","class_name","grams","kcal","carbo","protein","fat","vit_a","thiamin","riboflavin","niacin","vit_c","vit_d","calcium","iron"]:
            if need not in cols: 
                cols.append(need)
        b = before.set_index("menu_key").reindex(columns=cols, fill_value=0)
        a = after.set_index("menu_key").reindex(columns=cols, fill_value=0)
        if "class_name" in a.columns:
            b.loc[a.index, "class_name"] = a["class_name"]
        c = b.fillna(0).subtract(a.fillna(0), fill_value=0)
        c = c.reset_index()
        for k in ["grams","kcal","carbo","protein","fat","vit_a","thiamin","riboflavin","niacin","vit_c","vit_d","calcium","iron"]:
            if k in c.columns:
                c[k] = c[k].clip(lower=0.0)
        if "grams" in c.columns:
            c = c[c["grams"] > 0.1]
        return c

    df_c = _consumed(df_b, df_a)

    totals: Dict[str,float] = {}
    for k in ["grams","kcal","carbo","protein","fat","vit_a","thiamin","riboflavin","niacin","vit_c","vit_d","calcium","iron"]:
        if k in df_c.columns:
            totals[k] = float(df_c[k].sum())

    before_vis_path = os.path.join(out_dir, "vis_before.png")
    after_vis_path  = os.path.join(out_dir, "vis_after.png")
    _save_image(before_vis_path, vis_b)
    _save_image(after_vis_path,  vis_a)

    return IntakeResult(
        before_df=df_b, after_df=df_a, consumed_df=df_c, totals=totals,
        before_vis_path=before_vis_path, after_vis_path=after_vis_path
    )

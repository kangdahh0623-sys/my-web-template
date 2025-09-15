# backend/app/api/analyze.py
from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from fastapi.responses import JSONResponse
import os, shutil, tempfile, uuid, pandas as pd
from app.core.config import settings
from app.services.intake_runner_adapter import analyze_pair_with_your_logic, render_vis

router = APIRouter()

@router.post("/result")
async def analyze_result(
    before: UploadFile = File(...),
    after:  UploadFile = File(...),
    school_name: str = Form("구암고등학교"),
    weights_path: str | None = Form(None),
    imgsz: int = Form(224),
    conf: float = Form(0.5),
    max_det: int = Form(20),
):
    try:
        with tempfile.TemporaryDirectory(prefix="intake_") as td:
            # 1) 업로드 저장 (임시폴더)
            b_path = os.path.join(td, f"before_{before.filename or 'before.jpg'}")
            a_path = os.path.join(td, f"after_{after.filename  or 'after.jpg'}")
            for up, dst in ((before, b_path), (after, a_path)):
                with open(dst, "wb") as f:
                    shutil.copyfileobj(up.file, f)

            # 2) 분석 (네 로직)
            df, totals, res_b, res_a = analyze_pair_with_your_logic(
                b_path, a_path, school_name,
                weights_path or settings.YOLO_WEIGHTS,
                imgsz=imgsz, conf=conf, max_det=max_det
            )

            # 3) 시각화 이미지 생성 (여기서! 임시폴더 안에서 만든다)
            vis_b_tmp = os.path.join(td, "vis_before.jpg")
            vis_a_tmp = os.path.join(td, "vis_after.jpg")
            render_vis(b_path, res_b, vis_b_tmp)
            render_vis(a_path, res_a, vis_a_tmp)

            # 4) media/ 로 복사 (고유 파일명으로)
            media_dir = os.path.join(settings.MEDIA_DIR, settings.INTAKE_MEDIA_SUBDIR)
            os.makedirs(media_dir, exist_ok=True)
            uid = uuid.uuid4().hex[:8]
            vis_b = os.path.join(media_dir, f"vis_before_{uid}.jpg")
            vis_a = os.path.join(media_dir, f"vis_after_{uid}.jpg")
            shutil.copy2(vis_b_tmp, vis_b)
            shutil.copy2(vis_a_tmp, vis_a)

            # 5) 응답용 DF 가공
            def _safe(df: pd.DataFrame, cols):
                out = df[cols].copy() if not df.empty else pd.DataFrame(columns=cols)
                return out.fillna(0.0)

            before_df   = _safe(df, ["dish","g_before","kcal","carbo","protein","fat"])
            after_df    = _safe(df, ["dish","g_after","kcal","carbo","protein","fat"])
            consumed_df = _safe(df, ["dish","g_intake","kcal","carbo","protein","fat"])

            def rows(x: pd.DataFrame):
                return x.rename(columns={"dish":"menu_key"}).to_dict(orient="records")

            result = {
                "before": rows(before_df),
                "after":  rows(after_df),
                "consumed": rows(consumed_df),
                "totals": totals,
                "vis_before": vis_b.replace("\\", "/"),
                "vis_after":  vis_a.replace("\\", "/"),
            }
            return JSONResponse({"status": "ok", "result": result})

    except Exception as e:
        import traceback; print("analyze error\n", traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"analyze failed: {e}")

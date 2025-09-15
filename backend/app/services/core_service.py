# backend/app/services/core_service.py
import logging

logger = logging.getLogger(__name__)

class CoreService:
    """핵심 비즈니스 로직 서비스"""
    
    def __init__(self):
        logger.info("CoreService 초기화")
        # TODO: 필요한 의존성 초기화
        
    async def process_data(self, data: dict):
        """데이터 처리 메인 로직"""
        # TODO: 핵심 비즈니스 로직 구현
        logger.info(f"데이터 처리: {data}")
        return {"processed": True, "data": data}
    
    async def validate_input(self, input_data: dict) -> bool:
        """입력 데이터 검증"""
        # TODO: 검증 로직 구현
        return True

# 전역 서비스 인스턴스
core_service = CoreService()


# backend/app/services/core_service.py
import logging, os, tempfile, shutil
from typing import Any, Dict
from app.services.intake import estimate_intake  # ← 방금 만든 intake.py
logger = logging.getLogger(__name__)

class CoreService:
    """핵심 비즈니스 로직 서비스"""

    def __init__(self):
        logger.info("CoreService 초기화")

    async def process_data(self, data: dict):
        logger.info(f"데이터 처리: {data}")
        return {"processed": True, "data": data}

    async def validate_input(self, input_data: dict) -> bool:
        return True

    # === 새로 추가: 전/후 2장 바이트 → 임시 파일 → estimate_intake 호출 ===
    async def analyze_pair_from_bytes(
        self,
        before_bytes: bytes,
        after_bytes: bytes,
        tray_type: str = "high",        # "middle" | "high"
        model_path: str | None = None,  # None이면 intake.py의 DEFAULT_MODEL_PATH
        conf: float = 0.4,
        iou: float = 0.5,
        out_dir: str = "media/intake"
    ) -> Dict[str, Any]:
        tmpdir = tempfile.mkdtemp(prefix="intake_")
        try:
            before_path = os.path.join(tmpdir, "before.png")
            after_path  = os.path.join(tmpdir, "after.png")
            with open(before_path, "wb") as f:
                f.write(before_bytes)
            with open(after_path, "wb") as f:
                f.write(after_bytes)

            res = estimate_intake(
                before_path=before_path,
                after_path=after_path,
                tray_type=tray_type,
                model_path=model_path,
                conf=conf,
                iou=iou,
                out_dir=out_dir,  # 시각화 이미지 저장 경로
            )

            # IntakeResult → JSON 직렬화 가능한 dict 로 변환
            def _df_to_records(df):
                try:
                    return df.to_dict(orient="records")
                except Exception:
                    return []
            return {
                "before": _df_to_records(res.before_df),
                "after":  _df_to_records(res.after_df),
                "consumed": _df_to_records(res.consumed_df),
                "totals": res.totals,
                "vis_before": res.before_vis_path,
                "vis_after":  res.after_vis_path,
            }
        finally:
            # 임시파일 정리는 선택. 시각화 파일(out_dir)은 남김.
            shutil.rmtree(tmpdir, ignore_errors=True)

# 전역 인스턴스 (이미 있었던 코드 유지)
core_service = CoreService()

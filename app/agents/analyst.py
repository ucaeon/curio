# KPI 요약
from langfuse import observe

from app.agents.schemas import PipelineSnapshot


@observe(name="analyst")
def build_analyst_summary(snapshot: PipelineSnapshot) -> str:
    return (
        f"노출 {snapshot.impression_count:,}건, 유저 {snapshot.user_count:,}명 기준 "
        f"CTR {snapshot.ctr * 100:.2f}%, CVR {snapshot.cvr * 100:.2f}%, "
        f"CTCVR {snapshot.ctcvr * 100:.2f}% 입니다."
    )

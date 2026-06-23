# CTR, CVR, CTCVR 성과 지표 계산
import pandas as pd

CLICKED_COLUMN = "clicked"
CONVERTED_COLUMN = "converted"


def compute_ctr(log_df: pd.DataFrame) -> float:
    if log_df.empty:
        return 0.0
    return float(log_df[CLICKED_COLUMN].mean())


def compute_cvr(log_df: pd.DataFrame) -> float:
    clicked_df = log_df[log_df[CLICKED_COLUMN] == 1]
    if clicked_df.empty:
        return 0.0
    return float(clicked_df[CONVERTED_COLUMN].mean())


def compute_ctcvr(log_df: pd.DataFrame) -> float:
    if log_df.empty:
        return 0.0
    return float(log_df[CONVERTED_COLUMN].mean())


def compute_metrics(log_df: pd.DataFrame) -> pd.DataFrame:
    # CTR, CVR, CTCVR 일괄 계산
    return pd.DataFrame(
        [
            {
                "ctr": compute_ctr(log_df),
                "cvr": compute_cvr(log_df),
                "ctcvr": compute_ctcvr(log_df),
            }
        ]
    )

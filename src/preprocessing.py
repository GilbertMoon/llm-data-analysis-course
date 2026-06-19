import pandas as pd


def check_missing_values(df: pd.DataFrame) -> pd.Series:
    """각 컬럼의 결측치 개수를 확인합니다."""
    return df.isna().sum()


def remove_duplicates(df: pd.DataFrame) -> pd.DataFrame:
    """중복 행을 제거한 새 DataFrame을 반환합니다."""
    return df.drop_duplicates().reset_index(drop=True)


def convert_date_column(df: pd.DataFrame, column: str) -> pd.DataFrame:
    """문자열 날짜 컬럼을 datetime 형식으로 변환합니다."""
    result = df.copy()
    result[column] = pd.to_datetime(result[column], errors="coerce")
    return result

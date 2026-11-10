import pandas as pd


def read_excel(source: dict) -> pd.DataFrame:
    """Read one sheet exactly as the bundle describes it, as text."""
    df = pd.read_excel(source["path"], sheet_name=source["sheet"], dtype=str)
    df = df.rename(columns=lambda c: str(c).strip()).dropna(how="all")

    mapping = source.get("columns")
    if mapping:
        missing = [c for c in mapping if c not in df.columns]
        if missing:
            raise ValueError(
                f"columns missing from sheet {source['sheet']}: {missing}"
            )
        df = df[list(mapping)].rename(columns=mapping)
    return df
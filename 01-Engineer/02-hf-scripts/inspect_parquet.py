# inspect_each_parquet.py
import glob
from datasets import Dataset

for f in sorted(glob.glob("*.parquet")):
    ds = Dataset.from_parquet(f)
    print(f"\n=== {f} ===")
    print("rows:", ds.num_rows)
    print("features:", ds.features)
    print("sample:", ds[0])








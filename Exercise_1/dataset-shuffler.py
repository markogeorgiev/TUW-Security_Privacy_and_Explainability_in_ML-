import pandas as pd
import numpy as np
import hashlib
import argparse
import sys


def deterministic_shuffle(df: pd.DataFrame, key: str) -> pd.DataFrame:
    if len(df) != 70000:
        raise ValueError("Input DataFrame must have exactly 70,000 rows.")

    hash_digest = hashlib.sha256(key.encode()).digest()
    seed = int.from_bytes(hash_digest[:4], byteorder='big')

    rng = np.random.default_rng(seed)
    shuffled_indices = rng.permutation(len(df))

    return df.iloc[shuffled_indices].reset_index(drop=True)


def main():
    parser = argparse.ArgumentParser(description="Deterministically shuffle a 70,000-row CSV based on a key.")
    parser.add_argument("input_csv", help="Path to input CSV file with 70,000 rows.")
    parser.add_argument("output_csv", help="Path to output CSV file for shuffled result.")
    parser.add_argument("key", help="Shuffling key (string).")

    args = parser.parse_args()

    try:
        df = pd.read_csv(args.input_csv)
    except Exception as e:
        print(f"Failed to read input CSV: {e}", file=sys.stderr)
        sys.exit(1)

    try:
        shuffled_df = deterministic_shuffle(df, args.key)
        shuffled_df.to_csv(args.output_csv, index=False)
    except Exception as e:
        print(f"Error during shuffling: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()

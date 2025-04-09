import pandas as pd
import numpy as np


def analyze_csv(file_path):
    # Read the CSV file
    try:
        df = pd.read_csv(file_path)
    except Exception as e:
        print(f"Error reading CSV file: {e}")
        return

    print(f"Analyzing file: {file_path}")
    print(f"Total rows: {len(df)}")
    print(f"Columns: {len(df.columns)}")
    print("\nColumn Analysis:")

    for column in df.columns:
        print(f"\nColumn: {column}")

        # Check if column is numeric (with possible missing/string values)
        numeric_values = pd.to_numeric(df[column], errors='coerce')
        non_numeric_mask = numeric_values.isna()
        numeric_count = len(numeric_values) - non_numeric_mask.sum()

        # Check if column has any non-numeric values
        if non_numeric_mask.any():
            # Get the non-numeric values
            non_numeric_values = df[column][non_numeric_mask].unique()
            non_numeric_count = len(non_numeric_values)

            # If some values are numeric and some are not
            if numeric_count > 0:
                print("  Type: Mixed (numeric and categorical)")
                print(f"  Numeric range: {numeric_values.min():.2f} to {numeric_values.max():.2f}")
                print(f"  Numeric average: {numeric_values.mean():.2f}")
                print(f"  Numeric values count: {numeric_count}")
                print(f"  Categories count: {non_numeric_count}")
                print(f"  Categories: {list(non_numeric_values)}")
            else:
                # Pure categorical column
                print("  Type: Categorical")
                unique_values = df[column].unique()
                print(f"  Unique categories count: {len(unique_values)}")
                if len(unique_values) <= 10:
                    print(f"  Categories: {list(unique_values)}")
                else:
                    print(f"  First 10 categories: {list(unique_values[:10])} (and {len(unique_values) - 10} more)")
        else:
            # Pure numeric column
            print("  Type: Numeric")
            print(f"  Range: {df[column].min():.2f} to {df[column].max():.2f}")
            print(f"  Average: {df[column].mean():.2f}")
            print(f"  Standard deviation: {df[column].std():.2f}")


if __name__ == "__main__":
    import sys

    if len(sys.argv) != 2:
        print("Usage: python csv_analyzer.py <path_to_csv_file>")
    else:
        analyze_csv(sys.argv[1])
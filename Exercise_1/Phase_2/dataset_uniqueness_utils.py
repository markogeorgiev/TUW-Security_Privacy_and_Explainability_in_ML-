import os
import re
import pandas as pd


def get_unique_datasets(data_dir="datasets-p2", pattern=r"Financial_Records.*\.csv"):
    """
    Load datasets from the given directory matching the regex pattern.
    Return only unique datasets and their corresponding filenames.

    Parameters:
        data_dir (str): Directory containing the dataset files.
        pattern (str): Regex pattern to match dataset filenames.

    Returns:
        unique_datasets (List[pd.DataFrame]): List of unique DataFrames.
        unique_names (List[str]): List of filenames corresponding to each unique DataFrame.
        num_unique (int): Number of unique datasets.
    """
    compiled_pattern = re.compile(pattern)
    filenames = [os.path.join(data_dir, f) for f in os.listdir(data_dir) if compiled_pattern.match(f)]
    filenames.sort()

    raw_datasets = [pd.read_csv(fname) for fname in filenames]
    dataset_names = [os.path.basename(fname) for fname in filenames]

    unique_datasets = []
    unique_names = []

    for i, ds in enumerate(raw_datasets):
        is_duplicate = False
        for u in unique_datasets:
            if ds.equals(u):
                is_duplicate = True
                break
        if not is_duplicate:
            unique_datasets.append(ds)
            unique_names.append(dataset_names[i])

    return unique_datasets, unique_names, len(unique_datasets)


def save_cleaned_output_versioned(base_df, modification_log, num_unique, out_dir="output-datasets"):
    """
    Save the cleaned dataset and modification log to a versioned folder based on number of unique datasets.

    Parameters:
        base_df (pd.DataFrame): The cleaned dataset.
        modification_log (List[Dict]): List of modification entries (row, column, values).
        num_unique (int): Number of unique datasets used in the attack.
        out_dir (str): Root directory where results should be saved.

    Returns:
        save_dir (str): Path to the folder where outputs were saved.
    """
    os.makedirs(out_dir, exist_ok=True)

    version_folder_prefix = f"{num_unique}_v"
    version_numbers = []

    for d in os.listdir(out_dir):
        full_path = os.path.join(out_dir, d)
        if os.path.isdir(full_path) and d.startswith(version_folder_prefix):
            match = re.match(rf"{num_unique}_v(\d+)$", d)
            if match:
                version_numbers.append(int(match.group(1)))

    next_version = max(version_numbers) + 1 if version_numbers else 1
    version_folder = f"{num_unique}_v{next_version}"
    save_dir = os.path.join(out_dir, version_folder)
    os.makedirs(save_dir, exist_ok=True)

    output_filename = f"Financial_Records_No_Fingerprint_{num_unique}_v{next_version}.csv"
    base_df.to_csv(os.path.join(save_dir, output_filename), index=False)

    output_filename_mod_log = f"modification_log_{num_unique}_v{next_version}.csv"
    log_df = pd.DataFrame(modification_log)
    log_df.to_csv(os.path.join(save_dir, output_filename_mod_log), index=False)

    print(f"Cleaned dataset saved as '{output_filename}' in '{save_dir}'")
    print(f"Modification log saved as '{output_filename_mod_log}' in '{save_dir}'")

    return save_dir

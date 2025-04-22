import pandas as pd
import numpy as np
import hashlib
import random

# Load dataset
df = pd.read_csv("Shuffled_Financial_Records.csv")

# Set seed for reproducibility
random.seed(42)
np.random.seed(42)

### STEP 1: UID MANIPULATION ###
# Generate a synthetic UID from stable features and assign back to PID
def generate_uid(row, cols):
    concat_str = ''.join(str(row[col]) for col in cols)
    return int(hashlib.sha256(concat_str.encode()).hexdigest(), 16) % 10**8

uid_cols = ['age', 'sex', 'job', 'residence_since', 'property', 'housing']
df['PID'] = df.apply(lambda row: generate_uid(row, uid_cols), axis=1)

### STEP 2: BIT COLLISION ENGINEERING ###

# Categorical columns to attack
categorical_cols = [
    'sex', 'marital_status', 'job', 'credit_hist', 'purpose', 'debtors',
    'property', 'installment_other', 'housing', 'tel', 'online_banking', 'foreign'
]

# Function to randomly flip categorical values
def perturb_categorical(col):
    top_values = df[col].value_counts().nlargest(5).index.tolist()
    df[col] = df[col].apply(lambda x: random.choice(top_values) if random.random() < 0.3 else x)

for col in categorical_cols:
    perturb_categorical(col)

# Mixed-type columns: numeric part perturbation only
def perturb_mixed_numeric(col, value_range=0.1):
    numeric_mask = pd.to_numeric(df[col], errors='coerce').notnull()
    numeric_values = df.loc[numeric_mask, col].astype(float)
    noise = np.random.uniform(-value_range, value_range, size=numeric_values.shape[0])
    perturbed = (numeric_values * (1 + noise)).clip(lower=0).round().astype(int)
    df.loc[numeric_mask, col] = perturbed

perturb_mixed_numeric('employment_since', 0.2)
perturb_mixed_numeric('checking_account', 0.25)
perturb_mixed_numeric('savings', 0.25)

# Numeric columns to attack
numeric_cols = [
    'age', 'credit_amount', 'duration', 'installment_rate',
    'residence_since', 'existing_credits', 'liable_people',
    'monthly_rent_or_mortgage'
]

def perturb_numeric(col, shift_percent=0.1):
    values = df[col].astype(float)
    noise = np.random.normal(loc=0, scale=shift_percent, size=len(values))
    df[col] = (values * (1 + noise)).clip(lower=0).round().astype(int)

for col in numeric_cols:
    perturb_numeric(col, 0.15)

# Binary numeric columns (1 or 2) — flip occasionally
def flip_binary(col, prob=0.15):
    df[col] = df[col].apply(lambda x: 3 - x if random.random() < prob else x)

flip_binary('default', prob=0.2)

# Ensure all numeric columns are integers
for col in df.columns:
    if pd.api.types.is_numeric_dtype(df[col]):
        df[col] = df[col].round().astype(int)

# Save the attacked dataset
df.to_csv("Attacked_Financial_Records.csv", index=False)
import pandas as pd
import matplotlib.pyplot as plt

df = pd.read_csv("../Financial_Records.csv")  # Adjust the filename if needed

categorical_cols = ['sex', 'marital_status', 'job', 'credit_hist', 'purpose',
                    'debtors', 'property', 'installment_other', 'housing',
                    'tel', 'online_banking', 'foreign']

for col in categorical_cols:
    print(f"\n{col} value counts:\n{df[col].value_counts()}")
    df[col].value_counts().plot(kind='bar')
    plt.title(f"Distribution of {col}")
    plt.xlabel(col)
    plt.ylabel("Frequency")
    plt.tight_layout()
    plt.show()
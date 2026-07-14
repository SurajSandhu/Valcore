import pandas as pd

INPUT_FILE = "dataset/UNSW_2018_IoT_Botnet_Final_10_Best.csv"
OUTPUT_FILE = "dataset/balanced_bot_iot.csv"

chunksize = 50000

normal_rows = []
attack_rows = []

print("Reading dataset...")

for chunk in pd.read_csv(
    INPUT_FILE,
    sep=";",
    chunksize=chunksize,
    low_memory=False
):
    # Remove unnecessary column if it exists
    if "Unnamed: 0" in chunk.columns:
        chunk = chunk.drop(columns=["Unnamed: 0"])

    # Separate traffic
    normal = chunk[chunk["attack"] == 0]
    attack = chunk[chunk["attack"] == 1]

    if not normal.empty:
        normal_rows.append(normal)

    if not attack.empty:
        attack_rows.append(attack)

print("Finished reading!")

# Combine all normal traffic
normal_df = pd.concat(normal_rows)

print(f"Normal samples found: {len(normal_df)}")

# Combine all attack traffic
attack_df = pd.concat(attack_rows)

# Randomly select same number of attacks
attack_df = attack_df.sample(
    n=len(normal_df),
    random_state=42
)

# Merge
balanced = pd.concat([normal_df, attack_df])

# Shuffle
balanced = balanced.sample(
    frac=1,
    random_state=42
)

balanced.to_csv(OUTPUT_FILE, index=False)

print("\nBalanced dataset created!")
print(balanced["attack"].value_counts())
print(f"\nSaved as {OUTPUT_FILE}")
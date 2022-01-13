import pandas as pd
import seaborn as sns

df = pd.read_pickle("accidents.pkl.gz")
df["date"] = df["p2a"].astype("datetime64")

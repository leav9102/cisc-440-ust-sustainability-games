import pandas as pd
import math
import matplotlib.pyplot as plt

coords_path = "data/ust_building_coordinates.csv"
df = pd.read_csv(coords_path)

threshold = 0.00115

edges = []
for i in range(len(df)):
    for j in range(i + 1, len(df)):
        lat1, lon1 = df.loc[i, "Latitude"], df.loc[i, "Longitude"]
        lat2, lon2 = df.loc[j, "Latitude"], df.loc[j, "Longitude"]
        dist = math.sqrt((lat1 - lat2) ** 2 + (lon1 - lon2) ** 2)
        if dist <= threshold:
            edges.append({
                "Source": df.loc[i, "Building"],
                "Target": df.loc[j, "Building"],
                "Distance": round(dist, 6)
            })

connected = set()
for e in edges:
    connected.add(e["Source"])
    connected.add(e["Target"])

for i in range(len(df)):
    b = df.loc[i, "Building"]
    if b not in connected:
        best_j = None
        best_dist = None
        for j in range(len(df)):
            if i == j:
                continue
            lat1, lon1 = df.loc[i, "Latitude"], df.loc[i, "Longitude"]
            lat2, lon2 = df.loc[j, "Latitude"], df.loc[j, "Longitude"]
            dist = math.sqrt((lat1 - lat2) ** 2 + (lon1 - lon2) ** 2)
            if best_dist is None or dist < best_dist:
                best_dist = dist
                best_j = j
        s = df.loc[i, "Building"]
        t = df.loc[best_j, "Building"]
        pair = tuple(sorted((s, t)))
        already = any(tuple(sorted((e["Source"], e["Target"]))) == pair for e in edges)
        if not already:
            edges.append({
                "Source": s,
                "Target": t,
                "Distance": round(best_dist, 6)
            })

edges_df = pd.DataFrame(edges).sort_values(["Source", "Target"]).reset_index(drop=True)
edges_df.to_csv("data/ust_building_edges.csv", index=False)

fig, ax = plt.subplots(figsize=(10, 8))

for _, row in edges_df.iterrows():
    s = df[df["Building"] == row["Source"]].iloc[0]
    t = df[df["Building"] == row["Target"]].iloc[0]
    ax.plot([s["Longitude"], t["Longitude"]], [s["Latitude"], t["Latitude"]], linewidth=1)

ax.scatter(df["Longitude"], df["Latitude"], s=40)

for _, row in df.iterrows():
    ax.annotate(
        row["Building"],
        (row["Longitude"], row["Latitude"]),
        xytext=(4, 4),
        textcoords="offset points",
        fontsize=8
    )

ax.set_title("Approximate UST Campus Graph (30 Buildings)")
ax.set_xlabel("Longitude")
ax.set_ylabel("Latitude")
ax.grid(True)

plt.tight_layout()
plt.savefig("output/ust_campus_map_plot.png", dpi=200, bbox_inches="tight")
plt.show()

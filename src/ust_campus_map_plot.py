import pandas as pd
import math
import matplotlib.pyplot as plt

coords_path = "data/ust_game_subset_15nodes.csv"
df = pd.read_csv(coords_path)

threshold = 0.00115

edges = []
for i in range(len(df)):
    for j in range(i + 1, len(df)):
        lat1, lon1 = df.loc[i, "latitude"], df.loc[i, "longitude"]
        lat2, lon2 = df.loc[j, "latitude"], df.loc[j, "longitude"]
        dist = math.sqrt((lat1 - lat2) ** 2 + (lon1 - lon2) ** 2)
        if dist <= threshold:
            edges.append({
                "Source": df.loc[i, "building_name"],
                "Target": df.loc[j, "building_name"],
                "Distance": round(dist, 6)
            })

connected = set()
for e in edges:
    connected.add(e["Source"])
    connected.add(e["Target"])

for i in range(len(df)):
    b = df.loc[i, "building_name"]
    if b not in connected:
        best_j = None
        best_dist = None
        for j in range(len(df)):
            if i == j:
                continue
            lat1, lon1 = df.loc[i, "latitude"], df.loc[i, "longitude"]
            lat2, lon2 = df.loc[j, "latitude"], df.loc[j, "longitude"]
            dist = math.sqrt((lat1 - lat2) ** 2 + (lon1 - lon2) ** 2)
            if best_dist is None or dist < best_dist:
                best_dist = dist
                best_j = j
        s = df.loc[i, "building_name"]
        if best_j is None:
            continue
        t = df.loc[best_j, "building_name"]
        pair = tuple(sorted((str(s), str(t))))
        already = any(tuple(sorted((str(e["Source"]), str(e["Target"])))) == pair for e in edges)
        if not already:
            edges.append({
                "Source": s,
                "Target": t,
                "Distance": round(best_dist, 6)
            })

edges_df = pd.DataFrame(edges).sort_values(["Source", "Target"]).reset_index(drop=True)
edges_df.to_csv("data/ust_game_subset_15edges.csv", index=False)

fig, ax = plt.subplots(figsize=(10, 8))

for _, row in edges_df.iterrows():
    s = df[df["building_name"] == row["Source"]].iloc[0]
    t = df[df["building_name"] == row["Target"]].iloc[0]
    ax.plot([s["longitude"], t["longitude"]], [s["latitude"], t["latitude"]], linewidth=1)

ax.scatter(df["longitude"], df["latitude"], s=40)

for _, row in df.iterrows():
    ax.annotate(
        row["building_name"],
        (row["longitude"], row["latitude"]),
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

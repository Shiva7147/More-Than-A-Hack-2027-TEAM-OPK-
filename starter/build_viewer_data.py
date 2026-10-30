import os
import sys
import json
import numpy as np
import pandas as pd

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "evaluation"))
from games import GAME, GAMES, require
import starter.baseline as bl

VIEWER_DIR = os.path.join(ROOT, "viewer")
os.makedirs(VIEWER_DIR, exist_ok=True)

meta_path, raw_path = require(["atd_meta", "atd_raw"], GAME)
team_of_track = bl.team_of_each_track(meta_path)
length, width = GAMES[GAME]["pitch"]

# Read OPK predictions
opk_csv = os.path.join(ROOT, "evaluation", "results", "OPK.csv")
df_opk = pd.read_csv(opk_csv)
opk_labels = df_opk["label"].values

start_f, end_f = 11185, 18685
print(f"Extracting sample frames {start_f}..{end_f} for interactive viewer...")

frames_data = []
FIELD_SEP = ":"
GROUP_SEP = ";"
MISSING = "N"

with open(raw_path) as handle:
    for line in handle:
        parts = line.split(FIELD_SEP)
        if len(parts) != 3: continue
        fid = int(parts[0]) - 1
        if fid < start_f: continue
        if fid >= end_f: break
        
        # Subsample every 3 frames (~8.3 fps, lightweight, completely smooth with CSS transition)
        if (fid - start_f) % 3 != 0:
            continue
            
        ball_part = parts[2].strip()
        bx, by = None, None
        if ball_part[0] != MISSING:
            c1 = ball_part.index(",")
            c2 = ball_part.index(",", c1 + 1)
            bx = round(float(ball_part[:c1]) * length, 2)
            by = round(float(ball_part[c1+1:c2]) * width, 2)
            
        players = []
        for slot, grp in enumerate(parts[1].split(GROUP_SEP)):
            if grp[0] == MISSING: continue
            gc1 = grp.index(",")
            gc2 = grp.index(",", gc1 + 1)
            px = round(float(grp[:gc1]) * length, 2)
            py = round(float(grp[gc1+1:gc2]) * width, 2)
            team = "H" if team_of_track[slot] == 0 else "A"
            players.append({"id": slot, "t": team, "x": px, "y": py})
            
        frames_data.append({
            "f": fid,
            "b": [bx, by] if bx is not None else None,
            "p": players,
            "l": str(opk_labels[fid])
        })

out_json = os.path.join(VIEWER_DIR, "demo_data.json")
with open(out_json, "w") as f:
    json.dump({
        "pitch": {"len": length, "wid": width},
        "frames": frames_data
    }, f)

print(f"Exported {len(frames_data)} frames to {out_json} ({os.path.getsize(out_json)/(1024*1024):.2f} MB)")

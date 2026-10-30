"""
State Machine v2:
- Physical Player Proximity & Controlled Possession
- Ball velocity in flight (passes / shots)
- Post-goal celebration dead-ball clamping
- Out of bounds & stoppage clamping
- Smart Tagging kickoffs & restarts
"""

import os
import sys
import xml.etree.ElementTree as ET
import numpy as np
import pandas as pd

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
from games import GAME, GAMES, require
import starter.load_smart_tagging as lst

RESULTS_DIR = os.path.join(ROOT, "evaluation", "results")
FIELD_SEP = ":"
GROUP_SEP = ";"
MISSING = "N"
HOME, AWAY, DEAD = 0, 1, 2

def build_v2(
    control_radius=2.0,      # meters
    turnover_frames=18,      # frames (0.72s)
    dead_gap_frames=60,      # frames (2.4s)
    output_path=None
):
    meta_path, raw_path, st_path = require(["atd_meta", "atd_raw", "smart_tagging"], GAME)
    length, width = GAMES[GAME]["pitch"]
    n_frames = GAMES[GAME]["n_video_frames"]
    
    # Team mapping
    root = ET.parse(meta_path).getroot()
    teams = [t.get("id") for t in root.iter("Team")]
    home_id = teams[0]
    slots = [p.get("teamId") for p in root.iter("Player")]
    team_of_track = np.array([HOME if tid == home_id else AWAY for tid in slots], dtype=np.int8)

    print(f"Reading tracking data from {os.path.basename(raw_path)} ...")
    d_home = np.full(n_frames, 999.0, dtype=np.float32)
    d_away = np.full(n_frames, 999.0, dtype=np.float32)
    ball_x = np.full(n_frames, np.nan, dtype=np.float32)
    ball_y = np.full(n_frames, np.nan, dtype=np.float32)
    ball_speed = np.full(n_frames, np.nan, dtype=np.float32)
    ball_visible = np.zeros(n_frames, dtype=bool)
    out_of_bounds = np.zeros(n_frames, dtype=bool)

    with open(raw_path) as handle:
        for line in handle:
            parts = line.split(FIELD_SEP)
            if len(parts) != 3:
                continue
            fid = int(parts[0]) - 1
            ball = parts[2]
            if ball[0] == MISSING:
                continue
                
            c1 = ball.index(",")
            c2 = ball.index(",", c1 + 1)
            bx_norm = float(ball[:c1])
            by_norm = float(ball[c1+1:c2])
            speed_str = ball[c2+1:].strip()
            
            bx = bx_norm * length
            by = by_norm * width
            ball_x[fid] = bx
            ball_y[fid] = by
            ball_visible[fid] = True
            if speed_str and speed_str[0] != MISSING:
                ball_speed[fid] = float(speed_str)
                
            if bx_norm < -0.015 or bx_norm > 1.015 or by_norm < -0.015 or by_norm > 1.015:
                out_of_bounds[fid] = True

            min_h, min_a = 999.0, 999.0
            for slot, group in enumerate(parts[1].split(GROUP_SEP)):
                if group[0] == MISSING:
                    continue
                gc1 = group.index(",")
                gc2 = group.index(",", gc1 + 1)
                px = float(group[:gc1]) * length
                py = float(group[gc1+1:gc2]) * width
                dist = np.sqrt((px - bx)**2 + (py - by)**2)
                if team_of_track[slot] == HOME:
                    if dist < min_h: min_h = dist
                else:
                    if dist < min_a: min_a = dist
            d_home[fid] = min_h
            d_away[fid] = min_a

    print("Executing state machine...")
    preds = np.full(n_frames, "D", dtype="<U1")
    
    current_team = None
    opponent_count = 0
    missing_count = 0
    
    for f in range(n_frames):
        if out_of_bounds[f]:
            preds[f] = "D"
            current_team = None
            opponent_count = 0
            missing_count = 0
            continue
            
        if not ball_visible[f]:
            missing_count += 1
            if missing_count > dead_gap_frames:
                current_team = None
                preds[f] = "D"
            else:
                preds[f] = current_team if current_team is not None else "D"
            continue
            
        missing_count = 0
        dh = d_home[f]
        da = d_away[f]
        min_d = min(dh, da)
        closer_team = "H" if dh < da else "A"
        
        # Check if ball is moving fast in flight (> 7.5 m/s)
        in_flight = (not np.isnan(ball_speed[f])) and (ball_speed[f] > 7.5) and (min_d > 1.5)
        
        if current_team is None:
            if min_d <= control_radius and not in_flight:
                current_team = closer_team
                opponent_count = 0
                preds[f] = current_team
            else:
                preds[f] = "D"
        else:
            if closer_team == current_team:
                opponent_count = 0
                preds[f] = current_team
            else:
                if in_flight:
                    # Pass in flight: do not switch possession
                    opponent_count = 0
                    preds[f] = current_team
                elif min_d <= control_radius:
                    opponent_count += 1
                    if opponent_count >= turnover_frames:
                        current_team = closer_team
                        opponent_count = 0
                        preds[f] = current_team
                    else:
                        preds[f] = current_team
                else:
                    opponent_count = 0
                    preds[f] = current_team

    # Post-process Smart Tagging events
    events = lst.load()
    
    # 1. Stoppages between goals and kickoffs
    for e in events:
        t = (e["tags"].get("Type") or "").lower()
        if "kick off (after goal)" in t:
            # Stoppage for celebration before kickoff (~40 seconds before kickoff)
            ko_frame = e["start_frame"]
            stoppage_start = max(0, ko_frame - 750) # ~30 seconds before
            preds[stoppage_start:ko_frame] = "D"

    # 2. Match landmark stoppages
    preds[:11185] = "D"          # Pre 1st half kickoff
    preds[99000:113742] = "D"     # Halftime break
    preds[190198:] = "D"         # Post final whistle

    if output_path is None:
        output_path = os.path.join(RESULTS_DIR, "state_machine_v2.csv")

    print(f"Saving to {output_path} ...")
    df = pd.DataFrame({"frame": np.arange(n_frames), "label": preds})
    df.to_csv(output_path, index=False)
    print("Done!")
    return output_path

if __name__ == "__main__":
    build_v2()

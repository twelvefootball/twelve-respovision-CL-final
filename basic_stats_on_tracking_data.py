import json
import os

import scipy.signal as signal

import numpy as np
import pandas as pd



"""
    1. Read tracking data files
"""
path_to_folder = 'Data/'
match_id = 18768058

# Match information file
with open(f'{path_to_folder}{match_id}.json', 'r', encoding='utf-8') as f:
    match = json.load(f)

# Match information
print(match)

# Read tracking data file
data = []
with open(f'{path_to_folder}{match_id}_tracking.json', 'r') as f:
    for line in f:
        obj = json.loads(line)
        data.append(obj)

print(len(data))

# Example of one Frame   - Readme.md

# Reading tracking data
custom_data = []
for d in data[0:5000]: # Testing purpose limit

    for p in d['players']:
        custom_data.append({
            'frame': int(d['frame_id']),
            'period': d.get('period'),
            'jersey_number': p.get("jersey_number"),
            'speed': p.get('speed', 0),
            'player': p.get('person_name'),
            'team_name': p.get('team_name'),

        })

# Transform to dataframe
df = pd.DataFrame(custom_data).fillna(0)

"""
    Calculate simple match run stats
"""
column = 'speed'
match_stats = []
max_speed = 11 # cca 40kmh
window_length = 7
use_moving_avg_filter = False

# High speed runs trasholds
hs_run_treshold = 5.4 # cca 20kmh
sprint_window = 1 * 25 # 1 second

frames_to_save = []
for player, df_tracking in df.groupby('player'):

    # Smooth data
    df_tracking.at[df_tracking[column] > max_speed] = np.nan

    # 'moving average'
    if use_moving_avg_filter:
        ma_window = np.ones(window_length) / window_length
        df_tracking[column] = np.convolve(df_tracking[column], ma_window, mode='same')
    else:
        # 'Savitzky-Golay: https://en.wikipedia.org/wiki/Savitzky%E2%80%93Golay_filter
        df_tracking[column] = signal.savgol_filter(df_tracking[column], window_length=window_length, polyorder=1)

    # walking (less than 2 m/s)
    walking = df_tracking.loc[df_tracking[column] < 2, column].sum() / 25. / 1000 # Transform to km/h

    # jogging (between 2 and 4 m/s)
    jogging = df_tracking.loc[ (df_tracking[column] >= 2) & (df_tracking[column] < 4), column].sum() / 25. / 1000

    # running (between 4 and 7 m/s)
    running = df_tracking.loc[ (df_tracking[column] >= 4) & (df_tracking[column] < 7), column].sum() / 25. / 1000

    # sprinting (greater than 7 m/s)
    sprinting = df_tracking.loc[df_tracking[column] >= 7, column].sum() / 25. / 1000

    match_stats.append({
        'Player': player,
        'Walking (km/h)': walking,
        'Jogging (km/h)': jogging,
        'Running (km/h)': running,
        'Sprinting (km/h)': sprinting

    })

    # Checking High speed run frames
    player_hs_runs = np.diff(1 * (np.convolve(1 * (df_tracking[column] >= hs_run_treshold), np.ones(sprint_window), mode='same') >= sprint_window))
    hs_runs_start = np.where(player_hs_runs == 1)[0] - int(  sprint_window / 2) + 1  # adding sprint_window/2 because of the way that the convolution is centred
    hs_runs_end = np.where(player_hs_runs == -1)[0] + int(sprint_window / 2) + 1

    frames_to_save.extend(hs_runs_start)

df_match_stats = pd.DataFrame(match_stats)
print(df_match_stats)

# TASK: total distance, separate by period, by team...

"""
    2. Exporting Frames of interest
    
"""
_obj_p = []

for d in data:

    if int(d['frame_id']) in frames_to_save:
        ball = d.get('ball', None)
        if ball is not None:
            _obj_p.append({
                'frame': int(d['frame_id']),
                'period': int(d.get('period').split('_')[-1]),
                'jersey_number': -99,
                'player': "ball",
                'vx': ball.get('x_velocity', 0),
                'vy': ball.get('y_velocity', 0),
                'speed': ball.get('speed', 0),
                'x': ball.get('x', -1),
                'y': ball.get('y', -1),
                'team_name': "ball",

            })

        for p in d['players']:
            p_id = f'{"home_team" if p.get("team_name") == match["home_team"]["name"] else "away_team"}_player_{p.get("jersey_number")}'
            _obj_p.append(
                {
                    'frame': int(d['frame_id']),
                    'period': int(d.get('period').split('_')[-1]),
                    'jersey_number': p.get("jersey_number"),

                    'speed': p.get('speed', 0),
                    'x': p.get('x', -1),
                    'y': p.get('y', -1),
                    'vx': p.get('x_velocity', 0),
                    'vy': p.get('y_velocity', 0),

                    'player': p.get('person_name'),
                    'team_name': p.get('team_name'),
                }
            )

df_tracks = pd.DataFrame(_obj_p).fillna(0)

os.makedirs(f"Data",exist_ok=True)
df_tracks.reset_index().to_parquet(f"Data/{match_id}_tracks.parquet")
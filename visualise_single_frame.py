

"""
 Visualize tracking data
 
 Given a match ID and a frame, this code shows the positions of the players on
 the pitch.
 
 Ball is shown in red.
 
"""

import os

import pandas as pd
from matplotlib import pyplot as plt
from mplsoccer import Pitch


pitch_length = 105
pitch_width = 68

def transform_x_coordinates(x):
    return x / pitch_length * 100


def transform_y_coordinates(x):
    return 100 - (x / pitch_width * 100)

# CL Finals
match_id = 18768058

# Load tracking data frames from Tutorial 1
df_tracking = pd.read_parquet(f"Data/{match_id}_tracks.parquet")


# select frame
frame, period = df_tracking.iloc[300][['frame','period']]
selected_frame = df_tracking[(df_tracking['frame'] == frame)&(df_tracking['period'] == period)]

# Transform coordinates to wyscout
selected_frame['start_x'] = transform_x_coordinates(selected_frame['x'])
selected_frame['start_y'] = transform_y_coordinates(selected_frame['y'])

# Set team colors
team_colors = {
    'Manchester City': '#6cabdd',
    'Inter': '#010E80',
}
fig, ax = plt.subplots(nrows=1, ncols=1, figsize=(10,7))
pitch = Pitch(pitch_type="wyscout",
              goal_type='box',
              pitch_color= "w",
              linewidth=1,
              spot_scale=0,
              line_color="k",
              line_zorder=1)

pitch.draw(ax)

# Add players
for team, players in selected_frame.groupby('team_name'):

    # Add player positions as nodes
    pitch.scatter(
        players['start_x'],
        players['start_y'],
        color='r' if team == 'ball' else team_colors.get(team, 'k'),
        ec = 'k',
        ax=ax,
        lw = 1,
        zorder=3 if team=='ball' else 2, # ball order priority
        s= 50 if team=='ball' else 200, #Different size for ball

    )

    # Add jersey numbers to nodes, ignore ball
    for idx, row in players[players['team_name']!='ball'].iterrows():
        pitch.annotate(row['jersey_number'], xy=(row['start_x'], row['start_y']),
                           c='w', va='center',
                           zorder=4,
                           ha='center', size=8,
                            weight='bold',
                           alpha=1,
                           ax=ax)

# Add title
ax.set_title(f"Selected frame {frame}")

# Output image
os.makedirs("outputs",exist_ok=True)
fig.savefig(f"outputs/freeze_frame_{frame}_{period}.jpg", format='jpg', dpi=200, facecolor=fig.get_facecolor())


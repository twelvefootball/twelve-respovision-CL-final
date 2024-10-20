import pandas as pd
import os
from matplotlib import pyplot as plt
from matplotlib.cm import get_cmap
from mplsoccer import Pitch

"""
    Visualize runs - that were extracted from tracking data
"""

# CL Finals
match_id = 18768058

# Load wyscout event data - Coordinates are transformed to opta
df_events = pd.read_parquet(f"Data/{match_id}_stories.parquet")

# Load pre-generated "runs" data
df_runs = pd.read_parquet(f"Data/{match_id}_runs.parquet")

# Find all runs in possession when shot occurs
xg_runs = df_runs[df_runs['xGRun'] > 0]

# Group all runs into one possession

visualize_passing_chain = True
for possession_id, df_runs in xg_runs.groupby('possession_id'):

    # get team events in a possession
    df_possession = df_events[(df_events['possession_id'] == possession_id)&(df_events['possession_team_id'] == df_events['team_id'])]

    # Player can have multiple runs in on possession, keep only his last run
    df_runs = df_runs.drop_duplicates(subset='player', keep='last')

    # Plot all runs in possession
    fig, ax = plt.subplots(nrows=1, ncols=1, figsize=(10, 7))
    pitch = Pitch(pitch_type="opta",
                  goal_type='box',
                  pitch_color="w",
                  linewidth=1,
                  spot_scale=0,
                  line_color="k",
                  line_zorder=1)

    pitch.draw(ax)

    # Create color set
    name = "Set1"
    cmap = get_cmap(name)
    colors = cmap.colors
    counter = 0

    # Plot all runs
    for idx, row in df_runs.iterrows():

        # Visualize runs -
        pitch.arrows(row['start_x'], row['start_y'],
                          row['end_x'], row['end_y'],
                          width= 1.8,
                          headwidth=3, headlength=3, headaxislength=2,
                          color=colors[counter],
                          edgecolor= "k" if row['Target'] else colors[counter], # Differentiate target and off target runs
                          linewidth=1 if row['Target'] else 0, # Differentiate target and off target runs
                          alpha=0.8,
                          zorder=3,
                          label=row['player'],
                          ax=ax)

        counter += 1
        if counter >= len(colors):
            counter = 0

    # Visualize possession chain
    if visualize_passing_chain:
        pitch.arrows(df_possession[df_possession['end_x'].between(1, 100)]['start_x'],
                         df_possession[df_possession['end_x'].between(1, 100)]['start_y'],
                         df_possession[df_possession['end_x'].between(1, 100)]['end_x'],
                         df_possession[df_possession['end_x'].between(1, 100)]['end_y'], width=1, headwidth=5,
                         alpha=0.5, ls='--', zorder=2,
                         headlength=5, color='grey', ax=ax, label='completed passes')

    # Add title
    possession_start_time = df_runs['time_start'].min()[0:5]
    possession_end_time = df_runs['time_end'].max()[0:5]
    team_name = df_runs.iloc[0]['team_name']
    ax.set_title(f"{team_name} runs in possession from {possession_start_time} to {possession_end_time}")

    # Legend
    ax.legend(bbox_to_anchor=(0, 0), loc='upper left', fontsize='small', framealpha=0.0, ncol=1)

    # Save output image
    #os.makedirs("outputs", exist_ok=True)
    #fig.savefig(f"outputs/runs_{possession_id}.jpg", format='jpg', dpi=200, facecolor=fig.get_facecolor())

  

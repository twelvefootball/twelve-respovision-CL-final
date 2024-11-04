import json
import os

import pandas as pd

from matplotlib.animation import FuncAnimation
from mplsoccer import Pitch

os.chdir("..")
#%%
#Check match file
path_to_folder = 'data/RespoVis/'
match_id = 18768058

# Match information file
with open(f'{path_to_folder}{match_id}.json', 'r', encoding='utf-8') as f:
    match = json.load(f)

#%%
# Read tracking data file
data = []
with open(f'{path_to_folder}{match_id}_tracking.json', 'r') as f:
    for line in f:
        obj = json.loads(line)
        data.append(obj)


#For exploration
df_demo = data[10000:11000]


#%%
# Example of how to transform the data into a data frame for easier manipulation
# Reading tracking data
custom_data = []
for d in data:
    for p in d['players']:
        custom_data.append({
            'time': d.get('time'),
            'frame': int(d.get('frame_id')),
            'period': int(d.get('period')[-1]),
            'person_id': p.get("person_id"),
            'player': p.get('person_name'),
            'team_name': p.get('team_name'),
            'jersey_number': p.get("jersey_number"),
            'x': p.get('x'),
            'y': p.get('y'),
            'x_velocity': p.get('x_velocity'),
            'y_velocity': p.get('y_velocity'),
            'speed': p.get('speed'),
            'x_acceleration': p.get('x_acceleration'),
            'y_acceleration': p.get('y_acceleration'),
            'acceleration': p.get('acceleration'),
        })
    #Add the ball
    ball = d.get('ball')
    custom_data.append({
        'time': d.get('time'),
        'frame': int(d.get('frame_id')),
        'period': int(d.get('period')[-1]),
        'person_id': -100,
        'player': 'ball',
        'team_name': 'ball',
        'jersey_number': -1,
        'x': ball.get('x'),
        'y': ball.get('y'),
        'x_velocity': ball.get('x_velocity'),
        'y_velocity': ball.get('y_velocity'),
        'speed': ball.get('speed'),
        'x_acceleration': ball.get('x_acceleration'),
        'y_acceleration': ball.get('y_acceleration'),
        'acceleration': ball.get('acceleration')
    })
    

# Transform to dataframe - Note that this is a big file. 
# Not recomended to open in variable explorere
df_frames = pd.DataFrame(custom_data)
df_frames_demo = df_frames[1000:2000]

#Create custom unique frame_ids -> add 100000 to the frame of period 2
df_frames.loc[df_frames['period'] == 2, 'frame'] += 100000

#%% Exploring data to understand coordinates
#Here I checked the data in the variable explorer to "guess" that the coordinates were 105x68


df_ederson = df_frames[df_frames.player == 'Ederson']
df_ederson_1 = df_ederson[df_ederson.period == 1]
df_ederson_2 = df_ederson[df_ederson.period == 2]


print(f"Ederson's mean x in 1st half: {df_ederson_1.x.mean()}")
print(f"Ederson's mean x in 2nd half: {df_ederson_2.x.mean()}")

# From this we can infer that City was playing from right to left in the first half
# and left to right in the second. 
# That is, coordinates are not given always from left to right

df_grealish_1 = df_frames[(df_frames.player == 'Jack Grealish') & (df_frames.period == 1)]
df_grealish_2 = df_frames[(df_frames.player == 'Jack Grealish') & (df_frames.period == 2)]

print(f"Grealish's mean y in 1st half: {df_grealish_1.y.mean()}")
print(f"Grealish's mean y in 2nd half: {df_grealish_2.y.mean()}")

# Grealish played on the left wing in the game, thus we can infer that the coordinate system
# has the origin in the upper left corner of the field.
# (He has mean y of 54 in the first half when City are playing from right to left)

#%%
flip_y = True
# For plotting purposes, we flip the y-coordinates (and speed and acceleration)
if flip_y:
    df_frames['y'] = 68 - df_frames['y']
    df_frames[['y_velocity','y_acceleration']] = -1*df_frames[['y_velocity','y_acceleration']]
    flip_y = False

#%%
# Note that to make this work, you might need to download and configure ffmpeg:
# https://www.ffmpeg.org/download.html
# Guide to set it to environmental variables:
# https://www.youtube.com/watch?v=r1AtmY-RMyQ&ab_channel=TroubleChute

# Plot function for each frame 
def update(frame_id):
    ax.clear()
    pitch.draw(ax=ax)  # Redraw the pitch for each frame
    
    frame_data = frames.get_group(frame_id)
    
    #Set properties for the teams and the ball
    teams = {
        'Manchester City':{
            'color': "skyblue", 'size':150},
        'Inter':{
            'color': "blue", 'size':150},
        'ball':{
            'color': "black", 'size':50},
        }

    # Plot each player as a scatter point - Inter as dark blue, City lightblue
    for team, props in teams.items():
        ax.scatter(
            frame_data[frame_data['team_name'] == team]['x'], 
            frame_data[frame_data['team_name'] == team]['y'], 
            s=props['size'], 
            color=props['color'], 
            zorder=5
        )
        
        # Add velocity arrows for each team with specified arrow color
        ax.quiver(
            frame_data[frame_data['team_name'] == team]['x'], 
            frame_data[frame_data['team_name'] == team]['y'],
            frame_data[frame_data['team_name'] == team]['x_velocity'], 
            frame_data[frame_data['team_name'] == team]['y_velocity'],
            angles='xy', scale_units='xy', scale=2, color=props['color'], width=0.003, zorder=4
        )
    
    
    
    # Add jersey numbers on the players
    for _, row in frame_data.iterrows():
        if row['team_name'] != 'ball':
            ax.text(row['x'], row['y'], str(row['jersey_number']), color="white", 
                    ha="center", va="center", fontsize=8, weight="bold", zorder=6)
            
    # Retrieve the game time and period from the frame data
    game_time = frame_data['time'].iloc[0][0:5]  
    period = frame_data['period'].iloc[0]
    
    # Display the game time and period on top of the pitch
    ax.text(
        52.5, 72, f"Period {period} - Time {game_time}", 
        ha="center", va="center", fontsize=15, color="black", fontweight="bold", 
    )

#%%

#Select the frames to plot
frame_min = 40000
frame_max = 40250

df = df_frames[(df_frames.frame > frame_min) & (df_frames.frame < frame_max)]

# Create the pitch
pitch = Pitch(pitch_type='uefa')
fig, ax = pitch.draw(figsize=(10, 7))

# Group data by frame for easier access
frames = df.groupby('frame')
# Create the animation
frame_ids = sorted(df['frame'].unique())
anim = FuncAnimation(fig, update, frames=frame_ids, repeat=False)

# Save the animation as an mp4 video - The data is collected at 25 fps
# You can slow down or speed up the video by changing the fps variable.
anim.save('city_inter.mp4', fps=25)
# -*- coding: utf-8 -*-
"""social media monitoring.ipynb

Automatically generated by Colaboratory.

Original file is located at
    https://colab.research.google.com/drive/1LfS5WfOIaNzIGCwnucuDUIypacwxIEHy

***Process Mining*** - Prof. Paolo Ceravolo

Data Flows

Case study: social media monitoring
"""

# Import the needed libraries

# To better exploit mathematical operations
import numpy as np

# Plotting
import matplotlib.pyplot as plt

# Data Manipulation
import pandas as pd

# Mathematical objects
from math import pi

# Dataset creation

df = pd.read_csv('https://raw.githubusercontent.com/paoloceravolo/PM-Regensburg/main/data.csv', sep=';')


# Computing the dimensions sorting them by descending duration

df.timestamp = pd.to_datetime(df.timestamp)

dimensions = df.groupby('topics').agg({\
'topics': 'count',\
'sentiment': 'sum',\
'irony': 'sum',\
'timestamp': lambda x: x.max() - x.min()\
})

print(dimensions)

dimensions = dimensions.rename(\
	{'topics': 'occurences', 'timestamp': 'duration'}, axis='columns')

dimensions['duration'] = dimensions['duration'].dt.seconds.astype('int32')

dimensions=dimensions.sort_values('duration', ascending=False)

print("The dimensions per topic \n", dimensions)

# Data normalization computing z-scores

for col in dimensions.columns: 
    dimensions[col] = (dimensions[col]-dimensions[col].mean())/dimensions[col].std()
print("\nTop 6 normalized topics \n",dimensions.head(6))

# Taking the first four topics, renaming is just for visualization issues

df = dimensions.head(5).reset_index()
df = df.rename({'topics': 'group'}, axis='columns')

print("\nThe top 5 topics \n",df)

# Radar plot

# ------- PART 1: Create background
 
# number of variable
categories=list(df)[1:]
N = len(categories)
 
# What will be the angle of each axis in the plot? (we divide the plot / number of variable)
angles = [n / float(N) * 2 * pi for n in range(N)]
angles += angles[:1]
 
# Initialise the spider plot
ax = plt.subplot(111, polar=True)
 
# If you want the first axis to be on top:
ax.set_theta_offset(pi / 2)
ax.set_theta_direction(-1)
 
# Draw one axe per variable + add labels labels yet
plt.xticks(angles[:-1], categories)
 
# Draw ylabels
ax.set_rlabel_position(0)
# set the dimension of the radar
plt.yticks([-1,0,1,2], ["-1","0","1", "2"], color="grey", size=7)
plt.ylim(-1,3)
 
 
# ------- PART 2: Add plots
 
# Plot each individual = each line of the data
# I don't do a loop, because plotting more than 3 groups makes the chart unreadable
 
# Ind1
values=df.loc[0].drop('group').values.flatten().tolist()
values += values[:1]
ax.plot(angles, values, linewidth=1, linestyle='solid', label=dimensions.index[0])
ax.fill(angles, values, 'b', alpha=0.1)
 
# Ind2
values=df.loc[1].drop('group').values.flatten().tolist()
values += values[:1]
ax.plot(angles, values, linewidth=1, linestyle='solid', label=dimensions.index[1])
ax.fill(angles, values, 'r', alpha=0.1)

# Ind3
values=df.loc[2].drop('group').values.flatten().tolist()
values += values[:1]
ax.plot(angles, values, linewidth=1, linestyle='solid', label=dimensions.index[2])
ax.fill(angles, values, 'g', alpha=0.1)

# Ind4
values=df.loc[3].drop('group').values.flatten().tolist()
values += values[:1]
ax.plot(angles, values, linewidth=1, linestyle='solid', label=dimensions.index[3])
ax.fill(angles, values, 'm', alpha=0.1)

# Ind5
values=df.loc[4].drop('group').values.flatten().tolist()
values += values[:1]
ax.plot(angles, values, linewidth=1, linestyle='solid', label=dimensions.index[4])
ax.fill(angles, values, 'v', alpha=0.1)
 
# Add legend
plt.legend(loc='upper right', bbox_to_anchor=(0.1, 0.1))

# Visualize
print("Radar Plot")
plt.show()
"""
=============================
Grouped bar chart with labels
=============================

This example shows a how to create a grouped bar chart and how to annotate
bars with labels.
"""
import os
import sys
import matplotlib
import matplotlib.pyplot as plt
import numpy as np

labels = ['Time Bits', 'Symbol Bits', 'Runtime', 'Time OTs', 'Symbol OTs']
data=[]
with open('times.txt', 'r') as fp:
    line = fp.readline() #skip first line
    while fp:
        line = fp.readline()
        if line =="":
            break
        line_data = []
        for num in line.split():
            line_data.append(int(num))
        data.append(line_data)
print(data)
x = np.arange(len(labels))  # the label locations
width = 0.25  # the width of the bars

fig, ax = plt.subplots()

rects = []
for i in range(len(data)):
    y = ax.bar(x + (width*i), data[i], width, label=str(i))
    rects.append(y)

# Add some text for labels, title and custom x-axis tick labels, etc.
ax.set_ylabel(' ')
ax.set_title('Oblivious Transfer Statistics')
ax.set_xticks(x + (width*(len(data)-1)/2))
ax.set_xticklabels(labels)

plt.rcParams['font.size'] = '9'

for label in (ax.get_xticklabels() + ax.get_yticklabels()):
	label.set_fontsize(7)
ax.legend()

def autolabel(rects):
    """Attach a text label above each bar in *rects*, displaying its height."""
    for rect in rects:
        height = rect.get_height()
        ax.annotate('{}'.format(height),
                    xy=(rect.get_x() + rect.get_width() / 2, height),
                    xytext=(0, 3),  # 3 points vertical offset
                    textcoords="offset points",
                    ha='center', va='bottom')
for rect in rects:
    autolabel(rect)

fig.tight_layout()
fig.set_size_inches(w=3.5, h=4)
plt.show()

#############################################################################
#
# ------------
#
# References
# """"""""""
#
# The use of the following functions, methods and classes is shown
# in this example:
matplotlib.use("pgf")
matplotlib.axes.Axes.bar
matplotlib.pyplot.bar
matplotlib.axes.Axes.annotate
matplotlib.pyplot.annotate
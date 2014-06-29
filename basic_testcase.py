# -*- coding: utf-8 -*-
"""
Created on Fri Jun 13 16:13:58 2014

@author: pablo
"""

import simulator as s

# Here we are running a full simulation. If a test is not in the running set,
# it will not run, and if it was going to fail, the failure is ignored.
results = list()

sim = s.simulator(max_limit=5000,learning_set=3000)
sim.prepare_simulation()
res = sim.run_simulation(500)
del sim


import numpy as np
import matplotlib.pyplot as plt
plt.ion()
fig = plt.figure()
ax = fig.gca()

plt.bar(np.arange(len(res.pos_distribution)),res.pos_distribution)
plt.title('Distribution of failed tests in priority queue')
plt.xlabel('Position in priority queue')
plt.ylabel('Number of failures encountered')


"""
PLOT RECALL VS RUNNING SET SIZE

import numpy as np
import matplotlib.pyplot as plt

runs = [50,100,200,300,400,500,600,700,800]
recalls = [0.361,0.552,0.715,0.807,0.842,0.857,0.8657,0.8675,0.8675]
runses = np.asarray(runs,dtype=int)
recallses = np.asarray(recalls,dtype=float)

fig = plt.figure()
ax = fig.gca()
ax.set_yticks(np.arange(0,1.05,0.05))
plt.plot(runses,recallses,label = 'Recall')
plt.ylim(0,1.1)
plt.xlim(0,600)
plt.xlabel('Size of running set')
plt.ylabel('Recall')
plt.legend(loc='lower right')
plt.title('Recall by running set size')
plt.grid()
"""
# -*- coding: utf-8 -*-
"""
Created on Fri Jun 13 16:13:58 2014

@author: pablo
"""

import wrapper as s

# Here we are running a full simulation. If a test is not in the running set,
# it will not run, and if it was going to fail, the failure is ignored.
results = list()

sim = s.wrapper(file_dir = '/home/pablo/codes/files_test_runs/')
#max_limit=5000,learning_set=3000,beginning=10000,
#sim.prepare_simulation()
res = sim.run_simulation(max_limit=5000,learning_set=3000,running_set = 300)
del sim

"""

import numpy as np
import matplotlib.pyplot as plt
plt.ion()
fig = plt.figure()
ax = fig.gca()

plt.bar(np.arange(len(res.pos_distribution)),res.pos_distribution)
plt.title('Distribution of failed tests in priority queue')
plt.xlabel('Position in priority queue')
plt.ylabel('Number of failures encountered')



#PLOT RECALL VS RUNNING SET SIZE

import numpy as np
import matplotlib.pyplot as plt

runs = [50,100,200,300,400,500,600,700,800]
#recalls = [0.361,0.552,0.715,0.807,0.842,0.857,0.8657,0.8675,0.8675]
runs = [300,400,500]
recalls_orig = [0.41,0.446,0.491]
recalls_new = [0.651,0.7072,0.7374]
runses = np.asarray(runs,dtype=int)
recallses = np.asarray(recalls,dtype=float)
recallses_new = np.asarray(recalls_new,dtype=float)
recallses_orig = np.asarray(recalls_orig,dtype=float)

fig = plt.figure()
ax = fig.gca()
ax.set_yticks(np.arange(0,1.05,0.05))
plt.plot(runses,recallses_orig,label = 'Recall of original "standard" strategy')
plt.plot(runses,recalls_new,label = 'Recall of new strategy')
plt.ylim(0,1.1)
plt.xlim(200,600)
plt.xlabel('Size of running set')
plt.ylabel('Recall')
plt.legend(loc='lower right')
plt.title('Recall by running set size')
plt.grid()
"""
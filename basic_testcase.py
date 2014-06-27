# -*- coding: utf-8 -*-
"""
Created on Fri Jun 13 16:13:58 2014

@author: pablo
"""

import simulator as s

# Here we are running a full simulation. If a test is not in the running set,
# it will not run, and if it was going to fail, the failure is ignored.
sim = s.simulator(max_limit=5000,learning_set=3000)
#Recall: 55000 - 50 000 - No multiplier - 33%
sim.prepare_simulation()

pos_dist = sim.run_simulation(200)

import numpy as np
import matplotlib.pyplot as plt
plt.ion()
fig = plt.figure()
ax = fig.gca()
#ax.set_yticks(np.arange(0,1.05,0.05))
#plt.plot(pos_dist,label = 'Standard (Rand)')
plt.bar(np.arange(len(pos_dist)),pos_dist)
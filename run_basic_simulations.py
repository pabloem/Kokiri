# -*- coding: utf-8 -*-
"""
Created on Thu May 22 11:08:48 2014

@author: pablo
"""

import simulator as s
import numpy as np

#sim = s.simulator(time_factor=True)
sim = s.simulator(time_factor=True,test_edit_factor=True,full_simulation=False)

sim.prepare_simulation()

standard_results = list()
platform_results = list()
branch_results = list()
mixed_results = list()

#Sizes of the running sets, to graph number of caught failures
run_sets = (5,10,15,20,30,40,50,60,70,80,90,100,120,140,160,180,200,230,260,290,320,350,400,450,500,600,700,800)
basic_run_sets = (20,50,70,100,160,230,290,350,400,500,600,700,800)
basic_run_sets = (500,)

run_sets = basic_run_sets

for rset in run_sets:  # This loop takes several hours
    standard_results.append(sim.run_simulation(rset,'standard'))
    platform_results.append(sim.run_simulation(rset,'platform'))
    branch_results.append(sim.run_simulation(rset,'branch'))
    mixed_results.append(sim.run_simulation(rset,'mixed'))

caught_f_std = np.ndarray(dtype=float,shape=len(run_sets))
caught_f_plt = np.ndarray(dtype=float,shape=len(run_sets))
caught_f_brn = np.ndarray(dtype=float,shape=len(run_sets))
caught_f_mix = np.ndarray(dtype=float,shape=len(run_sets))
for i in range(len(run_sets)):
    caught_f_std[i] = standard_results[i].caught_failures
    caught_f_plt[i] = platform_results[i].caught_failures
    caught_f_brn[i] = branch_results[i].caught_failures
    caught_f_mix[i] = mixed_results[i].caught_failures
max_f = max(caught_f_mix)+0.0
for i in range(len(run_sets)):
    caught_f_std[i] = caught_f_std[i]/max_f
    caught_f_plt[i] = caught_f_plt[i]/max_f
    caught_f_brn[i] = caught_f_brn[i]/max_f
    caught_f_mix[i] = caught_f_mix[i]/max_f


import matplotlib.pyplot as plt

rsets = np.asarray(run_sets,dtype=int)

fig = plt.figure()
ax = fig.gca()
ax.set_yticks(np.arange(0,1.05,0.05))
plt.plot(rsets,caught_f_std,label = 'Standard')
plt.plot(rsets,caught_f_plt,label = 'Platform')
plt.plot(rsets,caught_f_brn,label = 'Branch')
plt.plot(rsets,caught_f_mix,label = 'Mixed (Branch/Platform)')
plt.ylim(0,1.1)
plt.xlabel('Size of running set')
plt.ylabel('Recall')
plt.legend(loc='lower right')
plt.title('Recall by running set size')
plt.grid()
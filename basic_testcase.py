# -*- coding: utf-8 -*-
"""
Created on Fri Jun 13 16:13:58 2014

@author: pablo
"""

import simulator as s
import numpy as np

# Here we are running a full simulation. If a test is not in the running set,
# it will not run, and if it was going to fail, the failure is ignored.
sim = s.simulator(time_factor=True,randomize_tail=True,full_simulation=True,do_logging=True)

sim.prepare_simulation()


standard_results = list()
platform_results = list()
branch_results = list()
mixed_results = list()


basic_run_sets = (20,50,100,150,200,250,350,400,500)
run_sets = basic_run_sets

for rset in run_sets:  # This loop takes several hours
    standard_results.append(sim.run_simulation(rset,'standard'))
    sim.cleanup()
    platform_results.append(sim.run_simulation(rset,'platform'))
    sim.cleanup()
    branch_results.append(sim.run_simulation(rset,'branch'))
    sim.cleanup()
    mixed_results.append(sim.run_simulation(rset,'mixed'))
    sim.cleanup()

standard_results1 = list()
platform_results1 = list()
branch_results1 = list()
mixed_results1 = list()

sim = s.simulator(time_factor=True,randomize_tail=False,full_simulation=True,do_logging=True)

sim.prepare_simulation()

basic_run_sets = (20,50,100,150,200,250,350,400,500)
run_sets = basic_run_sets

for rset in run_sets:  # This loop takes several hours
    standard_results1.append(sim.run_simulation(rset,'standard'))
    sim.cleanup()
    platform_results1.append(sim.run_simulation(rset,'platform'))
    sim.cleanup()
    branch_results1.append(sim.run_simulation(rset,'branch'))
    sim.cleanup()
    mixed_results1.append(sim.run_simulation(rset,'mixed'))
    sim.cleanup()

caught_f_std = np.ndarray(dtype=float,shape=len(run_sets))
caught_f_mix = np.ndarray(dtype=float,shape=len(run_sets))
caught_f_plt = np.ndarray(dtype=float,shape=len(run_sets))
caught_f_brch = np.ndarray(dtype=float,shape=len(run_sets))
caught_f_std1 = np.ndarray(dtype=float,shape=len(run_sets))
caught_f_mix1 = np.ndarray(dtype=float,shape=len(run_sets))
caught_f_plt1 = np.ndarray(dtype=float,shape=len(run_sets))
caught_f_brch1 = np.ndarray(dtype=float,shape=len(run_sets))
n_caught_f_std = np.ndarray(dtype=float,shape=len(run_sets))
n_caught_f_mix = np.ndarray(dtype=float,shape=len(run_sets))
n_caught_f_plt = np.ndarray(dtype=float,shape=len(run_sets))
n_caught_f_brch = np.ndarray(dtype=float,shape=len(run_sets))
n_caught_f_std1 = np.ndarray(dtype=float,shape=len(run_sets))
n_caught_f_mix1 = np.ndarray(dtype=float,shape=len(run_sets))
n_caught_f_plt1 = np.ndarray(dtype=float,shape=len(run_sets))
n_caught_f_brch1 = np.ndarray(dtype=float,shape=len(run_sets))
for i in range(len(run_sets)):
    caught_f_std[i] = standard_results[i].caught_failures
    caught_f_mix[i] = mixed_results[i].caught_failures
    caught_f_plt[i] = platform_results[i].caught_failures
    caught_f_brch[i] = branch_results[i].caught_failures
    caught_f_std1[i] = standard_results1[i].caught_failures
    caught_f_mix1[i] = mixed_results1[i].caught_failures
    caught_f_plt1[i] = platform_results1[i].caught_failures
    caught_f_brch1[i] = branch_results1[i].caught_failures
max_f = standard_results[0].caught_failures + standard_results[0].missed_failures
for i in range(len(run_sets)):
    n_caught_f_std[i] = caught_f_std[i]/max_f
    n_caught_f_mix[i] = caught_f_mix[i]/max_f
    n_caught_f_plt[i] = caught_f_plt[i]/max_f
    n_caught_f_brch[i] = caught_f_brch[i]/max_f
    n_caught_f_std1[i] = caught_f_std1[i]/max_f
    n_caught_f_mix1[i] = caught_f_mix1[i]/max_f
    n_caught_f_plt1[i] = caught_f_plt1[i]/max_f
    n_caught_f_brch1[i] = caught_f_brch1[i]/max_f
    

import matplotlib.pyplot as plt

rsets = np.asarray(run_sets,dtype=int)

fig = plt.figure()
ax = fig.gca()
ax.set_yticks(np.arange(0,1.05,0.05))
plt.plot(rsets,n_caught_f_std,label = 'Standard (Rand)')
plt.plot(rsets,n_caught_f_mix,label = 'Mixed (Rand)')
plt.plot(rsets,n_caught_f_plt,label = 'Platform (Rand)')
plt.plot(rsets,n_caught_f_brch,label = 'Branch (Rand)')
plt.plot(rsets,n_caught_f_std1,label = 'Standard (No Rand)')
plt.plot(rsets,n_caught_f_mix1,label = 'Mixed (No Rand)')
plt.plot(rsets,n_caught_f_plt1,label = 'Platform (No Rand)')
plt.plot(rsets,n_caught_f_brch1,label = 'Branch (No Rand)')
plt.ylim(0,1.1)
plt.xlabel('Size of running set')
plt.ylabel('Recall')
plt.legend(loc='lower right')
plt.title('Recall by running set size')
plt.grid()
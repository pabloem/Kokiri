# -*- coding: utf-8 -*-
"""
Created on Fri Jun 13 16:13:58 2014

@author: pablo
"""

import simulator as s
#import numpy as np
import simulation_result

# Here we are running a full simulation. If a test is not in the running set,
# it will not run, and if it was going to fail, the failure is ignored.
sim = s.simulator(time_factor=True,test_edit_factor=True,full_simulation=True)

sim.prepare_simulation()

res = sim.run_simulation(500,'mixed')
print 'Caught failures: ' + str(res.caught_failures) + ' | Total failures : '+\
        str(res.caught_failures+res.missed_failures)

del sim

# Here we are not running a full simulation. All failures are considered as caught
sim = s.simulator(full_simulation=False)

sim.prepare_simulation()

res2 = sim.run_simulation(500,'mixed')
print 'Caught failures: ' + str(res2.caught_failures) + ' | Total failures : '+\
        str(res2.caught_failures+res2.missed_failures)
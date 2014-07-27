# -*- coding: utf-8 -*-
"""
Created on Fri Jun 13 16:13:58 2014

@author: pablo
"""

import wrapper as s

sim = s.wrapper(file_dir = '/home/pablo/codes/files_test_runs/')
rec = sim.run_simulation(max_limit=300000,learning_set=3000,beginning=127000,running_set = 0.3)

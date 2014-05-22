This repository contains the code to analyze and run simulations on the testing
data from MariaDB development.

Files:
 - basic_simulator.py -- This file contains the simulator class that does the
                        basic simulations using exponential decay or weighted
                        average.
 - run_basic_simulations.py -- This file contains the code to run and graph
                        results from a set of basic simulations. The code is
                        quite self explanatory.
 - name_extractor.py
 - read_history.py -- These two files contain functions in charge of extracting
                        data for the analysis. The data is extracted from the 
                        csv/ and sqlstatements/ directories
 - logs/            -- This directory is where the logs from the test runs are
                        dumped.

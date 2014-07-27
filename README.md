This repository contains the code to analyze and run simulations on the testing
data from MariaDB development.

IMPORTANT TO DECOMPRESS direct_file_changes.csv in the csv/ directory

Files:
 - basic_simulator.py -- This file contains the simulator class that does the
                        basic simulations using exponential decay or weighted
                        average.
 - basic_testcase.py -- This file contains the code to run a basic simulation
 
 - name_extractor.py
 - read_history.py -- These two files contain functions in charge of extracting
                        data for the analysis. The data is extracted from the 
                        csv/ and sqlstatements/ directories
 - logs/            -- This directory is where the logs from the test runs are
                        dumped.

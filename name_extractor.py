# -*- coding: utf-8 -*-
"""
Created on Fri May  2 16:37:54 2014

@author: pablo
"""

import re #Regular expressions framework
import os #Operating system framework
import logging # Debug logging framework

def extract_names_from_testrun():
    logger = logging.getLogger('extract')
    p = re.compile('^(\S+) +(\'(\S+)\')? +(w\d)? +\[ pass \] +(\d+)$')
    
    """
    SETTING DIRECTORY. CHANGE IF RUNNING ON A DIFFERENT MACHINE OR SETTING
    """
    os.chdir("/home/pablo/codes/Kokiri")
    files = os.listdir("test_runs/")
    
    tests = dict()
    # Scan through all files, and get test names
    for file in files:
        logger.info("Test names from file: =====\""+file+"\"")
        get_lines = open("test_runs/"+file,'r')
        for line in get_lines:
            m = p.match(line)
            if m:
                tests[str(m.group(1))+' '+str(m.group(3))]['time'] = \
                    int(m.group(5))
                logger.debug("test["+str(m.group(1))+' '+str(m.group(3))+\
                    "]['time'] = "+m.group(5))
                #The test length is indexed by "test_name test_variation"
        logger.info("====="+str(len(tests))+" test names/variations inserted")
    return tests

def extract_names_from_failures():
    logger = logging.getLogger('extract')
    import csv
    tests = dict()
    filename = "csv/test_namevar.csv"
    f = open(filename,'r')
    reader = csv.reader(f)
    logger.info("Reading from file "+filename)
    count = 0
    for row in reader:
        logger.debug("row: "+str(row))
        tests[row[0]+' '+row[1]] = dict()
        (tests[row[0]+' '+row[1]])['time'] = 1
        count=count+1
    logger.info("Read "+str(count)+" test names from "+filename)
    return tests

"""
FUNCTION: get_all_test_names

This function returns all the test names+variations available in the 
test_namevar.csvand the typescript log files. This yields a large number 
of test/variation keys
"""
def get_all_test_names():
    test2 = extract_names_from_failures()
    """
    test1 = extract_names_from_testrun()
    for key in test2.keys():
        if key not in test1:
            test1[key] = 1
    """
    return test2

# -*- coding: utf-8 -*-
"""
Created on Tue May  6 11:43:16 2014

@author: pablo
"""

"""
Function: get_test_history
This function loads the test history and returns:
FIELDS (DICT)
    -TIMESTAMPS
    -BRANCHES
    -PLATFORMS
    -TYPS
    -FAIL_COUNTS
    
    ALL the DICTs inside FIELDS are indexed by TEST_RUN_ID
"""
import logging
def get_test_history(tr_filename):
    logger = logging.getLogger('extract')
    import csv
    #tr_filename = 'csv/fails_ptest_run.csv'
    tr_file = open(tr_filename,'r')
    tr_reader = csv.reader(tr_file)
    """
    STATEMENT FOR THE FAILS_PER_RUN FILE:
    timestamp,run_id, build_id, buildset_id, sourcestamp_id, tr_revision,
    ss.revision, tr_branch, ss.branch, platform,TYP, fails 
    """
    TIMESTAMP = 0
    RUN_ID = 1
    #BUILD_ID = 2 # THIS IS NOT BEING USED
    #BUILDSET_ID = 3 # THIS IS NOT BEING USED
    #SOURCESTAMP_ID = 4 # THIS IS NOT BEING USED
    #TR_REVISION = 5 # THIS IS NOT BEING USED
    #SS_REVISION = 6 # THIS IS NOT BEING USED
    BRANCH = 7
    #SS_BRANCH = 8 # THIS IS NOT BEING USED
    PLATFORM = 9
    TYP = 10
    FAILS = 11
    """
    ===============================================================================
    EXACTLY:
        select 
    unix_timestamp(cntr.dt) timestamp,trid run_id, b.id bbid, bs.id bsid, ss.id ssid,
    trrev,ss.revision ssrev,trbranch,ss.branch ssbranch, platform,trtyp, 
    sum(num) fails 
        from 
        (select tr.dt dt,tr.typ trtyp,tr.id trid,tr.bbnum trbid, platform, 
         tr.revision trrev, tr.branch trbranch, if(tf.test_name is null,0,1) num 
         from test_run tr left join test_failure tf on tr.id = tf.test_run_id 
         order by 1 desc) 
    cntr, builds b, buildrequests br, buildsets bs, sourcestamps ss 
        where  
    cntr.trbid = b.id and br.id = b.brid and bs.id = br.buildsetid and 
    bs.sourcestampid = ss.id group by 1 order by 1 desc
    ===============================================================================  
    In the following lines, we store information from the historical data on
    test_runs into dictionaries. These data will be used to integrate a data frame
    later on
    """
    timestamps = dict()
    branches = dict()
    platforms = dict()
    typs = dict()
    fail_counts = dict()
    logger.info('Loading test_run history from file '+tr_filename)
    count = 0
    for row in tr_reader:
        logger.debug('Loaded row['+row[RUN_ID]+'] = ' + str(row))
        timestamps[int(row[RUN_ID])] = int(row[TIMESTAMP])
        branches[int(row[RUN_ID])] = row[BRANCH]
        platforms[int(row[RUN_ID])] = row[PLATFORM]
        typs[int(row[RUN_ID])] = row[TYP]
        fail_counts[int(row[RUN_ID])] = int(row[FAILS])
        count = count+1
    logger.info('Loaded ' +str(count)+' rows')
    fields = dict()
    fields['timestamps'] = timestamps
    fields['branches'] = branches
    fields['platforms'] = platforms
    fields['typs'] = typs
    fields['fail_counts'] = fail_counts
    return fields

"""
Function: get_failure_history
    This function loads the test_failure history
Returns:
    A list of TEST_RUN_ID, TEST_NAME, TEST_VARIANT elements
    These elements indicate that TEST_NAME,TEST_VARIANT failed when it was run
    in TEST_RUN. These data can later be added to the dataframe
"""
def get_failure_history(tf_filename):
    logger = logging.getLogger('extract')
    import csv
    #tf_filename = 'csv/test_fail_history.csv'
    tf_file = open(tf_filename,'r')
    tf = csv.reader(tf_file)
    logger.info('Loading test failure history from file '+tf_filename)
    """
    Statement from TEST_FAIL_HISTORY:
    timestamp, test_run_id, test_name, test_variant, branch,
    revision, platform, typ, build_num
    """
    #TIMESTAMP = 0
    TEST_RUN_ID = 1
    TEST_NAME = 2
    TEST_VARIANT = 3
    #BRANCH = 4
    #REVISION = 5
    #PLATFORM = 6
    #TYP = 7
    #BUILD_NUM = 8
    """
    ===========================================================================
    EXACTLY
    select 
        unix_timestamp(tr.dt) timestamp, test_run_id run_id,test_name, 
        test_variant, branch, revision, platform, typ, bbnum 
    from 
        test_run tr, test_failure tf where tr.id = tf.test_run_id 
        order by 1 desc
    ===========================================================================
    """
    test_failures = list()
    count = 0
    for row in tf:
        test_failures.append\
            ([int(row[TEST_RUN_ID]),row[TEST_NAME],row[TEST_VARIANT]])
        count = count+1
    logger.info('Loaded '+str(count)+' records')
    return test_failures
"""
FUNCTION: load_failures
this function takes in the test_info dictionary, and goes through the failure
history file, attaching the test_run id to the test_info of each test
"""    
def load_failures(test_info, failure_per_test_run,\
                    failures_file='csv/test_fail_history.csv'):
    logger = logging.getLogger('extract')
    t_fails = get_failure_history(failures_file)
    """
    Now we go through the all the failures, and store in the test_info the
    test_run_id of the test that failed
    """
    count_fails = 0
    for fail in t_fails:
        count_fails = count_fails + 1
        test_name = fail[1]+' '+fail[2]
        #Adding the test_run number to the test_info
        if test_name in test_info:
            if 'failures' not in test_info[test_name]:
                test_info[test_name]['failures'] = list()
            test_info[test_name]['failures'].append(fail[0])
        #Adding the test_name to the test_run info
        if fail[0] not in failure_per_test_run:
            failure_per_test_run[fail[0]] = list()
        failure_per_test_run[fail[0]].append(test_name)
    logger.info('Reviewed '+str(count_fails)+' failures')

"""
FUNCTION: open_test_history
This function simply returns the csv read handler for the test history file
"""
def open_test_history(file_name='csv/test_fail_history_inv.csv'):
    import csv
    f = open(file_name,'r')
    tr_reader = csv.reader(f)
    return tr_reader
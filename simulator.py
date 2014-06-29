# -*- coding: utf-8 -*-
"""
Created on Tue May 20 18:42:05 2014

@author: pablo
"""
"""============================================================="""
"""====================== IMPORTANT IMPORTS ===================="""
"""============================================================="""
import logging # Debug logging framework
import numpy
#import math
import name_extractor as ne
import read_history as rh
import heapq
import simulation_result
import random

import ipdb

class simulator:
    logger = None
    """============================================================="""
    """===================== IMPORTANT CONSTANTS ==================="""
    """============================================================="""
    TIMESTAMP = 0
    RUN_ID = 1
    BRANCH = 7
    PLATFORM = 9
    TYP = 10
    FAILS = 11
    
    max_limit=5000
    omniscient = False
    learning_set = 2000
    running_set = None
    
    """============================================================="""
    """==============DEBUG LEVELS AND EXPLANATION==================="""
    """============================================================="""
    """WA_DEBUG AND ED_DEBUG ARE RELEVANCY COEFFICIENT DEBUG LEVELS,"""
    """THEY ARE DESIGNED TO BE USED WHEN WE WANT TO DEBUG ONE OF    """
    """THESE MEASURES. THEY ARE CONCEPTUALLY *LESS DEEP* THAN       """
    """THE DEEP_DEBUG LEVEL. IF USING DEEP_DEBUG, THE CORRESPONDING """
    """MEASURE DEBUG IS RECOMMENDED AS WELL                         """
    """============================================================="""
    WA_DEBUG = 7
    ED_DEBUG = 6
    DEEP_DEBUG = 5
    
    test_info = dict()
    file_info = dict()
    fail_per_testrun = dict()
    file_changes = None
    
    """
    Function: get_correlation
    This function calculates correlation between the failures of a test and
    the occurrence of another event
    - test_failures - Number of times a test has failed in this context
    - event_haps - Number of times the event has occurred in this context
        -- Test failed in previous test run
        -- File changed since last test run
    - correlated_haps - Number of times a test has failed AFTER the event has
                        happened
    """
    def get_correlation(self,test_failures,event_haps, correlated_haps):
        corr = correlated_haps/event_haps
        #corr = correlated_haps/test_failures
#        N = test_failures+event_haps-correlated_haps+1
#        corr = (N*correlated_haps - test_failures*event_haps) /\
#                (math.sqrt(N*test_failures-test_failures*test_failures)*\
#                math.sqrt(N*event_haps - event_haps*event_haps))
#        self.logger.debug('TF: '+str(test_failures)+' | EV: '+str(event_haps)+
#            ' | CH: '+str(correlated_haps)+' | CR: '+str(corr))
        return -corr
        # IMPORTANT - We return the NEGATIVE correlation because heapq 
        # gives high priority to lower values
        
        
    """
    Function: cleanup
    This function is in charge of resetting the simulator to its state before
    running any simulations.
    """
    def cleanup(self):
        return 1
    
    class Mode():
        standard = 'standard'
        platform = 'platform'
        branch = 'branch'
        mixed = 'mixed'
        
    """
    Function prepare_simulation
    This function initializes all the data that is essential for a simulation.
    Mainly, it initializes the test_info dictionary, and filling up the failures
    list in each test (test_info[test_name]['failures'] = list())
    (The failures list contains all the IDs from the test_runs where test_name
    has failed)
    """
    def prepare_simulation(self,fails_file=None):
        if len(self.test_info) == 0:
            self.test_info = ne.get_all_test_names()
        if len(self.fail_per_testrun) == 0:
            if fails_file is None:
                rh.load_failures(self.test_info, self.fail_per_testrun)
            else:
                rh.load_failures(self.test_info, self.fail_per_testrun,
                                failures_file=fails_file)
        if self.file_changes is None:
            self.file_changes = rh.load_file_changes()
        """
        Now we get the history of test_file editions
        """
#        if self.test_edit_factor:
#            rh.get_test_file_change_history(test_info=self.test_info)
    

    """
    Function: add_to_pos_dis_array
    This function is in charge of making the pos_dist array longer if necessary,
    and then adding to the distribution of positions
    """
    def add_to_pos_dis_array(self,pos_dist,ind):
        # If we need to increase the size of the pos_dist array, we do
        # up to the next 100
        if ind >= 0 and ind >= pos_dist.size:
            sz = ind+1
            chg_size = sz if sz % 100 == 0 else sz + 100 - sz % 100
            prev_size = pos_dist.size
            pos_dist = numpy.resize(pos_dist,chg_size)
            pos_dist[prev_size:pos_dist.size] = 0 #Making new elements zero
        if ind >= 0:
            pos_dist[ind] += 1
            
    
    """
    Function: get_last_run
    This function is in charge of returning the last test_run that concerns us,
    according to the Mode. If the mode is Platform, we return the last run on 
    the same Platform, and so on  for branch and Branch/Platform mix.
    """
    def get_last_run(self,runs,mode,test_run,runs_pq):
        if mode == self.Mode.standard and 'standard' in runs:
            return runs['standard']
        if mode == self.Mode.branch and test_run[self.BRANCH] in runs:
            return runs[test_run[self.BRANCH]]
        if mode == self.Mode.platform and test_run[self.PLATFORM] in runs:
            return runs[test_run[self.PLATFORM]]
        if mode == self.Mode.mixed and test_run[self.BRANCH]+' '+test_run[self.PLATFORM] in runs:
            return runs[test_run[self.BRANCH]+' '+test_run[self.PLATFORM]]
        
        self.logger.debug('No last_run found for this case. Using simpler.')
        # We prioritize the most specific last_run we can find, starting by
        # BRANCH, and then PLATFORM.
        if (mode == self.Mode.mixed or mode == self.Mode.platform) and\
                test_run[self.BRANCH] in runs:
            return runs[test_run[self.BRANCH]]
        if (mode == self.Mode.mixed or mode == self.Mode.branch) and\
                test_run[self.PLATFORM] in runs:
            return runs[test_run[self.PLATFORM]]
        for elm in runs:
            if runs[elm][self.RUN_ID] == runs_pq[0][1]:
                return runs[elm]
        return None
    
    """
    Function: get_fails
    This function returns a list of failures occurred in test_run
    """
    def get_fails(self,test_run):
        if int(test_run[self.RUN_ID]) in self.fail_per_testrun:
            return self.fail_per_testrun[int(test_run[self.RUN_ID])]
        return list()

    """
    Function: get_events(start_run,end_run)
    This function returns the events that occurred from start_run until end_run
    the events are of three types:
        - test_failures
        - file_changes
        - test_file_changes NOT COLLECTING YET
    """
    def get_events(self,start_run,end_run,mode,earliest_timestamp):
        
        assert int(start_run[self.TIMESTAMP])<int(end_run[self.TIMESTAMP])
            
        self.logger.debug('S_RUN: '+start_run[self.RUN_ID]+
                            ' | E_RUN: '+end_run[self.RUN_ID]+
                            ' | EARLY_TIME: '+str(earliest_timestamp))
        events = dict()
        events['recent_failures'] = self.get_fails(start_run)
        
        events['file_changes'] = dict()
        count = 0
        useless_elements = 0
        TIMESTAMP = 0
        FILENAME = 1
        BRANCH = 2
        for f in self.file_changes:
            count += 1
            if int(f[TIMESTAMP]) < earliest_timestamp:
                useless_elements += 1
            if int(f[TIMESTAMP]) < int(start_run[self.TIMESTAMP]):
                continue
            if int(f[TIMESTAMP]) > int(end_run[self.TIMESTAMP]):
                break
#            if (mode == self.Mode.branch or mode == self.Mode.mixed) and\
#                    end_run[self.BRANCH] != f[BRANCH]:
#                continue
            if f[FILENAME] not in events['file_changes']:
                events['file_changes'][f[FILENAME]] = 0
            events['file_changes'][f[FILENAME]] += 1
            
        self.file_changes = self.file_changes[useless_elements:]
        #self.logger.debug('CHCKD: '+str(count)+' | FLS '+str(len(events['recent_failures']))+'\n')
        return events
        
    """
    Function: update_event_information
    This function adds the correlated numbers for all tests
    """
    def update_event_information(self,fails,events,test_run,count):
        for test_name in self.test_info:
            if count % 50 != 0:
                break
            if 'fails_per_100' in self.test_info[test_name]:
                self.test_info[test_name]['fails_per_100'] *= 0.5
        for failed_test in fails:
            # Write down that the test failed
            if 'failures' not in self.test_info[failed_test]:
                self.test_info[failed_test]['failures'] = 0
            self.test_info[failed_test]['failures'] += 1.0
            if 'fails_per_100' not in self.test_info[failed_test]:
                self.test_info[failed_test]['fails_per_100'] = 0
            self.test_info[failed_test]['fails_per_100'] += 1
            
            # If the test failed in the previous test run, and in the new one, 
            # we write it down
            if failed_test in events['recent_failures']:
                if 'test_events' not in self.test_info[failed_test]:
                    self.test_info[failed_test]['test_events'] = 0
                self.test_info[failed_test]['test_events'] += 1.0
            
            # We write down the files that were changed between the previous
            # test run, and the new one
            if 'file_events' not in self.test_info[failed_test]:
                self.test_info[failed_test]['file_events'] = dict()
            multiplier = len(events['file_changes'])
            for edit in events['file_changes']:
                if edit not in self.test_info[failed_test]['file_events']:
                    self.test_info[failed_test]['file_events'][edit] = 0
                self.test_info[failed_test]['file_events'][edit] += 1.0/multiplier
                
        # We also write down how many times a file has been changed
        # we may use this later to calculate correlations
        for filename in events['file_changes']:
            if filename not in self.file_info:
                self.file_info[filename] = 0
            self.file_info[filename] += 1
        
        # We must update the fail_per_testrun list to remember only the fails
        # that we have seen for sure
        if int(test_run[self.RUN_ID]) in self.fail_per_testrun:
            self.fail_per_testrun[int(test_run[self.RUN_ID])] = fails
    
    """
    Function: calculate_relevancy
    This function calculates the relevancy of a test by adding up the historical 
    correlations between the recent events and the test that is going to be run
    """
    def calculate_relevancy(self,test_name,events):
        recent_fails = events['recent_failures']
        file_changes = events['file_changes']
        relevancy = 0.0
        
        if 'failures' not in self.test_info[test_name]:
            self.test_info[test_name]['failures'] = 0
            logging.debug('Supplemented FAILURES to self.test_info['+test_name+']')
        if 'file_events' not in self.test_info[test_name]:
            self.test_info[test_name]['file_events'] = dict()
            logging.debug('Supplemented FILE_EVENTS to self.test_info['+test_name+']')
        if 'test_events' not in self.test_info[test_name]:
            self.test_info[test_name]['test_events'] = 0
            logging.debug('Supplemented TEST_EVENTS to self.test_info['+test_name+']')
        
        for filename in file_changes:
            # If there are no correlations, no need to measure
            if filename not in self.file_info or self.file_info[filename] == 0:
                continue
            if filename in self.test_info[test_name]['file_events']:
                relevancy+= self.get_correlation(
                                    self.test_info[test_name]['failures'],
                                    self.file_info[filename],
                                    self.test_info[test_name]['file_events'][filename])
                                
        # We check that it's more than 1 since correlation func is numerically unstable
        if test_name in recent_fails and self.test_info[test_name]['failures'] > 1:
            relevancy += self.get_correlation(
                                self.test_info[test_name]['failures'],
                                self.test_info[test_name]['failures']-1,
                                self.test_info[test_name]['test_events'])
        if 'fails_per_100' in self.test_info[test_name]:
            relevancy -= self.test_info[test_name]['fails_per_100']/100
#        if relevancy != 0.0:
#            self.logger.debug('TST: '+test_name+'\tRLV: '+str(relevancy))
        return relevancy
    
    """
    Function: catch_failures
    This function is in charge of calculating relevancies for tests, and 
    building the priority queue to determine which tests will run.
    If we are in training mode, this step is skipped
    """
    def catch_failures(self,training,events,fails,pos_dist):
        if training:
            return fails
            
        TST_NAME = 1 # This is the index of TST NAME in the priority queues
        pr_q = list() # Here is the priority queue
        zeroes = 0
        for test_name in self.test_info:
            relv = self.calculate_relevancy(test_name,events)
            if relv == 0.0:
                zeroes +=1
            heapq.heappush(pr_q,(relv,test_name))
            
        pr_q = sorted(pr_q,key = lambda elem: elem[0])
        if zeroes < len(self.test_info):
            self.logger.debug('PQ: '+str(pr_q[0:5]))
        else:
            self.logger.debug('ALL ZEROES')
        caught_f = list()
        for ind, elm in enumerate(pr_q):
            if elm[TST_NAME] in fails:
                self.add_to_pos_dis_array(pos_dist,ind)
                
                # If we are supposed to see the failure, or if we are 
                # allowed to see ALL failures by default, we 'catch' it
                if ind < self.running_set or self.omniscient:
                    fails.remove(elm[TST_NAME])
                    caught_f.append(elm[TST_NAME])
        
        return caught_f

    """
    Function: remove_from_runs_pq
    This function is in charge of removing a test run from the priority queue
    of latest test runs. This allows to keep track of how old should be the 
    files that we want to look at
    """
    def remove_from_runs_pq(self,test_run,runs_pq):
        RUN_ID = 1
        rmv = -1
        for ind,elm in enumerate(runs_pq):
            if elm[RUN_ID] == test_run[self.RUN_ID]:
                rmv = ind
                break
        if rmv >= 0:
            runs_pq.pop(rmv)
            heapq.heapify(runs_pq)
            return
        self.logger.debug('FAILED to REMOVE')
    
    """
    Function: update_last_run
    This function simply updates the recently made run as the last run on the
    corresponding branch, platform, and mix
    """
    def update_last_run(self,runs,test_run,runs_pq):
        # Recording this as the last test run in the corresponding categories
        pr_num = len(runs_pq)
        if len(runs_pq) > 4:
            pr_num = 4
        self.logger.debug('NE: '+
                        str((test_run[self.TIMESTAMP],test_run[self.RUN_ID]))+
                        'RUNS_PQ: '+str(runs_pq[0:pr_num]))
                        
        if (test_run[self.BRANCH]+' '+test_run[self.PLATFORM] in runs):
            self.remove_from_runs_pq(runs[test_run[self.BRANCH]+' '+test_run[self.PLATFORM]],runs_pq)
            
        runs[test_run[self.BRANCH]+' '+test_run[self.PLATFORM]] = test_run
        runs['standard'] = test_run
        runs[test_run[self.BRANCH]] = test_run
        runs[test_run[self.PLATFORM]] = test_run
        heapq.heappush(runs_pq,(int(test_run[self.TIMESTAMP]),test_run[self.RUN_ID]))
    
    
    """
    Function: prepare_result
    This function fills up the result object that shows all the information 
    relevant to the test run
    """
    def prepare_result(self,pos_dist,missed_failures,caught_failures,mode):
        #TODO add extra information to the run result
        res = simulation_result.simulation_result()
        res.pos_distribution = pos_dist
        res.caught_failures = caught_failures
        res.missed_failures = missed_failures
        res.mode = mode
        return res
            
    """
    Function: run_simulation
    This is the main simulator function. This function runs the learning round
    and then the simulation.
    Arguments:
        = metric -      This is the metric that will be used to calculate relevancy 
                        of a test. ['weighted_avg','exp_decay']
        = running_set - This is the size of the running set. The number of tests
                        that will be consudered as run every new iteration. [int]
        = full_simulation - If this metric is False, the calculation of the relev.
                        index of a test will not depend on the running set.
                        If if is True, the calculation of the relevancy index
                        will depend on whether the test was inside the running set
                        or not. [True, False]
    """
    def run_simulation(self, running_set, mode=Mode.mixed):
        #ipdb.set_trace()
        self.running_set = running_set
        test_hist = rh.open_test_history()
        count = 0
        missed_failures = 0 # These are failures that would have been caught if the test had run
        caught_failures = 0 # These are failures that are caught - because the test ran
        training = True # This parameter is turned to false after the training round
        runs = dict() # We keep a dictionary of the last runs
        runs_pq = list()
        pos_dist = numpy.zeros(dtype=int,shape=1000) # Distribution of positions of tests
        
        self.logger.info('Simulating. RS: '+str(running_set)+' Mode: '+mode)
            
        """
        test_hist is the list from the query of test_run history. It returns 
        one-by-one the test_runs.
        In the following loop, we iterate over each test run, from the first to
        the last
        """
        for tr_index,test_run in enumerate(test_hist):
            fails = list()
            if count == self.learning_set:
                # First self.learning_set iterations are the learning set. 
                # After that, the simulation starts.
                training = False
                self.logger.debug("==============SIMULATION HAS BEGUN================")
            count=count+1
            
            if count > self.max_limit:
                break # If we have iterated the max_limit of test_runs, we break out
                
            last_run = self.get_last_run(runs,mode,test_run,runs_pq)
            if last_run is None:
                # If we couldn't decide on a last_run, then we don't know any
                # previous information, and thus can't do any predictions
                # we set this run as the latest one, and will use its information
                self.update_last_run(runs,test_run,runs_pq)
                continue
            #TODO change this to prqueue of test_runs
            events = self.get_events(last_run,test_run,mode,runs_pq[0][0])
            fails = self.get_fails(test_run)
            num_fails = len(fails)

            fails = self.catch_failures(training,events,fails,pos_dist)
            self.logger.info('RUN #'+test_run[self.RUN_ID]+' | FLS: '+
                str(len(fails)) +' | EDFS: '+str(len(events['file_changes']))+
                ' | PRV: #'+last_run[self.RUN_ID]+' | BR: '+test_run[self.BRANCH]+
                ' | PLT: '+test_run[self.PLATFORM])
            
            if not training:
                caught_failures += len(fails)
                missed_failures += num_fails-len(fails)
            
            #After the predictions, we store the information that we have so far
            self.update_event_information(fails,events,test_run,count)
            
            self.update_last_run(runs,test_run,runs_pq)

        """
        END OF THE SIMULATION - Final logging
        """
        self.logger.info('MF: '+str(missed_failures)+' | CF: '+str(caught_failures)+
                    ' | TF: '+str(missed_failures+caught_failures) +
                    ' | RECALL: '+str(caught_failures/(missed_failures+caught_failures+0.0)))
                    
        return self.prepare_result(pos_dist,missed_failures,caught_failures,mode)
    
    """
    Function: __init__
    This function is the constructor of the simulator object.
    Arguments:
     - max_limit -       This is the maximum number of test_runs to analyze
     - omniscient -     This indicates whether failures outside the running set
                         should be considered or ignored (True - Considered/ 
                         False - Ignored)
     - learning_set -    This is the number of entries to use as a training set
                         before attempting to predict failures.
     - test_edit_factor -This activates the revision of test file editions to-
                         determine if a file should be run or not.
    """
    def __init__(self,max_limit=5000,learning_set = 2000, do_logging = True,
                 omniscient = False):
        self.max_limit = max_limit
        self.learning_set = learning_set
        self.omniscient = omniscient 
        
        #TODO the custom logging functions are not properly set yet
        logging.addLevelName(self.WA_DEBUG,'WA_DEBUG')
        logging.addLevelName(self.ED_DEBUG,'ED_DEBUG')
        logging.addLevelName(self.DEEP_DEBUG,'DEEP_DEBUG')
        
        logger = logging.getLogger('simulation')
        logger.setLevel(logging.DEBUG)
        self.logger = logger
        sim_id = random.randrange(1000)
        
        if logger.handlers == []:
            fh = logging.FileHandler('logs/simulation_20140507.txt')
            fh.setLevel(logging.DEBUG)
            
            ff = logging.Formatter('%(asctime)s - %(funcName)s - ID'+str(sim_id)+' - %(message)s')
            cf = logging.Formatter('%(asctime)s - %(message)s')
            fh.setFormatter(ff)
            ch = logging.StreamHandler()
            ch.setLevel(logging.INFO)
            ch.setFormatter(cf)
            logger.addHandler(ch)
            logger.addHandler(fh)
        if not do_logging:
            logger.setLevel(logging.CRITICAL)
            for hdlr in logger.handlers:
                logger.removeHandler(hdlr)
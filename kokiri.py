# -*- coding: utf-8 -*-
"""
Created on Sat Jul 19 11:32:19 2014

@author: pablo
"""

import name_extractor as ne
import read_history as rh
import random
import logging
import math
import heapq

class kokiri:
    test_info = dict()
    runs = dict()
    events_dict = dict()
    file_changes = None
    prev_change = None
    logger = None
    fail_per_testrun = dict()
    file_info = dict()
    
    
    class Mode():
        standard = 'standard'
        platform = 'platform'
        branch = 'branch'
        mixed = 'mixed'
    
    mode = Mode.mixed
    
    TIMESTAMP = 0
    RUN_ID = 1
    BUILD_ID = 2
    NEXT_FILE_CHG = 3
    BRANCH = 7
    PLATFORM = 9
    TYP = 10
    FAILS = 11
    """
    Function: get_last_run
    This function is in charge of returning the last test_run that concerns us,
    according to the Mode. If the mode is Platform, we return the last run on 
    the same Platform, and so on  for branch and Branch/Platform mix.
    """
    def _get_last_run(self,mode,test_run):
        if mode == self.Mode.standard and 'standard' in self.runs:
            return self.runs['standard']
        if mode == self.Mode.branch and test_run[self.BRANCH] in self.runs:
            return self.runs[test_run[self.BRANCH]]
        if mode == self.Mode.platform and test_run[self.PLATFORM] in self.runs:
            return self.runs[test_run[self.PLATFORM]]
        if mode == self.Mode.mixed and test_run[self.BRANCH]+' '+test_run[self.PLATFORM] in self.runs:
            return self.runs[test_run[self.BRANCH]+' '+test_run[self.PLATFORM]]
        
        return None
    
    """
    Function: get_fails
    This function returns a list of failures occurred in test_run
    """
    def _get_fails(self,test_run):
        if test_run is not None and int(test_run[self.RUN_ID]) in self.fail_per_testrun:
            return self.fail_per_testrun[int(test_run[self.RUN_ID])]
        return list()    
    
    """
    Function: update_last_run
    This function simply updates the recently made run as the last run on the
    corresponding branch, platform, and mix
    """
    def _update_last_run(self,test_run):
        # Recording this as the last test run in the corresponding categories
        self.runs[test_run[self.BRANCH]+' '+test_run[self.PLATFORM]] = test_run
        self.runs['standard'] = test_run
        self.runs[test_run[self.BRANCH]] = test_run
        self.runs[test_run[self.PLATFORM]] = test_run
        
    """
    Function: get_events(start_run,end_run)
    This function returns the events that occurred from start_run until end_run
    the events are of three types:
        - test_failures
        - file_changes
        - test_file_changes NOT COLLECTING YET
    """
    def _get_events(self,start_run,end_run,mode):
        FC_TEST_RUN = 0
        #TEST_RUN BRANCH - 1
        #TEST_RUN PLATFORM - 2
        #SOURCESTAMP ID - 3
        FC_FILENAME = 4
        FC_ACTION = 5
        
        assert start_run is None or int(start_run[self.TIMESTAMP])<int(end_run[self.TIMESTAMP])

        events = dict()
        events['recent_failures'] = self._get_fails(start_run)

        events['file_changes'] = dict()
        
        if (self.prev_change is not None and 
                self.prev_change[FC_TEST_RUN] != end_run[self.RUN_ID]):
            return events
            
        if self.prev_change is not None:
            events['file_changes'][self.prev_change[FC_FILENAME]] = 1
        self.prev_change = None
            
        for f in self.file_changes:
            if int(f[FC_TEST_RUN]) < int(end_run[self.RUN_ID]):
                continue
            
            if f[FC_TEST_RUN] != end_run[self.RUN_ID]:
                self.prev_change = f
                break
            
            if f[FC_FILENAME] not in events['file_changes']:
                events['file_changes'][f[FC_FILENAME]] = 0
            events['file_changes'][f[FC_FILENAME]] += 1
        
        self.logger.debug('Events - FCH: '+str(len(events['file_changes']))+
                            ' | FLS: '+ str(len(events['recent_failures'])))
            
        return events
    
    
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
    def _get_correlation(self,test_failures,event_haps, correlated_haps):
        corr = correlated_haps/event_haps
        return -corr
        # IMPORTANT - We return the NEGATIVE correlation because heapq 
        # gives high priority to lower values
    """
    Function: calculate_relevance
    This function calculates the relevance of a test by adding up the historical 
    correlations between the recent events and the test that is going to be run
    """
    def _calculate_relevance(self,test_name,events):
        recent_fails = events['recent_failures']
        file_changes = events['file_changes']
        relevance = 0.0
        
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
                relevance+= self._get_correlation(
                                    self.test_info[test_name]['failures'],
                                    self.file_info[filename],
                                    self.test_info[test_name]['file_events'][filename])
                                
        # We check that it's more than 1 since correlation func is numerically unstable
        if test_name in recent_fails and self.test_info[test_name]['failures'] > 1:
            relevance += self._get_correlation(
                                self.test_info[test_name]['failures'],
                                self.test_info[test_name]['failures']-1,
                                self.test_info[test_name]['test_events'])
        if 'fails_per_100' in self.test_info[test_name]:
            relevance -= self.test_info[test_name]['fails_per_100']/100

        return relevance
    
    """
    Function: configure_priority_queue
    This function is in charge of calculating relevancies for tests, and 
    building the priority queue to determine which tests will run.
    """
    def _configure_priority_queue(self,events,input_test_list):
        TST_NAME = 1 # This is the index of TST NAME in the priority queues
        pr_q = list() # Here is the priority queue
        zero_list = list()
        zeroes = 0
        for test_name in self.test_info:
            if test_name not in input_test_list:
                self.logger.debug('NOT IN INPUT TEST LIST')
                continue
            relv = self._calculate_relevance(test_name,events)
            if relv != 0.0:
                heapq.heappush(pr_q,(relv,test_name))
            else:
                zeroes +=1
                zero_list.append((0.0,test_name))
        pr_q = sorted(pr_q,key = lambda elem: elem[0])
        
        random.shuffle(zero_list)
        
        return pr_q+zero_list
    
    """
    Function: update_results
    This function is in charge of absorbing the training information, to be used
    when implementing predictions. It must be called after each test_run.
    """
    def update_results(self,fails,test_run):
        self._update_test_list(fails)
        if test_run[self.RUN_ID] in self.events_dict:
            events = self.events_dict[test_run[self.RUN_ID]]
            del self.events_dict[test_run[self.RUN_ID]]
        else:
            last_run = self._get_last_run(self.mode,test_run)
            events = self._get_events(last_run,test_run,self.mode)
        
        count = int(test_run[self.RUN_ID])
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
#            if self.test_info[failed_test]['failures'] >= 10.0:
#                self.recalibrare_failure_rates(self.test_info[failed_test])
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
            #multiplier = len(events['file_changes'])
            multiplier = 1
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
        self.fail_per_testrun[int(test_run[self.RUN_ID])] = fails    
    
    """
    Function: update_test_list
    This function is in palce to make sure that all tests in the input list
    are in the test_info dictionary with the information about said tests.
    """
    def _update_test_list(self,test_list):
        for tname in test_list:
            if tname not in self.test_info:
                self.test_info[tname] = dict()
                # SHOULD WE RISE THE RELEVANCE OF THIS TEST?
                
    def _make_running_set(self,running_set,pr_queue):
        if running_set < 1.0: # If running set is < 1, then it's a percentage; else it's an exact number
            running_set = math.ceil(len(pr_queue)*running_set)
        
        running_set = int(running_set)
        
        rset = list()
        for i in range(running_set):
            rset.append(pr_queue[i][1])
        return rset
    
    """
    Function: load_status
    This function loads the initial state
    In a REAL SETTING, this function must read up to the previous test run.
    """
    def _load_status(self):
#        if len(self.test_info) == 0:
#            ne.get_all_test_names(self.test_info)
        if self.file_changes is None:
            self.file_changes = rh.load_file_changes()
            
    def choose_running_set(self,test_list,running_set,test_run,
                           training=False):
        self.logger.info('TR: '+test_run[self.RUN_ID]+
                        ' Lst: '+str(len(test_list))+
                        ' RS: '+str(running_set))
                        
        self._update_test_list(test_list)

        last_run = self._get_last_run(self.mode,test_run)
        if last_run is None:
            # If we couldn't decide on a last_run, then we don't know any
            # previous information, and thus can't do any predictions
            # we set this run as the latest one, and will use its information
            self._update_last_run(test_run)
        
        events = self._get_events(last_run,test_run,self.mode)
        self.events_dict[test_run[self.RUN_ID]] = events
        
        if training:
            return test_list
        
        pr_queue = self._configure_priority_queue(events,test_list)
        
        return self._make_running_set(running_set,pr_queue)
        
    def _configure_logging(self,log_events):
        logger = logging.getLogger('simulation')
        logger.setLevel(logging.INFO)
        self.logger = logger
        sim_id = random.randrange(1000)
        if logger.handlers == []:
            a = 1
            fh = logging.FileHandler('logs/simulation_20140507.txt')
            fh.setLevel(logging.DEBUG)
            ff = logging.Formatter('%(asctime)s - %(funcName)s - ID'+str(sim_id)+' - %(message)s')
            fh.setFormatter(ff)
            
            logger.addHandler(fh)
            
            ch = logging.StreamHandler()
            ch.setLevel(logging.INFO)
            cf = logging.Formatter('%(asctime)s - %(message)s')
            ch.setFormatter(cf)
            
            logger.addHandler(ch)
        if not log_events:
            logger.setLevel(logging.CRITICAL)
            for hdlr in logger.handlers:
                logger.removeHandler(hdlr)
        
    def __init__(self,log_events=True,mode=Mode.mixed):
        self._configure_logging(log_events)
        self._load_status()
        self.mode = mode
        random.seed(1)
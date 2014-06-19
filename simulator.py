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
import math
import name_extractor as ne
import read_history as rh
import heapq
import simulation_result
import random

import ipdb

class simulator:
    """============================================================="""
    """===================== IMPORTANT CONSTANTS ==================="""
    """============================================================="""
    TIMESTAMP = 0
    RUN_ID = 1
    BRANCH = 7
    PLATFORM = 9
    TYP = 10
    FAILS = 11
    
    """ALPHA IS THE RATE OF WEIGHTED AVERAGE"""
    alpha = 0.90
    """DR IS THE DECAY RATE FOR THE EXPONENTIAL DECAY ALGORITHM"""
    dr = 10.0
    
    max_limit=5000
    full_simulation=True
    metric='exp_decay'
    learning_set = 2000
    
    """ If the running set is not full, run more tests at random    """
    randomize = False
    
    
    """ The time_factor determines whether the time-since-last run  """
    """ should affect the relevancy of a test or not """
    time_factor = False
    RUN_MULTIPLIER = 0.033
    
    """ The test_edit_factor determines whether editions made to   """
    """ test files should affect the relevancy of a test or not    """
    test_edit_factor = False
    
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
    
    calculate_metric = None
    test_info = dict()
    fail_per_testrun = dict()
    
    """
    Function: cleanup
    This function is in charge of resetting the simulator to its state before
    running any simulations. It makes sure to 
    """
    def cleanup(self):
        for test_name in self.test_info:
            if self.metric in self.test_info[test_name]:
                self.test_info[test_name].pop(self.metric)
            if 'passed_editions' in self.test_info[test_name]:
                for branch in self.test_info[test_name]['passed_editions']:
                    extra = list()
                    if branch in self.test_info[test_name]['editions']:
                        extra = self.test_info[test_name]['editions'][branch]
                    self.test_info[test_name]['editions'][branch] = \
                        self.test_info[test_name]['passed_editions'][branch]+extra
                del self.test_info[test_name]['passed_editions']
    

    def calculate_exp_decay(self,test_name, test_info, fail,branch,platform, \
                            ran, editions):
        logger = logging.getLogger('simulation')
        if fail < 0 or fail > 1:
            logger.warning('FAIL input is inappropriate')
            return
        
        if editions > 0:
            fail = 1
        if 'exp_decay' not in  test_info[test_name]:
            test_info[test_name]['exp_decay'] = dict()
            
        if 'standard' not in test_info[test_name]['exp_decay'] and fail == 1:
            test_info[test_name]['exp_decay']['standard'] = 0.0
        if platform not in test_info[test_name]['exp_decay']  and fail == 1:            
            test_info[test_name]['exp_decay'][platform] = 0.0
        if branch not in test_info[test_name]['exp_decay'] and fail == 1:          
            test_info[test_name]['exp_decay'][branch] = 0.0
        if branch+' '+platform not in test_info[test_name]['exp_decay'] and fail == 1:           
            test_info[test_name]['exp_decay'][branch+' '+platform] = 0.0
        
        if fail == 0 and not ran and self.time_factor:
            fail = self.RUN_MULTIPLIER
            
        for key in [branch,platform,branch+' '+platform, 'standard']:
            if key in test_info[test_name]['exp_decay']:
                test_info[test_name]['exp_decay'][key] = \
                    test_info[test_name]['exp_decay'][key]/math.exp(1/self.dr)+fail
                   
        if 'standard' in test_info[test_name] and test_info[test_name]['exp_decay']['standard'] > 0:
            pref = 'FAIL' if fail == 1 else 'PASS'
            level = self.ED_DEBUG if fail == 1 else self.DEEP_DEBUG
            logger.log(level, pref+' '+test_name +\
                ' ed_ind: '+str(test_info[test_name]['exp_decay']))
    

    def calculate_weighted_avg(self,test_name,test_info,fail,branch,platform,\
                                ran,editions):
        logger = logging.getLogger('simulation')
        
        if fail < 0 or fail > 1:
            logger.warning('FAIL input is inappropriate')
            return
            
        if editions > 0:
            fail = 1
            
        if 'weighted_avg' not in test_info[test_name]:
            test_info[test_name]['weighted_avg'] = dict()
            
        if 'standard' not in test_info[test_name]['weighted_avg'] and fail == 1:
            test_info[test_name]['weighted_avg']['standard'] = 0.0
    
        if branch not in test_info[test_name]['weighted_avg'] and fail == 1:
            test_info[test_name]['weighted_avg'][branch] = 0.0
        if platform not in test_info[test_name]['weighted_avg'] and fail == 1:
            test_info[test_name]['weighted_avg'][platform] = 0.0
        if branch+' '+platform not in test_info[test_name]['weighted_avg'] and fail == 1:
            test_info[test_name]['weighted_avg'][branch+' '+platform] = 0.0
            
        if fail == 0 and not ran and self.time_factor:
            fail = self.RUN_MULTIPLIER
            
        for key in [branch,platform,branch+' '+platform, 'standard']:
            if key in test_info[test_name]['weighted_avg']:
                test_info[test_name]['weighted_avg'][key] = (1-self.alpha)*fail + \
                    test_info[test_name]['weighted_avg'][key]*self.alpha
        
        if 'standard' in test_info[test_name] and test_info[test_name]['weighted_avg']['standard'] != 0:
            pref = 'FAIL' if fail == 1 else 'PASS'
            level = self.WA_DEBUG if fail == 1 else self.DEEP_DEBUG
            logger.log(level,pref+' '+test_name +\
                ' wa_ind: '+str(test_info[test_name]['weighted_avg']))

    def add_to_pr_queue(self,test_info, test_name, pq,platform,branch):
        heapq.heappush(pq['standard'],\
            (-test_info[test_name][self.metric]['standard'],test_name)\
            )
        if platform in test_info[test_name][self.metric]:
            heapq.heappush(pq[platform],\
                (-test_info[test_name][self.metric][platform],test_name)\
                )
        if branch in test_info[test_name][self.metric]:
            heapq.heappush(pq[branch],\
                (-test_info[test_name][self.metric][branch],test_name)\
                )
        if branch+' '+platform in test_info[test_name][self.metric]:
            heapq.heappush(pq[branch+' '+platform],\
                (-test_info[test_name][self.metric][branch+' '+platform],test_name)\
                )
                
    """
    Function: build_old_pr_queues
    This function is in charge of building the priority queues for branch, platform
    and the mixed priority queue if they have never before been built.
    """
    def build_old_pr_queues(self,needed_queues,old_qs,test_info,branch,plat):
        logger = logging.getLogger('simulation')
        logger.debug('build_old_pr_queues was called on: '+str(needed_queues.keys()))
        for nm in needed_queues:
            old_qs[nm] = list()
        for test_name in test_info:
            if 'standard' in needed_queues and 'standard' in test_info[test_name][self.metric]:
                heapq.heappush(old_qs['standard'],\
                        (-test_info[test_name][self.metric]['standard'],test_name))
            if 'branch' in needed_queues and branch in test_info[test_name][self.metric]:
                heapq.heappush(old_qs['branch'],\
                        (-test_info[test_name][self.metric][branch],test_name))
            if 'platform' in needed_queues and plat in test_info[test_name][self.metric]:
                heapq.heappush(old_qs['platform'],\
                        (-test_info[test_name][self.metric][plat],test_name))
            if 'mixed' in needed_queues and branch+' '+plat in test_info[test_name][self.metric]:
                heapq.heappush(old_qs['mixed'],\
                        (-test_info[test_name][self.metric][branch+' '+plat],test_name))
                
    class Mode():
        standard = 'standard'
        platform = 'platform'
        branch = 'branch'
        mixed = 'mixed'
    """
    Function: assign_pq
    This function returns the most interesting priority queue according to the
    mode of the analysis.
    """
    def assign_pq(self, pq,mode,branch,platform):
        if mode == self.Mode.standard:
            return pq['standard']
        if mode == self.Mode.platform:
            return pq[platform]
        if mode == self.Mode.branch:
            return pq[branch]
        if mode == self.Mode.mixed:
            return pq[branch+' '+platform]
            
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
                rh.load_failures(self.test_info, self.fail_per_testrun,\
                                failures_file=fails_file)
        """
        Now we get the history of test_file editions
        """
        if self.test_edit_factor:
            rh.get_test_file_change_history(test_info=self.test_info)
    
    
    """
    Function prepare_result
    This function prepares and outputs the result object of a simulation
    """
    def prepare_result(self,pos_dist,missed_fails,caught_fails,mode,run_tests):
        res = simulation_result.simulation_result()
        res.training_set = self.learning_set
        
        res.test_runs=self.max_limit
        res.full_simulation=self.full_simulation
        res.metric=self.metric
        res.caught_failures = caught_fails
        res.missed_failures = missed_fails
        res.pos_distribution = pos_dist
        res.mode = mode
        res.run_tests = run_tests        
        
        return res
    
    """
    Function: rearrange_queues
    This function is ran at the beginning of each new test_run iteration. It
    does the following:
        - Find the list of queues that are necessary to build for the
            iteration, and adds them to needed_queues
        - Sorts and takes the priority queues that we'll use in this iteration,
            it puts them all in old_qs
        - If there are queues that we need to assemble, it calls build_old_pr_queues,
            to make sure they are assembled
        - Finally, resets the queues in pq that we will reassemble in this 
            iteration
    """
    def rearrange_queues(self,needed_queues,old_qs,pq,test_run):
        if 'standard' in pq:
            #We need to sort pq['standard'] because it's a heap, so it 
            #will not be in perfect linear order
            old_qs['standard'] = sorted(pq['standard'],key = lambda elem: elem[0])
        else:
            needed_queues['standard'] = True
        if test_run[self.PLATFORM] in pq:
            old_qs['platform'] = sorted(pq[test_run[self.PLATFORM]],key = lambda elem: elem[0])
        else:
            needed_queues['platform'] = True
        if test_run[self.BRANCH] in pq:
            old_qs['branch']= sorted(pq[test_run[self.BRANCH]],key = lambda elem: elem[0])
        else:
            needed_queues['branch'] = True
        if test_run[self.BRANCH]+' '+test_run[self.PLATFORM] in pq:
            old_qs['mixed'] = sorted(pq[test_run[self.BRANCH]+' '+test_run[self.PLATFORM]],\
                        key = lambda elem: elem[0])
        else:
            needed_queues['mixed'] = True
        
        if len(needed_queues) > 0:
                    self.build_old_pr_queues(needed_queues,old_qs,self.test_info,\
                                        test_run[self.BRANCH],test_run[self.PLATFORM])
        """
        After the old_pr_queues have been built, we reset the priority 
        queues for the new iteration
        """
        pq[test_run[self.PLATFORM]] = list()
        pq[test_run[self.BRANCH]] = list()
        pq[test_run[self.BRANCH]+' '+test_run[self.PLATFORM]] = list()
        pq['standard'] = list()

    """
    Function: get_number_of_editions
    This function calculates and returns the number of times a file has been
    edited
    """
    def get_number_of_editions(self,test_run,test_name):
        num_editions = 0
        TIMESTAMP = 0
        if 'editions' not in self.test_info[test_name]:
            return 0
        if test_run[self.BRANCH] not in self.test_info[test_name]['editions']:
            return 0
        try:
            for elm in self.test_info[test_name]['editions'][test_run[self.BRANCH]]:
                if int(elm[TIMESTAMP]) > int(test_run[self.TIMESTAMP]):
                    break
                num_editions += 1
                if 'passed_editions' not in self.test_info[test_name]:
                    self.test_info[test_name]['passed_editions'] = dict()
                if test_run[self.BRANCH] not in self.test_info[test_name]['passed_editions']:
                    self.test_info[test_name]['passed_editions'][test_run[self.BRANCH]] = list()
                self.test_info[test_name]['passed_editions'][test_run[self.BRANCH]].append(elm)
        except:
            ipdb.set_trace()
        self.test_info[test_name]['editions'][test_run[self.BRANCH]] = \
            self.test_info[test_name]['editions'][test_run[self.BRANCH]][num_editions:]
        if len(self.test_info[test_name]['editions'][test_run[self.BRANCH]]) == 0:
            del self.test_info[test_name]['editions'][test_run[self.BRANCH]]
        return num_editions
        
    """
    Function: relevant_queue
    This function returns the relevant queue, where we want to get the jobs from
    in this test run.
    """
    def relevant_queue(self,mode,old_qs):
        if mode == self.Mode.standard:
            return old_qs['standard']
        if mode == self.Mode.branch:
            return old_qs['branch']
        if mode == self.Mode.platform:
            return old_qs['platform']
        if mode == self.Mode.mixed:
            return old_qs['mixed']

    """
    Function: calculate_first_time_and_ind
    The following code finds the position of the test in the 
    corresponding priority queue, according to the mode that
    we are running.
    """
    def calculate_ind(self,queue,mode,test_run,test_name):
        ind = -1
        tag = None
        if mode == self.Mode.standard:
            tag = 'standard'
        elif mode == self.Mode.branch:
            tag = test_run[self.BRANCH]
        elif mode == self.Mode.platform:
            tag = test_run[self.PLATFORM]
        elif mode == self.Mode.mixed:
            tag = test_run[self.BRANCH]+' '+test_run[self.PLATFORM]
            
            
        if tag in self.test_info[test_name][self.metric] and\
            self.test_info[test_name][self.metric][tag] > 0.0:
            ind = queue.index(\
                (-self.test_info[test_name][self.metric][tag],test_name))
        return ind
        
    """
    Function: get_next_test_run
    This function returns the next test_run element on the same branch
    """
    def get_next_test_run(self,test_run,test_hist):
        for t_run in test_hist:
            if t_run == test_run: #Skip the first one
                continue
            if test_run[self.BRANCH] == t_run[self.BRANCH]:
                return t_run
        return None
    
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
    Function: can_be_added_to_pq
    This function returns True if a test can be properly added to the priority
    queues (this is determined by checking if it has a relevancy quotient)
    """
    def can_be_added_to_pq(self,test):
        tag = 'standard'            
        if self.metric in test and tag in test[self.metric]:
            return True
        return False

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
    def run_simulation(self, running_set, mode=Mode.standard):
        #ipdb.set_trace()
        logger = logging.getLogger('simulation')
        test_hist = rh.open_test_history()
        count = 0
        missed_failures = 0 # These are failures that would have been caught if the test had run
        caught_failures = 0 # These are failures that are caught - because the test ran
        simulating = False # This parameter is turned to true after the learning round
        pq = dict() # We keep a dict of priority queues
        pos_dist = numpy.zeros(dtype=int,shape=1000) # Distribution of positions of tests
        run_tests = 0 # This is to calculate the number of tests ran during simulation mode
        
        logger.info('Simulating. RS: '+str(running_set)+' Mode: '+mode+' Full sim: '+str(self.full_simulation))
            
        """
        test_hist is the list from the query of test_run history. It returns 
        one-by-one the test_runs.
        In the following loop, we iterate over each test run, from the first to
        the last
        """
        for tr_index,test_run in enumerate(test_hist):
            tests_run_now = 0
            if count == self.learning_set:
                # First self.learning_set iterations are the learning set. 
                # After that, the simulation starts.
                simulating = True
                logger.debug("==================================================")
                logger.debug("==============SIMULATION HAS BEGUN================")
                logger.debug("==================================================\n\n")
            count=count+1
            
            if count > self.max_limit:
                break # If we have iterated the max_limit of test_runs, we break out
            
            next_run = None
            if self.test_edit_factor:
                next_run = self.get_next_test_run(test_run,test_hist[tr_index:])
            
            old_qs = dict()
            randomized_tests = 0 # The number of tests in the tail that we will run
            
            if simulating: #Only if we are simulating do we need a pr_queue
                """
                Priority queues are built every iteration, listing the tests by
                relevancy.
                At any given time, 4 queues are being used or re built: 
                 - The standard queue, 
                 - The queue per-platform, 
                 - The queue per-branch, and
                 - The mixed per-branch/platform queue.advanced_simulator-corr
                The priority queues are in the  pq  dictionary.
                
                Since the queues are only built in simulation-mode, the 
                following code identifies the priority queues that have not been
                built yet and thus we need to build before we go ahead with the 
                simulation.
                """
                needed_queues = dict()
                self.rearrange_queues(needed_queues,old_qs,pq,test_run)
                
                if self.randomize and len(self.relevant_queue(mode,old_qs)) < running_set:
                    randomized_tests = running_set - len(self.relevant_queue(mode,old_qs))
                    logger.debug('Rand.tests: ' + str(randomized_tests)+' | Len queue: '+\
                                str(len(self.relevant_queue(mode,old_qs))))
                    run_tests += len(self.relevant_queue(mode,old_qs))
                    tests_run_now = len(self.relevant_queue(mode,old_qs))
                else:
                    run_tests += running_set
                    tests_run_now = running_set
                                
            if int(test_run[self.RUN_ID]) in self.fail_per_testrun:
                logger.debug('Test run #'+test_run[self.RUN_ID]+' had '+ \
                    str(len(self.fail_per_testrun[int(test_run[self.RUN_ID])])) +\
                    ' failures')
                fails = self.fail_per_testrun[int(test_run[self.RUN_ID])]
            else:
                logger.debug('Test run #'+str(test_run[self.RUN_ID])+' had no failures')
                fails = list()
            """
            fails is a list of all the tests that failed in this test_run. Empty
            if no tests failed in this test run.
            """

            for test_ind,test_name in enumerate(self.test_info):
                fail = int(test_name in fails) #1 if the test failed, 0 if it did not
                ind = -1 # This is the index of the test in the priority queue (-1 if not part of it)
                
                if simulating and fail == 1:
                    """
                    This code runs for tests that would fail if they run, and if
                    they don't run, should be recorded as a missed failure.
                    
                    The position is accumulated on the pos_dist array, which
                    contains the distribution of the positions of tests.
                    """
                    ind = self.calculate_ind(self.relevant_queue(mode,old_qs),\
                                            mode,test_run,test_name)
                    self.add_to_pos_dis_array(pos_dist,ind)
                    
                """
                If the test doesn't have a relevancy score, and we have enough
                space to run extra tests, we'll select a few tests randomly
                and run them. 
                The strategy to select the tests seems not 100%
                uniform, but good enough:
                http://stackoverflow.com/a/48089/1255356
                """
                if self.randomize and ind == -1 and randomized_tests > 0:
                    prob = (randomized_tests+0.0)/(len(self.test_info)-test_ind)
                    if random.random() <= prob:
                        ind = 1
                        run_tests += 1
                        tests_run_now += 1
                        randomized_tests -= 1
                        
                if simulating and fail == 1:
                    """
                    Conditions to MISS a failure:
                    1. We are running a full simulation
                    2. The test will fail if it runs
                    3. The test is NOT inside the running set (this it does not run):
                        - Its position in the priority queue is beyond the running set OR
                        - It is not in the priority queue (not competing for resources)
                    """
                    if self.full_simulation and fail == 1 and \
                        (ind < 0 or ind > running_set):
                        fail = 0
                        missed_failures += 1
                    
                    caught_failures += fail

                
                # If we are simulating, and the test is not inside the 
                # learning_set, we consider it as NOT RUNNING. Otherwise, we 
                # consider it as running
                ran = True
                if simulating and (ind > self.learning_set or ind < 0):
                    ran = False
                
                if simulating and ran:
                    run_tests += 1
                
                # This code runs only for simulations with test_edit_factor
                editions = 0
                if self.test_edit_factor and next_run is not None:
                    editions = self.get_number_of_editions(next_run,test_name)
                
                # Calculate the metric for this test
                self.calculate_metric[self.metric](test_name,self.test_info,\
                            fail,test_run[self.BRANCH],test_run[self.PLATFORM],\
                            ran,editions)
                
                # Add the test to the priority queue if we are in simulation mode,
                # and the test has failed at least once
                if simulating and self.can_be_added_to_pq(self.test_info[test_name]):
                    self.add_to_pr_queue(self.test_info,test_name,pq,\
                                        test_run[self.PLATFORM],test_run[self.BRANCH])

            # Do logging after each iteration in simulation mode
            if simulating:
                #q = self.assign_pq(pq,mode,test_run[self.BRANCH],test_run[self.PLATFORM])
                #logger.debug('PR_QUEUE: '+str(heapq.nsmallest(5,q)))
                logger.debug('TESTS_RUN: '+str(tests_run_now))
                logger.debug('BR: '+test_run[self.BRANCH]+' | PL: '+\
                             test_run[self.PLATFORM]+'\n')
        
        """
        END OF THE SIMULATION - Final logging
        """
        logger.info('MF: '+str(missed_failures)+' | CF: '+str(caught_failures)+\
                    ' | TF: '+str(missed_failures+caught_failures) +\
                    ' | RECALL: '+str(caught_failures/(missed_failures+caught_failures+0.0))+\
                    ' | TESTS_RUN: ' + str(run_tests))
                    
        return self.prepare_result(pos_dist,missed_failures,caught_failures,mode,run_tests)
    
    """
    Function: __init__
    This function is the constructor of the simulator object.
    Arguments:
     - max_limit -       This is the maximum number of test_runs to analyze
     - full_simulation - This indicates whether failures outside the running set
                         should be considered or ignored (True - Ignored/ 
                         False - Considered)
     - metric -          This is the metric to use when calculating the 
                         relevancy of a test
     - learning_set -    This is the number of entries to use as a training set
                         before attempting to predict failures.
     - test_edit_factor -This activates the revision of test file editions to-
                         determine if a file should be run or not.
    """
    def __init__(self,max_limit=5000,full_simulation=True,metric='exp_decay', \
                learning_set = 2000,time_factor=False,test_edit_factor=False,\
                do_logging = False, randomize_tail = False):
        self.max_limit = max_limit
        self.full_simulation = full_simulation       
        self.metric = metric
        self.learning_set = learning_set
        self.time_factor = time_factor
        self.test_edit_factor = test_edit_factor
        self.randomize = randomize_tail
        if randomize_tail:
            random.seed(1)
        
        #TODO the custom logging functions are not properly set yet
        logging.addLevelName(self.WA_DEBUG,'WA_DEBUG')
        logging.addLevelName(self.ED_DEBUG,'ED_DEBUG')
        logging.addLevelName(self.DEEP_DEBUG,'DEEP_DEBUG')
        
        logger = logging.getLogger('simulation')
        logger.setLevel(logging.DEBUG)
        
        if logger.handlers == []:
            fh = logging.FileHandler('logs/simulation_20140507.txt')
            fh.setLevel(logging.DEBUG)
            
            ff = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
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
        
        self.calculate_metric = dict()
        self.calculate_metric['exp_decay'] = self.calculate_exp_decay
        self.calculate_metric['weighted_avg'] = self.calculate_weighted_avg
        
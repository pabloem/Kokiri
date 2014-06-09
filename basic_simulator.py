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
    
    
    """ The time_factor determines whether the time-since-last run  """
    """ should affect the relevancy of a test or not """
    time_factor = False
    
    """ The test_edit_factor determines whether editions made to   """
    """ test files should affect the relevancy of a test or not    """
    test_edit_factor = False
    
    RUN_MULTIPLIER = 0.033
    
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
    
    calculate_metric = dict()
    test_info = dict()
    fail_per_testrun = dict()
    test_f_changes = list()
    

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
            self.test_f_changes = \
                rh.get_test_file_change_history(test_info=self.test_info)
    
    
    """
    Function prepare_result
    This function prepares and outputs the result object of a simulation
    """
    def prepare_result(self,pos_dist,missed_fails,caught_fails,mode):
        res = simulation_result.simulation_result()
        res.training_set = self.learning_set
        
        res.test_runs=self.max_limit
        res.full_simulation=self.full_simulation
        res.metric=self.metric
        res.caught_failures = caught_fails
        res.missed_failures = missed_fails
        res.pos_distribution = pos_dist
        res.mode = mode
        
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
        logger = logging.getLogger('simulation')
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
        except:
            ipdb.set_trace()
        self.test_info[test_name]['editions'][test_run[self.BRANCH]] = \
            self.test_info[test_name]['editions'][test_run[self.BRANCH]][num_editions:]
        if len(self.test_info[test_name]['editions'][test_run[self.BRANCH]]) == 0:
            del self.test_info[test_name]['editions'][test_run[self.BRANCH]]
        return num_editions

    """
    Function: calculate_first_time_and_ind
    This function retrieves the index of a test in a priority queue and whether
    it is the first time that a failure is encountered on this test
    """
    def calculate_first_time_and_ind(self,old_qs,mode,test_run,test_name):
        logger = logging.getLogger('simulation')
        ind = -1
        first_time = False
        if mode == self.Mode.standard:
            if 'standard' in self.test_info[test_name][self.metric]:
                ind = old_qs['standard'].index((-self.test_info[test_name][self.metric]['standard'],test_name))
            else:
                first_time = True
        elif mode == self.Mode.branch:
            if test_run[self.BRANCH] in self.test_info[test_name][self.metric] and\
               self.test_info[test_name][self.metric][test_run[self.BRANCH]] > 0.0:
                ind = old_qs['branch'].index(\
                    (-self.test_info[test_name][self.metric][test_run[self.BRANCH]],\
                    test_name))
            else:
                first_time = True
                logger.debug('First recorded failure of '+test_name)
        elif mode == self.Mode.platform:
            if test_run[self.PLATFORM] in self.test_info[test_name][self.metric] and\
                self.test_info[test_name][self.metric][test_run[self.PLATFORM]] > 0.0:
                ind = old_qs['platform'].index(\
                    (-self.test_info[test_name][self.metric][test_run[self.PLATFORM]],\
                    test_name))
            else:
                first_time = True
        elif mode == self.Mode.mixed:
            if test_run[self.BRANCH]+' '+test_run[self.PLATFORM] in self.test_info[test_name][self.metric] and\
                self.test_info[test_name][self.metric][test_run[self.BRANCH]+' '+test_run[self.PLATFORM]] > 0.0:
                ind = old_qs['mixed'].index(\
                    (-self.test_info[test_name][self.metric][test_run[self.BRANCH]+' '+test_run[self.PLATFORM]],\
                    test_name))
            else:
                first_time = True
        return ind,first_time
        
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
        missed_failures = 0
        caught_failures = 0
        simulating = False # This parameter is turned to true after the learning round
        pq = dict() # We keep a dict of priority queues
        pos_dist = numpy.zeros(dtype=int,shape=1000) # Distribution of positions of tests
        
        cheated_info = 0
        logger.info('Simulating. RS: '+str(running_set)+' Mode: '+mode+' Full sim: '+str(self.full_simulation))
        
        """
        test_hist is the file handler from the query of test_run history. It 
        returns one-by-one the test_runs.
        In the following loop, we iterate over each test run, from the first to
        the last
        """
        for tr_index,test_run in enumerate(test_hist):
            if count == self.learning_set:
                # First 2000 iterations are the learning set. After that, the
                # simulation starts.
                simulating = True
                logger.debug("==================================================")
                logger.debug("==============SIMULATION HAS BEGUN================")
                logger.debug("==================================================\n\n")
            count=count+1
            
            if count > self.max_limit:
                break
            if self.test_edit_factor:
                next_run = self.get_next_test_run(test_run,test_hist[tr_index:])
            
            old_qs = dict()
            if simulating: #Only if we are simulating do we need a pr_queue
                """
                Priority queues are built every iteration, listing the tests by
                relevancy.
                At any given time, 4 queues are being used or re built: 
                 - The standard queue, 
                 - The queue per-platform, 
                 - The queue per-branch, and
                 - The mixed per-branch/platform queue.
                The priority queues are in the  pq  dictionary.
                
                Since the queues are only built in simulation-mode, the 
                following code identifies the priority queues that have not been
                built yet and thus we need to build before we go ahead with the 
                simulation.
                """
                needed_queues = dict()
                self.rearrange_queues(needed_queues,old_qs,pq,test_run)
                                
            if int(test_run[self.RUN_ID]) in self.fail_per_testrun:
                logger.debug('Test run #'+test_run[self.RUN_ID]+' had '+ \
                    str(len(self.fail_per_testrun[int(test_run[self.RUN_ID])])) +' failures')
                fails = self.fail_per_testrun[int(test_run[self.RUN_ID])]
            else:
                logger.debug('Test run #'+str(test_run[self.RUN_ID])+' had no failures')
                fails = list()
            """
            fails is a list of all the tests that failed in this test_run. Empty
            if no tests failed in this test run.
            """
            
            found_fails = 0
            for test_name in self.test_info:
                fail = int(test_name in fails) #1 if the test failed, 0 if it did not
                ind = -1
                first_time = False
                
                if fail == 1:
                    found_fails += 1
                #The found_fails variable is used later for data sanity checks
                   
                if simulating and fail == 1:
                    if self.metric not in self.test_info[test_name]:
                        first_time = True
                        logger.debug('Very first recorded failure of '+test_name)
                    """
                    The following code finds the position of the test in the 
                    corresponding priority queue, according to the mode that
                    we are running.
                    The position is accumulated on the pos_dist array, which
                    contains the distribution of the positions of tests
                    """
                    ind, first_time = self.calculate_first_time_and_ind(old_qs,mode,test_run,test_name)
                    
                    if not first_time:
                        if ind >= pos_dist.size:
                            # If we need to increase the size of the pos_dist array, we do
                            # up to the next 100
                            sz = ind+1
                            chg_size = sz if sz % 100 == 0 else sz + 100 - sz % 100
                            prev_size = pos_dist.size
                            pos_dist = numpy.resize(pos_dist,chg_size)
                            pos_dist[prev_size:pos_dist.size] = 0 #Making new elements zero
                        pos_dist[ind] += 1
                        
                    # If the test is not in the running set, the FAILURE is not recognized
                    # and is marked as missed
                    if simulating and self.full_simulation and ind > running_set and fail == 1: 
                        fail = 0
                        missed_failures += 1
                    elif fail == 1:
                        # If the test is in the running set, the FAILURE is recognized and caught
                        caught_failures += 1

                if not simulating or (ind >= 0 and ind < self.learning_set):
                    # If we are not simulating, or the index is inside the 
                    # learning set, we consider the test as run
                    ran = True
                else:
                    # Otherwise, we want to raise the relevancy test for this test
                    ran = False
                
                editions = 0
                if self.test_edit_factor and next_run is not None:
                    editions = self.get_number_of_editions(next_run,test_name)
                
                # Calculate the metric for this test
                self.calculate_metric[self.metric](test_name,self.test_info,\
                            fail,test_run[self.BRANCH],test_run[self.PLATFORM],\
                            ran,editions)
                
                # Add the test to the priority queue if we are in simulation mode
                if simulating and 'standard' in self.test_info[test_name][self.metric]:
                    self.add_to_pr_queue(self.test_info,test_name,pq,\
                                        test_run[self.PLATFORM],test_run[self.BRANCH])
                                        
                # Keeping track of how many times we 'cheat' by considering 
                # a failure that we could not have known about
                if first_time:
                    cheated_info += 1
            
            # Do logging after each iteration
            if simulating and found_fails > 0:
                logger.debug('FAILS FOUND: '+str(found_fails)+' | KNOWN: '+str(len(fails)))
                
                q = self.assign_pq(pq,mode,test_run[self.BRANCH],test_run[self.PLATFORM])
                logger.debug('PR_QUEUE: '+str(heapq.nsmallest(10,q)))
                logger.debug('BR: '+test_run[self.BRANCH]+' | PL: '+test_run[self.PLATFORM])
            if simulating:
                logger.debug('\n')
        logger.info('MF: '+str(missed_failures)+' | CF: '+str(caught_failures)+\
                    ' | TF: '+str(missed_failures+caught_failures) +\
                    ' | CHEAT: '+str(cheated_info))
                    
        return self.prepare_result(pos_dist,missed_failures,caught_failures,mode)
    
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
    """
    def __init__(self,max_limit=5000,full_simulation=True,metric='exp_decay', \
                learning_set = 2000,time_factor=False,test_edit_factor=False):
        self.max_limit = max_limit
        self.full_simulation = full_simulation       
        self.metric = metric
        self.learning_set = learning_set
        self.time_factor = time_factor
        self.test_edit_factor = test_edit_factor
        
        #TODO the custom logging functions are not properly set yet
        logging.addLevelName(self.WA_DEBUG,'WA_DEBUG')
        logging.addLevelName(self.ED_DEBUG,'ED_DEBUG')
        logging.addLevelName(self.DEEP_DEBUG,'DEEP_DEBUG')
        
        logger = logging.getLogger('simulation')
        logger.setLevel(logging.DEBUG)
        fh = logging.FileHandler('logs/simulation_20140507.txt')
        fh.setLevel(logging.DEBUG)
        
        ff = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        cf = logging.Formatter('%(asctime)s - %(message)s')
        fh.setFormatter(ff)
        logger.addHandler(fh)
        ch = logging.StreamHandler()
        ch.setLevel(logging.INFO)
        ch.setFormatter(cf)
        logger.addHandler(ch)
        
        self.calculate_metric = dict()
        self.calculate_metric['exp_decay'] = self.calculate_exp_decay
        self.calculate_metric['weighted_avg'] = self.calculate_weighted_avg
        
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


class simulation_result:
    running_set_size = 0
    missed_failures = 0
    caught_failures = 0
    metric = ''
    learning_set_size = 0
    full_simulation = False
    max_limit = 0
    pos_distribution = None
    mode = ''

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
    

    def calculate_exp_decay(self,test_name, test_info, fail,branch,platform):
        logger = logging.getLogger('simulation')
        
        if fail < 0 or fail > 1:
            logger.warning('FAIL input is inappropriate')
            return
            
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
            
        for key in [branch,platform,branch+' '+platform, 'standard']:
            if key in test_info[test_name]['exp_decay']:
                test_info[test_name]['exp_decay'][key] = \
                    test_info[test_name]['exp_decay'][key]/math.exp(1/self.dr)+fail
                   
        if 'standard' in test_info[test_name] and test_info[test_name]['exp_decay']['standard'] > 0:
            pref = 'FAIL' if fail == 1 else 'PASS'
            level = self.ED_DEBUG if fail == 1 else self.DEEP_DEBUG
            logger.log(level, pref+' '+test_name +\
                ' ed_ind: '+str(test_info[test_name]['exp_decay']))
    

    def calculate_weighted_avg(self,test_name,test_info,fail,branch,platform):
        logger = logging.getLogger('simulation')
        
        if fail < 0 or fail > 1:
            logger.warning('FAIL input is inappropriate')
            return
            
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
    This function initializes all the data that is essential for a simulation, but 
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
    Function prepare_result
    This function prepares and outputs the result object of a simulation
    """
    def prepare_result(self,pos_dist,missed_fails,caught_fails,mode):
        res = simulation_result()
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
    Function: run_simulation
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
        logger = logging.getLogger('simulation')
        test_hist = rh.open_test_history()
        count = 0
        missed_failures = 0
        caught_failures = 0
        simulating = False
        pq = dict()
        positions = list()
        pos_dist = numpy.zeros(dtype=int,shape=1000) # Distribution of positions of tests
        logger.info('Simulating. RS: '+str(running_set)+' Mode: '+mode+' Full sim: '+str(self.full_simulation))
        for test_run in test_hist:
            if count == self.learning_set:
                simulating = True
                logger.debug("==================================================")
                logger.debug("==============SIMULATION HAS BEGUN================")
                logger.debug("==================================================\n\n")
            count=count+1
            
            if count > self.max_limit:
                break
            
            old_qs = dict()
            if simulating: #Only if we are simulating do we need a pr_queue
                needed_queues = dict()
                if 'standard' in pq:
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
                pq[test_run[self.PLATFORM]] = list()
                pq[test_run[self.BRANCH]] = list()
                pq[test_run[self.BRANCH]+' '+test_run[self.PLATFORM]] = list()
                pq['standard'] = list()
                positions = list()
                max_pos = 0
                
            if int(test_run[self.RUN_ID]) in self.fail_per_testrun:
                logger.debug('Test run #'+test_run[self.RUN_ID]+' had '+ \
                    str(len(self.fail_per_testrun[int(test_run[self.RUN_ID])])) +' failures')
                fails = self.fail_per_testrun[int(test_run[self.RUN_ID])]
            else:
                logger.debug('Test run #'+str(test_run[self.RUN_ID])+' had no failures')
                fails = list()
            
            found_fails = 0
            max_pos = 0
            for test_name in self.test_info:
                fail = int(test_name in fails)
                
                if fail == 1: #This is just for data-sanity checks
                    found_fails += 1
                    
                if simulating and self.metric not in self.test_info[test_name] and fail == 1:
                    logger.debug('Very first recorded failure of '+test_name)
                if simulating and fail == 1:
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
                    if not first_time:
                        if ind >= pos_dist.size:
                            chg_size = ind if ind % 100 == 0 else ind + 100 - ind % 100
                            prev_size = pos_dist.size
                            pos_dist = numpy.resize(pos_dist,chg_size)
                            pos_dist[prev_size:pos_dist.size] = 0 #Making new elements zero
                        pos_dist[ind] += 1
                        max_pos = ind if ind > max_pos else max_pos
                        positions.append([test_name,ind])
                    
                    # If the test is not in the running set, the FAILURE is not recognized
                    if simulating and self.full_simulation and ind > running_set and fail == 1: 
                        fail = 0
                        missed_failures += 1
                    elif fail == 1:
                        caught_failures += 1
                self.calculate_metric[self.metric](test_name,self.test_info,fail,test_run[self.BRANCH],test_run[self.PLATFORM])
                if simulating and 'standard' in self.test_info[test_name][self.metric]: #Only if we are simulating do we need a pr_queue
                    self.add_to_pr_queue(self.test_info,test_name,pq,\
                                        test_run[self.PLATFORM],test_run[self.BRANCH])
                    
            if simulating and found_fails > 0:
                logger.debug('MAX pos: '+str(max_pos)+'|===|'+str(len(positions))+ \
                                ' POSITIONS: '+str(positions))
                logger.debug('FAILS FOUND: '+str(found_fails)+' | KNOWN: '+str(len(fails)))
                
                q = self.assign_pq(pq,mode,test_run[self.BRANCH],test_run[self.PLATFORM])
                logger.debug('PR_QUEUE: '+str(heapq.nsmallest(10,q)))
                logger.debug('BR: '+test_run[self.BRANCH]+' | PL: '+test_run[self.PLATFORM])
            if simulating:
                logger.debug('\n')
        logger.info('MF: '+str(missed_failures)+' | CF: '+str(caught_failures)+\
                    ' | TF: '+str(missed_failures+caught_failures))
                    
        return self.prepare_result(pos_dist,missed_failures,caught_failures,mode)
        
    def __init__(self,max_limit=5000,full_simulation=True,metric='exp_decay', learning_set = 2000):
        self.max_limit = max_limit
        self.full_simulation = full_simulation       
        self.metric = metric
        self.learning_set = learning_set
        
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
        
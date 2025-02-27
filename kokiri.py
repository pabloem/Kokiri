# -*- coding: utf-8 -*-
"""
Created on Sat Jul 19 11:32:19 2014

@author: pablo
"""

import ipdb
import random
import logging
import math
import heapq

class kokiri(object):
    test_info = dict()
    logger = None

    upd_count = dict()
    pred_count = dict()
    
    
    class Mode(object):
        standard = 'standard'
        platform = 'platform'
        branch = 'branch'
        mixed = 'mixed'
    
    mode = Mode.standard
    
    TIMESTAMP = 0
    RUN_ID = 1
    BUILD_ID = 2
    NEXT_FILE_CHG = 3
    BRANCH = 7
    PLATFORM = 9
    TYP = 10
    FAILS = 11
    
    def _get_label(self,test_run):
        label = 'standard'
        if self.mode == self.Mode.platform:
            label = test_run[self.PLATFORM]
        if self.mode == self.Mode.branch:
            label = test_run[self.BRANCH]
        if self.mode == self.Mode.mixed:
            label = test_run[self.BRANCH]+' '+test_run[self.PLATFORM]
        return label
    
    """DR IS THE DECAY RATE FOR THE EXPONENTIAL DECAY ALGORITHM"""
    dr = 10.0
    def _calculate_exp_decay(self,test_name,fail,test_run):
        label = self._get_label(test_run)
            
        if 'exp_decay' not in  self.test_info[test_name]:
            self.test_info[test_name]['exp_decay'] = dict()
        
        if label not in self.test_info[test_name]['exp_decay']:
            self.test_info[test_name]['exp_decay'][label] = 0.0
            
        self.test_info[test_name]['exp_decay'][label] = \
                    (self.test_info[test_name]['exp_decay'][label]/
                    math.exp(1.0/self.dr)+fail)
                    
        return self.test_info[test_name]['exp_decay'][label]
        
    _calculate_metric = {'exp_decay':_calculate_exp_decay}
    metric = 'exp_decay' #TODO may need other metrics?
    
    """
    Function: calculate_relevance
    This function calculates the relevance of a test by adding up the historical 
    correlations between the recent events and the test that is going to be run
    """
    def _calculate_relevance(self,test_run,test_name):
        label = self._get_label(test_run)
            
        if self.metric not in self.test_info[test_name]:
            self.test_info[test_name][self.metric] = dict()
        if label not in self.test_info[test_name][self.metric]:
            self.test_info[test_name][self.metric][label] = 0.0
            
        return self.test_info[test_name][self.metric][label]
    
    """
    Function: configure_priority_queue
    This function is in charge of calculating relevancies for tests, and 
    building the priority queue to determine which tests will run.
    """
    def _configure_priority_queue(self,test_run,input_test_list):
        # TST_NAME = 1 # This is the index of TST NAME in the priority queues
        pr_q = list() # Here is the priority queue
        zero_list = list()
        zeroes = 0
        for test_name in self.test_info:
            if test_name not in input_test_list:
                #self.logger.debug('NOT IN INPUT TEST LIST')
                continue
            relv = self._calculate_relevance(test_run,test_name)
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
    def update_results(self,fails,test_run,input_list):
        self.logger.info('UDResults - TR'+str(test_run[self.RUN_ID])+
                         ' Fls ' + str(len(fails))+
                         ' | ITLlen '+str(len(input_list)))
        self._update_count(test_run,self.upd_count)
        self._update_test_list(input_list)
        fs = dict()
        for elm in fails:
            fs[elm] = 0
        for elm in input_list:
            fail = int(elm in fs) #Changed search to O(1) per lookup from O(n)
            self._calculate_metric[self.metric](self,elm,fail,test_run)
    
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
        # If running set is < 1, then it's a percentage; else it's an exact number
        if running_set < 1.0:
            running_set = math.ceil(len(pr_queue)*running_set)
        if running_set < 50:
            running_set = 50
            
        running_set = int(running_set) if running_set < len(pr_queue) else len(pr_queue)
        
        rset = list()
        for i in range(running_set):
            rset.append(pr_queue[i][1])
        return rset

    """
    Function: _update_count
    This function updates the count of result updates or prediction rounds
    that we have ran
    """
    def _update_count(self,test_run,count):
        label = self._get_label(test_run)
        if label not in count:
            count[label] = 0
        count[label] += 1
        
        if 'standard' not in count:
            count['standard'] = 0
        if label is not 'standard':
            count['standard'] += 1
    
    """
    Function: load_status
    This function loads the initial state
    In a REAL SETTING, this function must read up to the previous test run.
    """
    def _load_initial_status(self):
        self.logger.debug('Loading status')
#        if len(self.test_info) == 0:
#            ne.get_all_test_names(self.test_info)
            
    def choose_running_set(self,test_list,running_set,test_run):
        self.logger.info('ChooseRSet - TR: '+test_run[self.RUN_ID]+
                        ' | TLlen: '+str(len(test_list))+
                        ' | RSet: '+str(running_set))
        self._update_count(test_run,self.pred_count)
        
        self._update_test_list(test_list)

        pr_queue = self._configure_priority_queue(test_run,test_list)
        
        return self._make_running_set(running_set,pr_queue)

    """
    Function: save_state
    This function stores the state of the simulator, to be able to conserve and
    reload later on (if simulation won't be done completely in memory)
    """
    def save_state(self,dbuser,dbpassword,db):
        tinfo_labels = [('test_info',
                         test+' '+metric+' '+label,
                         str(self.test_info[test][metric][label]),
                         str(self.test_info[test][metric][label]))
                        for test in self.test_info
                        for metric in self.test_info[test]
                        for label in self.test_info[test][metric]]
        upd_count_labels = [('upd_count',
                             label,
                             str(self.upd_count[label]),
                             str(self.upd_count[label]))
                             for label in self.upd_count]
        pred_count_labels = [('pred_count',
                             label,
                             str(self.pred_count[label]),
                             str(self.pred_count[label]))
                             for label in self.pred_count]
        import MySQLdb
        db = MySQLdb.connect(user=dbuser,
                            passwd=dbpassword,db=db)
        c = db.cursor()
        c.executemany(
        """INSERT INTO kokiri_data (dict, labels, value) VALUES (%s,%s,%s)
            ON DUPLICATE KEY UPDATE value = %s""",
            tinfo_labels+upd_count_labels+pred_count_labels
        )
        db.commit()
        c.close()
        db.close()
    
    """
    Function: load_state
    This function loads in the state of a previous simulation. It is the
    inverse function of save_state. They can be adapted to different permanent
    storage methods
    """
    def load_state(self,dbuser,dbpassword,db):
        self.test_info = dict()
        self.upd_count = dict()
        self.pred_count = dict()
        import MySQLdb
        db = MySQLdb.connect(user=dbuser,
                            passwd=dbpassword,db=db)
        c = db.cursor()
        c.execute("""SELECT * from kokiri_data""")
        DICT = 0
        LABELS = 1
        VAL = 2
        for row in c.fetchall():
            if row[DICT] == 'pred_count':
                self.pred_count[row[LABELS]] = int(row[VAL])
            elif row[DICT] == 'upd_count':
                self.upd_count[row[LABELS]] = int(row[VAL])
            elif row[DICT] == 'test_info':
                TEST = 0
                METRIC = 1
                LABEL = 2
                lbls = row[LABELS].split()
                if lbls[TEST] not in self.test_info:
                    self.test_info[lbls[TEST]] = dict()
                if lbls[METRIC] not in self.test_info[lbls[TEST]]:
                    self.test_info[lbls[TEST]][lbls[METRIC]] = dict()
                self.test_info[lbls[TEST]][lbls[METRIC]][lbls[LABEL]] = float(row[VAL])
        c.close()
        db.close()
        
    """
    Function: get_count
    This function returns the count of update/prediction rounds
    for the given test_run. It takes as arguments:
    - test_run - In case we need a certain platform/branch,etc
    - what_count - To define if we want the count of prediction rounds or
                    the count of result updates
    - total - To define if we want the total count, or if we want only
            the count of rounds for a given platform/branch/mix
    """
    def get_count(self,test_run,what_count,total=False):
        assert what_count in ['result_updates','prediction_rounds']
        
        label = 'standard'
        if not total:
            label = self._get_label(test_run)

        if label not in self.upd_count:
            self.upd_count[label] = 0
        if label not in self.pred_count:
            self.pred_count[label] = 0
            
        if what_count == 'result_updates':
            return self.upd_count[label]
        return self.pred_count[label]
    
    def _configure_logging(self,log_events):
        logger = logging.getLogger('simulation')
        logger.setLevel(logging.INFO)
        self.logger = logger
        sim_id = random.randrange(1000)
        if logger.handlers == []:
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
        
    def __init__(self,log_events=True,mode=Mode.platform):
        self._configure_logging(log_events)
        self._load_initial_status()
        self.mode = mode
        random.seed(1)

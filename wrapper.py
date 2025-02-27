# -*- coding: utf-8 -*-
"""
Created on Sat Jul 19 11:33:37 2014

@author: pablo
"""
import ipdb
import name_extractor as ne
import read_history as rh
import kokiri
import numpy
import re

class wrapper(object):
    fail_per_testrun = dict()
    test_info = dict()
    input_test_lists = None
    test_file_dir = None
    
    diagnostics = dict()
    
    
    TIMESTAMP = 0
    RUN_ID = 1
    BUILD_ID = 2
    NEXT_FILE_CHG = 3
    BRANCH = 7
    PLATFORM = 9
    TYP = 10
    FAILS = 11
    
    def load_startup(self):
        self.diagnostics['no_input_list'] = 0
        self.diagnostics['with_input_list'] = 0
        test_info = dict()
        if len(self.test_info) == 0:
            ne.get_all_test_names(self.test_info)
        fail_per_testrun = dict()    
        if len(self.fail_per_testrun) == 0:
            rh.load_failures(self.test_info, self.fail_per_testrun)
            
        self.input_test_lists = rh.load_input_test_lists(self.test_file_dir)
    
    """
    Function parse_out_tests
    This function is in charge of opening the file name that comes, and parsing
    out all the tests that should be considered as part of the input list.
    """
    def parse_out_tests(self,file_name):
        tests = dict()
        f = open(self.test_file_dir+file_name)
        #exp = re.compile('([^, ]*)( [^ ]*)? *(w[1-4])? \[ ([a-z]*) \]')
        exp = re.compile('([^, ]+) ?([^ ]*) *.*\[ (fail|disabled|pass|skipped) \]')
        for line in f:
            mch = exp.match(line)
            if not mch:
                continue
            test_name = mch.group(1)
            test_variant = mch.group(2)
            result = mch.group(3)
#            if result == 'skipped':
#                continue
            tests[test_name] = 0
        return tests
        
    """
    Function: get_fails
    This function returns a list of failures occurred in test_run
    """
    def get_fails(self,test_run):
        if test_run is not None and int(test_run[self.RUN_ID]) in self.fail_per_testrun:
            return self.fail_per_testrun[int(test_run[self.RUN_ID])]
        return list()
    
    """
    Function: get_input_test_list
    This function gets the list that was input to MTR on this test run, or 
    if it's not possible to find, then it defaults to 'all' tests
    """
    def get_input_test_list(self,test_run):
        label = test_run[self.PLATFORM]+' '+test_run[self.BUILD_ID]
        if label not in self.input_test_lists:
            self.diagnostics['no_input_list'] += 1
            return self.test_info # SHOULD THIS BE CHANGED TO THE WHOLE LIST OF FILES?

        if label in self.input_test_lists and len(self.input_test_lists[label]) == 0:
            print("PROBLEM WITH INPUT TEST LIST")
            self.diagnostics['no_input_list'] += 1
            return self.test_info 
            
        if label in self.input_test_lists and len(self.input_test_lists[label]) > 0:
            self.diagnostics['with_input_list'] += 1
            file_name = self.input_test_lists[label].pop(0)
            
        return self.parse_out_tests(file_name)
        
    """
    Function: verify_input_and_fails
    This function just makes sure that all failures can be caught
    """
    def verify_input_and_fails(self,input_test_list,fails):
        for elm in fails:
            if elm not in input_test_list:
                print "FAILURE NOT IN INPUT TEST LIST"
                input_test_list[elm] = 0
            #assert elm in input_test_list
            
    def run_simulation(self,max_limit,learning_set,running_set,beginning=0,
                       learning_rounds_per_unit= 0,mode = 'standard'):
        core = kokiri.kokiri(mode=mode)
        test_hist = rh.open_test_history()
        count = 0
        skips = 0
        caught_cnt = 0 # These are failures that would have been caught if the test had run
        missed_cnt = 0 # These are failures that are caught - because the test ran
        training = True # This parameter is turned to false after the training round
        pos_dist = numpy.zeros(dtype=int,shape=1200)
        
        """
        test_hist is the list from the query of test_run history. It returns 
        one-by-one the test_runs.
        In the following loop, we iterate over each test run, from the first to
        the last
        """
        for tr_index,test_run in enumerate(test_hist):
            skips += 1
            if skips <= beginning:
                continue
            if core.get_count(test_run,'result_updates',total=True) == learning_set:
                
                # First self.learning_set iterations are the learning set. 
                # After that, the simulation starts.
                training = False
                #print("==============SIMULATION HAS BEGUN================")
            count=count+1
            
#            if count%1000 == 0:
#                #ipdb.set_trace()
#                tinfo = core.test_info
#                prounds = core.pred_count
#                uprounds = core.upd_count
#                core.save_state(dbuser='root',dbpassword='admin',db='kokiri_jul24')
#                del core
#                corez = kokiri.kokiri(mode=mode)
#                corez.load_state(dbuser='root',dbpassword='admin',db='kokiri_jul24')
#                if not (tinfo == corez.test_info and 
#                        id(tinfo) != id(corez.test_info) and
#                        prounds == corez.pred_count and
#                        id(prounds) != id(corez.pred_count) and
#                        uprounds == corez.upd_count and 
#                        id(uprounds) != id(corez.upd_count)):
#                    print 'INFORMATION NOT EXACTLY EQUAL'
#                core = corez
            
            if count > max_limit:
                break # If we have iterated the max_limit of test_runs, we break out
            fails = self.get_fails(test_run)
            input_test_list = self.get_input_test_list(test_run)
            count_per_unit = core.get_count(test_run,'result_updates')
            if not training and count_per_unit < learning_rounds_per_unit:
                print 'GONE BACK TO PREDICTION FOR NEW UNIT'
            if (not training and 
                 count_per_unit >= learning_rounds_per_unit):
                if input_test_list == self.test_info:
##                    count -= 1
                    continue
                self.verify_input_and_fails(input_test_list,fails)
                rset = core.choose_running_set(input_test_list, running_set, 
                                                   test_run)
                
                missed_fails = list()
                if count >= learning_set:
                    caught_fails = list()
                    for elm in fails:
                        if elm not in rset:
                            missed_fails.append(elm)
                        else:
                            caught_fails.append(elm)
                    fails = caught_fails
                    missed_cnt += len(missed_fails)
                    caught_cnt += len(fails)
            
            core.update_results(fails,test_run,input_test_list)
        
        print('MF: '+str(missed_cnt)+' | CF: '+str(caught_cnt)+
                    ' | TF: '+str(missed_cnt+caught_cnt) +
                    ' | RECALL: '+str(caught_cnt/(missed_cnt+caught_cnt+0.0))+
                    ' | NO_IN_LST: '+str(self.diagnostics['no_input_list'])+
                    ' | WTH_IN_LST: '+str(self.diagnostics['with_input_list'])
                    )
        return core
        return caught_cnt/(missed_cnt+caught_cnt+0.0)
                    
    def __init__(self,file_dir='tests_lists/'):
        self.test_file_dir = file_dir
        self.load_startup()

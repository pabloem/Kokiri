# Results of the project
During the last 3 to 4 months, several different algorithms to analyze the 
data from mysql-test-run of MariaDB. The final resulting algorithms are two,
and each has small variants.

## The file-change correlation algorithm and the fail frequency algorithm
Two algorithms were developed and tested. In the end, the fail frequency
algorithm had slightly better results, as can be seen in the following chart

![results chart](https://raw.githubusercontent.com/pabloem/random/master/final_figure.png "Recall by running set size")

### The Fail Frequency algorithm
This algorithm is contained in the ```master``` branch of the git repository.
To decide which tests are more likely to fail in the next run, it uses a
time-weighted average of failures. The more recent a failure has been, the
more significant it will be to make the test be considered significant.
Since this algorithm had the best results, 

### The File-change correlation algorithm
This algorithm is contained in the ```file_change_correlations``` branch. It
uses correlation between changes of files and subsequent failed tests to 
estimate which test is more relevant. The performance of this algorithm is not
a lot worse than the fail frequency algorithm, but another disadvantage that
it presents is that it requires a lot of information (

## Methods exposed by the ```kokiri``` class
The algorithms are implemented by the ```kokiri``` class. This class exposes
the following methods:
### ```get_count```
This function provides the counts of update or prediction rounds for each
unit (platform, branch or mix). It can be called to know the historical
information contained by the class.
###```update_results``` - 
This function stores information for each run. It is important to call it
after every test run, no matter if there was a prediction phase or not.
### ```choose_running_set``` 
This function is the predicting function. It takes in a list of prospective
tests to run, and it returns a subset of this list, with the tests that the
class estimates to be more likely to fail.
### ```save_state```
This function stores the state of the class to persistent storage. The current
implementation stores to a local database, but it is simple enough to be
modified to store to a different database, file or other kinds of storage.
### ```load_state```
This function loads in the previous state of the class. The current
implementation loads the data from a local database, but the implementation
can easily be changed.

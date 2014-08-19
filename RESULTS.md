## Results of the project
During the last 3 to 4 months, several different algorithms to analyze the 
data from mysql-test-run of MariaDB. The final resulting algorithms are two,
and each has small variants.

### The file-change correlation algorithm and the fail frequency algorithm
Two algorithms were developed and tested. In the end, the fail frequency
algorithm had slightly better results, as can be seen in the following chart

![results chart](https://raw.githubusercontent.com/pabloem/random/master/final_figure.png "Recall by running set size")

### The Fail Frequency algorithm
This algorithm is contained in the ```master``` branch of the git repository.
To decide which tests are more likely to fail in the next run, it uses a
time-weighted average of failures. The more recent a failure has been, the
more significant it will be to make the test be considered significant.
This algorithm had the best results in tests, and is faster to run.

#### The File-change correlation algorithm
This algorithm is contained in the ```file_change_correlations``` branch. It
uses correlation between changes of files and subsequent failed tests to 
estimate which test is more relevant. The performance of this algorithm is not
a lot worse than the fail frequency algorithm, but another disadvantage that
it presents is that it requires a lot of information (parsing of filenames
from file changes, as well as keeping the correlations in memory, making it 
more space-complex).

### Methods exposed by the ```kokiri``` class
The algorithms are implemented by the ```kokiri``` class. This class exposes
the following methods:

#### The ```get_count``` method
This function provides the counts of update or prediction rounds for each
unit (platform, branch or mix). It can be called to know the historical
information contained by the class.

#### The ```update_results``` method
This function stores information for each run. It is important to call it
after every test run, no matter if there was a prediction phase or not.

#### The ```choose_running_set``` method
This function is the predicting function. It takes in a list of prospective
tests to run, and it returns a subset of this list, with the tests that the
class estimates to be more likely to fail.

#### The ```save_state``` method
This function stores the state of the class to persistent storage. The current
implementation stores to a local database, but it is simple enough to be
modified to store to a different database, file or other kinds of storage.

#### The ```load_state``` method
This function loads in the previous state of the class. The current
implementation loads the data from a local database, but the implementation
can easily be changed.

### Conclusions
After extensive testing, the results have shown that the fail frequency
strategy in 'standard' mode performs better than all the other strategies.

The file-changes correlation strategy trailed closely. Maybe a closer look at
the correlations, or a more refined equation for correlation would show useful
patterns, and may help improve the performance of the algorithm, but that is 
just wishful thinking.

Regarding the fail frequency strategy, results may vary once a lengthy and 
continuous set of data is leveraged for testing. Particularly, the 'platform' 
mode might turn out to predict better on the long term.

In conclusion, although a data-gatering phase would be necessary, it seems
that the fail frequency strategy can deliver better results, as it has done
so far.

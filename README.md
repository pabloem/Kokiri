# Analyzing MariaDB mysql-test-run Info
## INTRODUCTION
This repository contains the code to analyze and run simulations on the testing
data from MariaDB development.

## Storing and retrieving from permanent storage
The kokiri class includes a couple of functions that store and retrieve data
from a database which information can be provided to them as input. The data is
stored in a table called 'kokiri_data', which can be created as follows:
```
CREATE TABLE kokiri_data
    (dict VARCHAR(20),
    labels VARCHAR(200),
    value VARCHAR(100),
    PRIMARY_KEY(dict,labels));
```
The labels field stores the nested list of labels in python dictionaries. The
value field stores the numeric value that the element contains, so for the
following dict:
```
my_dict = {'test1':{'exp_decay':{'p1':1 'p2':3}} 'test2':{'exp_decay':{'p5':2}}}
```
The table would look as follows:
```
=================================================
|   DICT    |   LABELS              |   VALUE   |
|-----------|-----------------------|-----------|
|'my_dict'  |'test1 exp_decay p1'   |1          |
|'my_dict'  |'test1 exp_decay p2'   |3          |
|'my_dict'  |'test2 exp_decay p5'   |2          |
=================================================
```
To further customize the data storage section, the kokiri.save_state and
kokiri.load_state functions may be modified.

## Adding the test_run input test list directory
The wrapper module requires the input test list directory when being 
initialized. It should be passed to the wrapper.wrapper constructor as follows:
```
wrapper.wrapper(file_dir='directory')
```
To download and created automatically, just run download_files.sh

## Creating the csv files with SQL
This repository utilizes a few csv files that contain the data from the code 
and test history of MariaDB. In this repository, the most important csv files
are the following:

* test_fail_history_inv.csv
* test_fail_history.csv
* test_namevar.csv

### Creating test_fail_history_inv.csv
Log in to the MariaDB development database and run the following query:
```
select      
    unix_timestamp(cntr.dt) timestamp,trid run_id, b.id bbid, bs.id bsid, 
    ss.id ssid, trrev,ss.revision ssrev,trbranch,ss.branch ssbranch, 
    platform,trtyp, sum(num) fails
    from
    (select 
        tr.dt dt,tr.typ trtyp,tr.id trid,tr.bbnum trbid, platform,
        tr.revision trrev, tr.branch trbranch, if(tf.test_name is null,0,1) num
        from test_run tr left join test_failure tf on tr.id = tf.test_run_id
        order by 1 desc)
    cntr, builds b, buildrequests br, buildsets bs, sourcestamps ss

    where
        cntr.trbid = b.id and br.id = b.brid and bs.id = br.buildsetid and
        bs.sourcestampid = ss.id 
    group by 1 
    order by 1 asc 
        into outfile 
        '/tmp/test_fail_history_inv.csv' 
        fields terminated by ',' 
        enclosed by '"' 
        lines terminated by '\n';
```

### Creating test_fail_history.csv
Log in to the MariaDB development database and run the following query:
```
select
    unix_timestamp(tr.dt) timestamp, test_run_id run_id,test_name,
    test_variant, branch, revision, platform, typ, bbnum
    from
        test_run tr, test_failure tf 
    where 
        tr.id = tf.test_run_id
    order by 1 desc 
        into outfile 
        '/tmp/test_fail_history.csv'
        fields terminated by ',' 
        enclosed by '"' 
        lines terminated by '\n';
```

### Creating test_namevar.csv
Log in to the MariaDB development database and run the following query:
```
select 
    test_name, test_variant 
    from test_failure 
    group by 1, 2 
    into outfile '/tmp/test_namevar.csv' 
    fields enclosed by '"' 
    terminated by ',' 
    lines terminated by '\n';
```

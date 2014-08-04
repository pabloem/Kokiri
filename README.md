# Analyzing MariaDB mysql-test-run Info
## INTRODUCTION
This repository contains the code to analyze and run simulations on the testing
data from MariaDB development.

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
* fails_p_test_run.csv

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

### Creating fails_p_test_run.csv
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
        '/tmp/fails_p_test_run.csv'
        fields terminated by ',' 
        enclosed by '"' 
        lines terminated by '\n';
```


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
* test_fail_history.csv
* test_namevar.csv
* direct_file_changes.csv

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

### Creating direct_file_changes.csv file
Log into the MariaDB development database and run the following query:
```
select tr.id, tr.branch, tr.platform, ss.id, ss_info.chfl, ss_info.action 
    from 
     test_run tr
     left join builds b on b.id = tr.bbnum
     left join buildrequests br on br.id = b.brid
     left join buildsets bs on bs.id = br.buildsetid
     left join sourcestamps ss on ss.id = bs.sourcestampid
     left join
     (select ss.id ssid,ss.branch ssbranch,ch.changeid changeid, 
      substring_index(cf.filename,' ',1) chfl, 
      substring_index(substring_index(cf.filename,' ',3),' ', -1) action
     from change_files cf, changes ch,sourcestamp_changes ssc, sourcestamps ss 
     where cf.changeid = ch.changeid and 
         ssc.changeid = ch.changeid and 
         ssc.sourcestampid = ss.id 
         group by 1,4) ss_info on ss.id = ss_info.ssid
    into outfile 
    '/tmp/direct_file_changes.txt' 
    fields terminated by ',' 
    enclosed by '"' 
    lines terminated by '\n';
 ```

#!/bin/sh
mkdir tests_lists
cd tests_lists
wget ftp://ftp.askmonty.org/secret/buildbot_mtr_stdio.tar.gz
tar -zxvf buildbot_mtr_stdio.tar.gz
rm buildbot_mtr_stdio.tar.gz

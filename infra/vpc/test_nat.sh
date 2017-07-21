#!/bin/bash
wget http://treepotato.com/everywhere.jpg >tp.log 2>&1
aws s3 cp tp.log s3://thousandleaves-backup/test_nat.log

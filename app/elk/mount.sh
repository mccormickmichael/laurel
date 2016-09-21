#!/bin/sh

# Mount an additional volume to store ElasticSearch data. Run this on startup, probably as userdata

VOLNAME=xvdb
DEVICE=/dev/$VOLNAME
ESDATA=/var/lib/elasticsearch


lsblk | grep $VOLNAME || exit

# this isn't syntactially right, test it later
test "$(file -s $DEVICE)" == 'data' && mkfs -t ext4 $DEVICE

mkdir $ESDATA
chmod 0777 $ESDATA
mount $DEVICE $ESDATA

# no need to add to fstab if this is run on startup


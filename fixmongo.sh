#!/bin/sh

sudo service mongodb stop
cd /media/alarm_db/mongodb/
sudo rm -f mongod.lock
sudo service mongodb start

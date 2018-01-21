#!/bin/bash
#make sure a process is always running.

process_keyword="meep.py"
init_cmd="/home/pi/bin/meep/fixmongo.sh"
start_process="/usr/bin/python /home/pi/bin/meep/meep.py > /media/alarm_db/output 2>&1 &"

#Mongod likes to throw a curveball and lock itself.  Let's stop it,
#remove the .lock file, and start it again.
$init_cmd

#Check to see if the meep process is running.  If not, start it.
if ps ax | grep -v grep | grep $process_keyword > /dev/null
then
    echo "Watchdog - meep already running"
    exit
else
    echo "Watchdog - starting meep"
    $start_process
fi

exit

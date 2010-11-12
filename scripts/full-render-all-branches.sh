#!/bin/bash

# Usage: ./full-render.sh
# Example: while true; do ./full-render.sh; sleep 5; done

MCHOME=/minecraft-boo
GMAP=$MCHOME/apps/Minecraft-Overviewer/gmap.py
WORLD=$MCHOME/world
BRANCH_ROOT=$MCHOME/branches

LOGPATH=$MCHOME/logs/$(date +%Y%m%d-%H%M).log

CHUNKLIST=$LOGPATH.rsync


START=$(date +%s)

echo "Start at: $START" >> $LOGPATH

# Make sure we are in the right directory
cd $MCHOME

# Take snapshot of world
echo "Start snapshot at: $(date +%s)" >> $LOGPATH
rsync -av --password-file=/etc/rsync.password user@mcserver::world-boo $WORLD/ > $CHUNKLIST
echo "End snapshot at: $(date +%s)" >> $LOGPATH

# Unlit = default
BRANCH=unlit
CACHE=$BRANCH_ROOT/$BRANCH/cache
OUTPUT=$BRANCH_ROOT/$BRANCH/output

# Run incremental update
echo "Start incremental update at: $(date +%s)" >> $LOGPATH
echo "python $GMAP --cachedir=$CACHE $WORLD $OUTPUT" >> $LOGPATH
python $GMAP --cachedir=$CACHE $WORLD $OUTPUT
if [ $? -ne 0 ]; then
   sleep 120;
   echo "python returned error, sleeping before retrying";
fi

echo "End incremental update at: $(date +%s)" >> $LOGPATH


# Unlit = default
BRANCH=day
CACHE=$BRANCH_ROOT/$BRANCH/cache
OUTPUT=$BRANCH_ROOT/$BRANCH/output

# Run incremental update
echo "Start incremental update at: $(date +%s)" >> $LOGPATH
echo "python $GMAP --cachedir=$CACHE $WORLD $OUTPUT" >> $LOGPATH
python $GMAP --lighting --cachedir=$CACHE $WORLD $OUTPUT
if [ $? -ne 0 ]; then
   sleep 120;
   echo "python returned error, sleeping before retrying";
fi

echo "End incremental update at: $(date +%s)" >> $LOGPATH

# Unlit = default
BRANCH=night
CACHE=$BRANCH_ROOT/$BRANCH/cache
OUTPUT=$BRANCH_ROOT/$BRANCH/output

# Run incremental update
echo "Start incremental update at: $(date +%s)" >> $LOGPATH
echo "python $GMAP --cachedir=$CACHE $WORLD $OUTPUT" >> $LOGPATH
python $GMAP --night  --cachedir=$CACHE $WORLD $OUTPUT
if [ $? -ne 0 ]; then
   sleep 120;
   echo "python returned error, sleeping before retrying";
fi

echo "End incremental update at: $(date +%s)" >> $LOGPATH

# Calculate end time
END=$(date +%s)
DIFF=$(( $END - $START))

echo "It took $DIFF seconds"
echo "It took $DIFF seconds" >> $LOGPATH
let "MINS=$DIFF / 60"
let "HOURS=$MINS / 60"
echo " or $MINS minutes"
echo " or $MINS minutes" >> $LOGPATH
echo " or $HOURS hours"
echo " or $HOURS hours" >> $LOGPATH

echo "End at: $END" >> $LOGPATH
echo "DIFF: $DIFF" >> $LOGPATH

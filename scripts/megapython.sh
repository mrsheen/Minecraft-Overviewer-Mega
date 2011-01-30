#!/bin/bash

# Usage: ./mega.sh 

MCHOME=/minecraft
GMAP=$MCHOME/src/my_mods/Minecraft-Overviewer-Mega/gmap.py
LIVEWORLD=$MCHOME/server/world
WORLD=$MCHOME/world
CACHE=$MCHOME/cache
QUEUE=$MCHOME/cache
OUTPUT=$MCHOME/maps

LOGPATH=$MCHOME/logs/$(date +%Y%m%d-%H%M).log.python

START=$(date +%s)

echo "Start at: $START" >> $LOGPATH

# Make sure we are in the right directory
cd $MCHOME

# Start continuous process
echo "Start continuous process at: $(date +%s)" >> $LOGPATH
python $GMAP --cachedir=$CACHE $WORLD $OUTPUT

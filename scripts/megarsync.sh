#!/bin/bash

# Usage: ./mega.sh 

MCHOME=/minecraft
GMAP=$MCHOME/src/my_mods/Minecraft-Overviewer-Mega/gmap.py
LIVEWORLD=$MCHOME/server/world
WORLD=$MCHOME/world
CACHE=$MCHOME/cache
QUEUE=$MCHOME/cache
OUTPUT=$MCHOME/maps

LOGPATH=$MCHOME/logs/$(date +%Y%m%d-%H%M).log.rsync

START=$(date +%s)

echo "Start at: $START" >> $LOGPATH

# Make sure we are in the right directory
cd $MCHOME

# Start running rsync
while true; do
	echo "Starting rsync run"
	rsync -av --exclude 'tmp_chunk.dat' --exclude 'session.lock' $LIVEWORLD/ $WORLD/ >> $QUEUE/queue
	sleep 5
done

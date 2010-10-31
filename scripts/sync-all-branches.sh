#!/bin/bash
rsync -av --password-file=/etc/rsync.password /minecraft/maps/ user@mcserver::map


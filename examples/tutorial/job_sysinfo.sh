#!/bin/sh

HOSTNAME=$(hostname -f)
MEM=$(free -h)
DISK=$(df -h)

cat << END_OF_TEXT
Hostname
========

$HOSTNAME


Memory
======

$MEM


Disk
====

$DISK
END_OF_TEXT

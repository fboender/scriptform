#!/bin/sh

HOSTNAME=$(hostname -f)
MEM=$(free -h)
DISK=$(df -h)

cat << END_OF_TEXT
<h3>Hostname</h3>
<pre>$HOSTNAME</pre>

<h3>Memory</h3>
<pre>$MEM</pre>

<h3>Disk</h3>
<pre>$DISK</pre>
END_OF_TEXT

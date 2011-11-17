#!/bin/sh

# Interface is the parameter to the script
INTF=$1

# get the current number of bytes in and bytes out
sample1=(`/usr/sbin/netstat -ib -n | awk "/$INTF/"'{print $7" "$10; exit}'`)

# wait one second
sleep 1

# get the number of bytes in and out one second later
sample2=(`/usr/sbin/netstat -ib -n | awk "/$INTF/"'{print $7" "$10; exit}'`)

# find the difference between bytes in and out during that one second
# and convert bytes to kilobytes
results=(`echo "2k ${sample2[0]} ${sample1[0]} - 1024 / p" "${sample2[1]} ${sample1[1]} - 1024 / p" | dc`)

# print the results
printf "%s <- %.2f -> %.2f KB/sec\n" $INTF ${results[0]} ${results[1]}

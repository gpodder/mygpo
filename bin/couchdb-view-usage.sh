#!/bin/bash

DIR=`dirname $0`
cd $DIR/../mygpo
DIRS=`find . -type d -wholename "*/_design/views/*"`

for view in $DIRS; do
    view_name=`echo $view | awk '{split($0,array,"/")} END{print array[2]"/"array[5]}'`
    count=`git grep "$view_name" | wc -l`
    if [ $count = "0" ]; then
        echo -e -n "\e[00;31m"
    fi
    echo $view_name $count | awk '{ printf "%-40s%-5s\n",$1,$2}'
    echo -e -n '\e[00m'
done

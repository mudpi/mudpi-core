#!/bin/bash
FILES=/var/www/html/mudpi/public/img/snaps/*
for f in $FILES
do
  echo "Processing $f file..."
  # take action on each file. $f store current file name
  echo "Renaming $f to $f ${f::(-21)}.jpg"
  #mv $f ${f::(-17)}
done
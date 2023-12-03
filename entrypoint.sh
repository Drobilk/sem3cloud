#!/bin/sh -l

echo "Hello $1"
time=$(date)
echo "time=$time" >> $GITHUB_OUTPUT

if <condition> ; then
  echo "Game over!"
  exit 1
fi

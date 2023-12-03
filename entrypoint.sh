#!/bin/sh -l

RUN chmod +x entrypoint.sh
ENTRYPOINT ["/entrypoint.sh"]
echo "Hello $1"
time=$(date)
echo "time=$time" >> $GITHUB_OUTPUT

if <condition> ; then
  echo "Game over!"
  exit 1
fi

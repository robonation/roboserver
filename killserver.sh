#!/bin/sh

lsof -i:9000 | grep LISTEN | cut -d ' ' -f 3 | xargs kill -9

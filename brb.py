#!/bin/bash

# brb - A simple command line utility

if [ "$#" -ne 3 ]; then
    echo "Usage: brb <person> <bike> <distance>"
    exit 1
fi

PERSON="$1"
BIKE="$2"
DISTANCE="$3"

echo "$PERSON will ride the $BIKE for $DISTANCE."
#!/bin/bash

SIZES="22 16 32 48 24 256 128 512"

for size in $SIZES; do
  mkdir -p $size
  rsvg-convert \
    -w $size -h $size \
    -o $size/netflix-penguin.png \
    netflix-penguin.svg
done

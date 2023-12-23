#!/bin/bash
#
# From json file with word timestamps, get all words in sequence.
# JSON file was produced by stable-ts (word_transcribe.py)

input_file=$1
output_file=$2

jq '[.segments[] | .words[] | {word: .word, start: .start, end: .end}]' "$input_file" > "$output_file"

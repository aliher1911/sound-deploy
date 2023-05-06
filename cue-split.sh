#!/bin/bash
#
# Prereqs check 
#
satisfied=1
if ! command -v shntool &>/dev/null ; then
  echo "Error: shntool not found. Please install shntool package or make sure shntool is in the path"
  satisfied=
fi
cuetag=cuetag
if ! command -v "${cuetag}" &>/dev/null ; then
  cuetag=cuetag.sh
  if ! command -v "${cuetag}" &>/dev/null ; then
    echo "Error: cuetag or cuetag.sh not found. Please install cuetools or make sure cuetag is in the path"
    satisfied=
  fi
fi

[ -z "${satisfied}" ] && echo "Please correct errors above and retry" && exit 2

#
# Args check
#
[ -z "${1}" ] && echo "Usage "$(basename "$0")" <cue file> [<flac file>]" && exit 1

cue_path="${1}"
flac_path="${cue_path%.*}.flac"

[ -n "${2}" ] && flac_path="${2}"

name=$(basename "${cue_path}")
name="${name%.*}"

#
# Convert
#
set -ue

# Create output directory
mkdir -p "${name}"

# Split files
echo "Splitting to tracks"
shntool split -f "${cue_path}" -o "flac flac -s -5 -o %f -" -t "%n-%t" -d "${name}" "${flac_path}"
echo "Applying common tags"
"${cuetag}" "${cue_path}" "${name}"/*.flac
echo "Done"


#!/bin/bash

script_dir=$(dirname $0)
echo "Script dir is ${script_dir}" 

activator="${script_dir}/venv/bin/activate"

[ ! -f "${activator}" ] && zenity --error --text="Virtualenv not created for script.\nSee README.md" --no-wrap && exit 2

. "${activator}"

PYTHONPATH="${script_dir}"

tmpfile=$(mktemp /tmp/copy-to-car.XXXXXX)

dest="/media/${USER}/4955-ED4E"

if ! python "${script_dir}/main.py" -a deploy -d archive -p mp3 "$@" "${dest}" 2>$tmpfile ; then
    zenity --error --text="Failed to copy files. Error log in '${tmpfile}'" --no-wrap
else
    rm ${tmpfile}
    zenity --info --text="Copy '${@}' to '${dest}' complete" --no-wrap
fi

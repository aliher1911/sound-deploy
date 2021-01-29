#!/bin/bash

script_dir=$(dirname $0)
echo "Script dir is ${script_dir}"

activator="${script_dir}/venv/bin/activate"

[ ! -f "${activator}" ] && echo "Can't find venv activator at ${activator}" && exit 2

. "${activator}"

PYTHONPATH="${script_dir}"

python "${script_dir}/main.py" $@

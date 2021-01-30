Deploy flac/mp3 tags according to embedded tags
===============================================

Can move around file and rename them to form human readable structure.

Requirements
------------

Helper script expects venv craated inside venv dir:

virtualenv -p python3 --creator venv venv
pip install -r requirements.txt

Helper script could then be used with desktop intergation to process files

To convert flac to mp3 during deploy you need ffmpeg available in path

Desktop integration
-------------------

Adding script to Dolphin (or other file manager possibly)
copy provided deploy.desktop to ${HOME}/.local/share/kservices5/ServiceMenus
and edit accordingly to point to action.sh
change path in action.sh to point to your desired destination

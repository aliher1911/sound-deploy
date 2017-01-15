#!/usr/bin/python
import os
import argparse
from data import *
from deploy import *
from retag import *

class History:
    def __init__(self, histfile='relocate.hist'):
        self.history = set()
        try:
            with open('relocate.hist', 'r') as source:
                for line in source:
                    self.history.add(line.strip())
            self.file = open('relocate.hist', 'a')
        except IOError:
            self.file = open('relocate.hist', 'w')

    def has(self, name):
        return name in self.history

    def remember(self, name):
        self.history.add(name)
        self.file.write(name + '\n')
        # self.file.flush()

    def close(self):
        self.file.close()

class NoHistory:
    def has(self, file):
        return False
    def remember(self, file):
        pass
    def close(self):
        pass

def read_info(filename, album=None):
    upcase = filename.upper()
    if upcase.endswith('.MP3'):
        return Mp3Tags(filename)
    elif upcase.endswith('.FLAC'):
        return FlacTags(filename)
    else:
        print "Unknown file type for " + filename
        return None

def scan_directory(path, files):
    print "Processing directory %s" % path
    album = Album(path)
    for name in files:
        src = os.path.join(path, name)
        infos = read_info(src)
        if infos:
            album.add(src, infos)
    return None if album.empty() else album

def recursive(root):
    print "Scanning '" + root + "' recursively"
    def iterate():
        print "Iterating walk"
        return os.walk(root)
    return iterate

def single(root):
    print 'Scanning ' + root
    def iterate():
        files = [name for name in os.listdir(root) 
                      if os.path.isfile(os.path.join(root, name))]
        yield (root, [], files)
    return iterate

def directory_scanner(source, history):
    def generate():
        print "Scan tree"
        for (path, dirs, names) in source():
            if history.has(path):
                continue
            print path
            tags = scan_directory(path, names)
            if not tags:
                continue
            yield tags
    return generate

def process_albums(scanner, function, history):
    for album in scanner():
        if function(album):
            history.remember(album.path())

def main():
    parser = argparse.ArgumentParser(description='Fiddle with file tags')
    parser.add_argument('-a', choices=['deploy', 'fixup'], default='deploy', help='Action')
    parser.add_argument('src', nargs=1)
    parser.add_argument('dst', nargs='?')
    parser.add_argument('-d', choices=['fiio', 'archive'], default='fiio')
    parser.add_argument('-i', dest='interactive', action='store_true', help='Intractive e.g. ask user to choose options')
    parser.add_argument('--recursive', dest='recursive', action='store_true', help='Recursive directory scan')
    parser.add_argument('--no-recursive', dest='recursive', action='store_false', help='Scan single directory only')
    parser.add_argument('--history', dest='history', action='store_true', help='Use history file to avoid rescan')
    parser.add_argument('--title', help='Album title to set')
    parser.add_argument('--comment', help='Coment to set')
    parser.add_argument('--artist', help='Artist to set')
    parser.set_defaults(recursive=True)
    parser.set_defaults(history=False)
    parser.set_defaults(interactive=False)
    args = parser.parse_args()
    # fixme: error should be user friendly
    assert (args.a == 'fixup' or not args.dst is None), "Deploy mode requires destination path"

    pre_defined = {}
    if args.title is not None: pre_defined[TagSettings.TITLE] = args.title
    if args.comment is not None: pre_defined[TagSettings.COMMENT] = args.comment
    if args.artist is not None: pre_defined[TagSettings.ARTIST] = args.artist

    processor = move_function(args.dst) if args.a == 'deploy' else fix_function(pre_defined, True)
    history = History() if args.history else NoHistory()
    source = recursive(args.src[0]) if args.recursive else single(args.src[0])

#    print ask_user(Album('hello'), 'Title', ['Alb1', 'Alb2'])
#    process_albums(directory_scanner(source, history), processor, history)
    process_albums(directory_scanner(source, history), processor, history)

if __name__ == '__main__':
    main()

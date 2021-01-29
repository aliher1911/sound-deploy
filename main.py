#!/usr/bin/python
import os
import argparse
from data import *
from deploy import *
from retag import *
from history import *
from fiio import FiioNaming
from archive import ArchiveNaming


def read_info(filename):
    """
    Read tags from file
    """
    upcase = filename.upper()
    if upcase.endswith('.MP3'):
        return Mp3Tags(filename)
    elif upcase.endswith('.FLAC'):
        return FlacTags(filename)
    else:
        print("Unknown file type for " + filename)
        return None

    
def scan_directory(path, files):
    """
    Yield album from path
    """
    print("Processing directory %s" % path)
    album = Album(path)
    for name in files:
        src = os.path.join(path, name)
        infos = read_info(src)
        if infos:
            album.add(src, infos)
    if not album.empty():
        yield album

        
def recursive(root):
    """
    Iterate file system tree with os.walk
    returns iterator 
    """
    print("Scanning '" + root + "' recursively")
    def iterate():
        print("Iterating walk")
        return os.walk(root)
    return iterate


def single(root):
    """
    Iterate single directory content simulating os.walk behaviour
    returns iterator
    """
    print("Scanning " + root)
    def iterate():
        files = [name for name in os.listdir(root) 
                      if os.path.isfile(os.path.join(root, name))]
        yield (root, [], files)
    return iterate


def directory_scanner(source, history, dir_reader):
    """
    Iterate parsed albums from the source
    returns album iterator
    """
    def generate():
        print("Scan tree")
        for (path, dirs, names) in source():
            if history.has(path):
                continue
            print("Attempting to scan " + path)
            for tags in dir_reader(path, names):
                yield tags
    return generate


# Main processing loop:
# for each album
#  - album is scanned - tags read for all files in album directory
#  - album is prepared - tags are processed to guess album type etc
#  - album is processed - based on collected and guessed info it is copied to other location and tags are updated
def process_albums(processor, scanner, history, filter=None):
    for album in scanner():
        if not processor.prepare(album):
            print("Failed to prepare " + album.path())
            continue
        if not processor.process(album, filter):
            print("Failed to process " + album.path())
            continue
        history.remember(album.path())

        
def _config_file_name(self, filename_override=None):
    config_dir = os.path.expanduser(f"~/.config/sound-deploy")
    os.makedirs(config_dir, exist_ok=True)
    config_file = os.path.join(config_dir, "config")
    print(f"Using config file {config_file}")
    return config_file

        
def main():
    parser = argparse.ArgumentParser(description='Fiddle with file tags')
    parser.add_argument('-a', choices=['deploy', 'fixup'], default='deploy', help='Action')
    parser.add_argument('src', nargs=1)
    # deploy files
    parser.add_argument('dst', nargs='?')
    parser.add_argument('-d', choices=['fiio', 'archive', 'car'], default='fiio')
    # update files
    parser.add_argument('-i', dest='interactive', action='store_true', help='Intractive e.g. ask user to choose options')
    parser.set_defaults(interactive=False)
    parser.add_argument('--title', help='Album title to set')
    parser.add_argument('--comment', help='Coment to set')
    parser.add_argument('--artist', help='Artist to set')
    # directory scanning
    parser.add_argument('--recursive', dest='recursive', action='store_true', help='Recursive directory scan')
    parser.add_argument('--no-recursive', dest='recursive', action='store_false', help='Scan single directory only')
    parser.add_argument('--history', dest='history', action='store_true', help='Use history file to avoid rescan')
    parser.set_defaults(recursive=True)
    parser.set_defaults(history=False)

    args = parser.parse_args()
    # fixme: error should be user friendly
    assert (args.a == 'fixup' or not args.dst is None), "Deploy mode requires destination path"

    pre_defined = {}
    if args.title is not None: pre_defined[TagSettings.TITLE] = args.title
    if args.comment is not None: pre_defined[TagSettings.COMMENT] = args.comment
    if args.artist is not None: pre_defined[TagSettings.ARTIST] = args.artist

    history = History() if args.history else NoHistory()
    source = recursive(args.src[0]) if args.recursive else single(args.src[0])

    if args.a == 'deploy':
        naming = FiioNaming() if args.d == 'fiio' else ArchiveNaming()
        # This is some BS leftovers
        processor = Deployer(naming, args.dst) if args.a == 'deploy' else Tagger(pre_defined)
    else:
        # This will fail
        processor = fix_function(pre_defined, True)

    process_albums(processor, directory_scanner(source, history, scan_directory), history)

    
if __name__ == '__main__':
    main()

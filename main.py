#!/usr/bin/python
import os
import argparse
from data import *
from deploy import *
from retag import *
from history import *
from fiio import FiioNaming
from archive import ArchiveNaming
from transform import CopyProcessor, Mp3Processor


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

    
def scan_album(path, files):
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

        
def file_source(paths, recursive):
    """
    Create a source of albums and file filter to drive processor
    returns (generator, filter)
    """
    # build list of paths that could then be used for generator
    # filter will contain album -> desired paths mapping
    path_filters = {}
    album_dirs = []
    for path in paths:
        if os.path.isfile(path):
            # we need to filter tracks from album which are not explicitly requested
            album_dir = os.path.dirname(path)
            if album_dir not in path_filters:
                path_filters[album_dir] = set()
            path_filters[album_dir].add(path)
            album_dirs.append((album_dir, False))
        else:
            album_dirs.append((path, recursive))

    def iterate():
        for album_entry in album_dirs:
            album_dir = album_entry[0]
            if album_entry[1]:
                for (path, _, names) in os.walk(album_dir):
                    yield (path, names)
            else:
                files = [name for name in os.listdir(album_dir)
                         if os.path.isfile(os.path.join(album_dir, name))]
                yield (album_dir, files)

    def filter(album_path, file_path):
        if album_path in path_filters:
            return file_path in path_filters[album_path]
        return True

    return (iterate, filter)


def album_scanner(source, history, dir_reader):
    """
    Iterate parsed albums from the source
    returns album iterator
    """
    def generate():
        print("Scan tree")
        for (path, names) in source():
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
def process_albums(processor, scanner, file_filter, history):
    for album in scanner():
        if not processor.prepare(album):
            print("Failed to prepare " + album.path())
            continue
        if not processor.process(album, file_filter):
            print("Failed to process " + album.path())
            continue
        history.remember(album.path())

        
def main():
    parser = argparse.ArgumentParser(description='Fiddle with file tags')
    parser.add_argument('-a', choices=['deploy', 'fixup'], default='deploy', help='Action')
    parser.add_argument('paths', nargs='+', help="one of more sources and destination if deploying")
    # deploy files
    parser.add_argument('-d', choices=['fiio', 'archive'], default='fiio')
    parser.add_argument('-p', choices=['copy', 'mp3'], default='copy')
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
    assert (args.a == 'fixup' or len(args.paths) > 1), f"Deploy mode requires destination path"

    print(f"Paths are {args.paths}")

    
    pre_defined = {}
    if args.title is not None: pre_defined[TagSettings.TITLE] = args.title
    if args.comment is not None: pre_defined[TagSettings.COMMENT] = args.comment
    if args.artist is not None: pre_defined[TagSettings.ARTIST] = args.artist

    history = History() if args.history else NoHistory()
    
    if args.a == 'deploy':
        naming = FiioNaming() if args.d == 'fiio' else ArchiveNaming()
        transform = Mp3Processor() if args.p == 'mp3' else CopyProcessor()
        processor = Deployer(naming, args.paths[-1], transform)
        dir_source, file_filter = file_source(args.paths[:-1], args.recursive)
    else:
        # This will fail
        processor = fix_function(pre_defined, True)
        dir_source, file_filter = file_source(args.paths, args.recursive)

    process_albums(processor, album_scanner(dir_source, history, scan_album), file_filter, history)

    
if __name__ == '__main__':
    main()

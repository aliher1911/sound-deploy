#!/usr/bin/python
import os
import re
from mutagen.mp3 import MP3
from mutagen.id3 import ID3, TIT2, TALB, TPE1, TPE2, COMM, USLT, TCOM, TCON, TDRC
import mutagen.flac
import shutil
import argparse

class Mp3Tags:
    def __init__(self, filename):
        self.tags = mutagen.mp3.MP3(filename)
        self._artist = None
        self._trackName = None
        self._albumTitle = None

    # reading fields

    def trackArtist(self):
        return self._tag('TPE1')

    def albumArtist(self):
        return self._tag('TPE2')

    def trackName(self):
        return self._tag('TIT2')

    def albumName(self):
        return self._tag('TALB')

    def year(self):
        year = self._tag('TYER')
        if year:
            return str(year)
        date = self._tag('TDRC')
        # maybe we need to parse here?
        return str(date)

    def trackNumber(self):
        return self._numeric_tag('TRCK')

    def discNumber(self):
        return self._numeric_tag('TPOS')

    def _numeric_tag(self, tag):
        dn = self._tag(tag)
        if not dn:
            return None
        sep = dn.find('/')
        return dn if sep == -1 else dn[0:sep]

    def totalDiscs(self):
        dn = self._tag('TPOS')
        if not dn:
            return None
        sep = dn.find('/')
        return dn if sep == -1 else dn[sep+1:]

    def compilation(self):
        return self._tag('TCMP')

    def live(self):
        comm = self._tag('COMM')
        return comm and comm.lower().find('live') != -1

    def soundtrack(self):
        comm = self._tag('COMM')
        return comm and comm.lower().find('soundtrack') != -1

    def type(self):
        return ".mp3"

    def _tag(self, name):
        return self.tags[name][0] if name in self.tags else None

    # updating fields

    # Overwrite to make compilations, soundtracks etc
    def setArtist(self, artist):
        self._artist = artist

    # Overwrite to make compilations, soundtracks etc
    def setTrackName(self, trackName):
        self._trackName = trackName

    # Title to include artist for compilations etc
    def setTitle(self, albumTitle):
        self._albumTitle = albumTitle

    def save(self, filename):
        if not self._artist and not self._trackName and not self._albumTitle:
            print "Tags unchanged for " + filename
            return
        new_tags = mutagen.mp3.MP3(filename)
        if self._artist:
            new_tags['TPE1'] = mutagen.id3.TPE1(encoding=3, text=self._artist)
        if self._trackName:
            new_tags['TIT2'] = mutagen.id3.TIT2(encoding=3, text=self._trackName)
        if self._albumTitle:
            new_tags['TALB'] = mutagen.id3.TALB(encoding=3, text=self._albumTitle)
        new_tags.save(filename)

class FlacTags:
    def __init__(self, filename):
        self.tags = mutagen.flac.FLAC(filename)
        self._artist = None
        self._trackName = None
        self._albumTitle = None

    # reading fields

    def trackArtist(self):
        return self._tag('artist')

    def albumArtist(self):
        return self._tag('albumartist')

    def trackName(self):
        return self._tag('title')

    def albumName(self):
        return self._tag('album')

    def year(self):
        return self._tag('date')

    def trackNumber(self):
        return self._tag('tracknumber')

    def discNumber(self):
        return self._tag('discnumber')

    def totalDiscs(self):
        totd = self._tag('disctotal')
        return self._tag('totaldiscs') if not totd else totd

    def compilation(self):
        return self._tag('compilation')

    def live(self):
        comm = self._tag('comment')
        return comm and comm.lower().find('live') != -1

    def soundtrack(self):
        comm = self._tag('comment')
        return comm and comm.lower().find('soundtrack') != -1

    def type(self):
        return ".flac"

    def _tag(self, name):
        return self.tags[name][0] if name in self.tags else None

    # updating fields

    # Overwrite to make compilations, soundtracks etc
    def setArtist(self, artist):
        self._artist = artist

    # Overwrite to make compilations, soundtracks etc
    def setTrackName(self, trackName):
        self._trackName = trackName

    # Title to include artist for compilations etc
    def setTitle(self, albumTitle):
        self._albumTitle = albumTitle

    def save(self, filename):
        if not self._artist and not self._trackName and not self._albumTitle:
            print "Tags unchanged for " + filename
            return
        new_tags = mutagen.flac.FLAC(filename)
        if self._artist:
            new_tags['artist'] = self._artist
        if self._trackName:
            new_tags['title'] = self._trackName
        if self._albumTitle:
            new_tags['album'] = self._albumTitle
        new_tags.save(filename)

DISALLOWED = re.compile('[\\\\/:?*]')

def escape(filename):
    return DISALLOWED.sub('_', filename)

class Album:
    def __init__(self, path):
        self._files = []
        self._processed = False
        self._path = path

    def add(self, filename, tags):
        self._files.append([filename, '', tags])

    def empty(self):
        return len(self._files) == 0

    def destination(self):
        artist = escape(self._artist)
        album = escape(self._album)
        return os.path.join(artist, album)

    def _target_artist(self):
        if self._all_off(lambda x: x.compilation()):
            return 'Compilations'
        if self._all_off(lambda x: x.soundtrack()):
            return 'Soundtracks'
        artist = self._all_off(lambda x: x.trackArtist())
        if artist:
            return artist
        artist = self._all_off(lambda x: x.albumArtist())
        if artist:
            return artist
        # maybe fix atist from directory?
        raise Exception("Can't identify artist for " + self._files[0][0])        

    def _target_album(self):
        album = self._all_off(lambda x: x.albumName())
        if album:
            path = []
            year = self._all_off(lambda x: x.year())
            if year:
                path.append(year)
            path.append(album)
            discs = self._all_off(lambda x: x.totalDiscs())
            disc = self._all_off(lambda x: x.discNumber())
            if discs and discs > 1 or disc and disc > 1:
                path.append('[Disc ' + disc + ']')
            if self._all_off(lambda x: x.live()):
                path.append('Live')
            return '-'.join(path)
        raise Exception("Can't identify album for " + self._files[0][0])

    def _target_name(self, tags):
        path = []
        track = tags.trackNumber()
        if track:
            if len(track)==1:
                track = '0' + track
            path.append(track)
        track = tags.trackName()
        if not track:
            raise Exception("No track name")
        path.append(track)
        # Add optional artist for compilations
        return '-'.join(path) + tags.type()

    def _all_off(self, read):
        vals = set(map(lambda x: read(x[2]), self._files))
        return None if len(vals)!=1 else vals.pop()

    def analyze_tags(self):
        try:
            self._artist = self._target_artist()
            self._album = self._target_album()
            for file in self._files:
                title = self._target_name(file[2])
                file[1] = escape(title)
                file[2].setArtist(self._artist)
                file[2].setTitle(self._album)
            self._processed = True
            return True
        except Exception as e:
            print "Ignoring album : " + e.message
            return False

    def files(self):
        if not self._processed:
            raise Exception('Internal error. No tags were fixed')
        return self._files

    def path(self):
        return self._path

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

def move_album(album, destination):
    dst = os.path.join(destination, album.destination())
    print "Moving album to %s" % dst
    if not os.path.isdir(dst):
        os.makedirs(dst)
    for file in album.files():
        dest = os.path.join(dst, file[1])
        shutil.copy(file[0], dest)
        file[2].save(dest)

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

def tree_scanner(source, history):
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

def move_function(destination):
    def move_valid(album):
        if album.analyze_tags():
            move_album(album, destination)
            return True
        return False
    return move_valid


def main():
    parser = argparse.ArgumentParser(description='Fiddle with file tags')
    parser.add_argument('-a', choices=['deploy', 'fixup'], default='deploy', help='Action')
    parser.add_argument('src', nargs=1)
    parser.add_argument('dst', nargs='?')
    parser.add_argument('-d', choices=['fiio', 'archive'], default='fiio')
    parser.add_argument('-i', type=bool, default=False, help='Intractive')
    parser.add_argument('--recursive', dest='recursive', action='store_true', help='Recursive directory scan')
    parser.add_argument('--no-recursive', dest='recursive', action='store_false', help='Scan single directory only')
    parser.add_argument('--history', dest='history', action='store_true', help='Use history file to avoid rescan')
    parser.set_defaults(recursive=True)
    parser.set_defaults(history=False)
    args = parser.parse_args()
    # fixme: error should be user friendly
    assert (args.a == 'fixup' or not args.dst is None), "Deploy mode requires destination path"

    history = History() if args.history else NoHistory()
    files = recursive(args.src[0]) if args.recursive else single(args.src[0])
    process_albums(tree_scanner(files, history), move_function(args.dst), history)

if __name__ == '__main__':
    main()

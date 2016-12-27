#!/usr/bin/python
import os
import mutagen.mp3
import mutagen.flac
import shutil

SRC_DIR='Samples'
DST_DIR='Destination'

#

# Same name, same or no year, maybe multiple discs
class Album:
    def __init__(self):
        self.tracks = []
        self.year = None

    def add(self, track):
        self.tracks.append(track)
        ty = track.real_year()
        if self.year == None:
            self.year = ty
        elif self.year != ty:
            self.year = ''

    def get_year(self):
        return self.year

ALBUM_TAG = u'album'
YEAR_TAG = u'date'
TITLE_TAG = u'title'
ARTIST_TAG = u'artist'
ARTITS2_TAG = u'albumartist'

# compilation flag?

class EasyMp3File:
    def __init__(self, filename, album=None):
        self.album = album
        self.filename = filename
        self.file = mutagen.mp3.MP3(open(filename))

    # artist|compilation/[year-]album [suffix]* 
    def path_components(self):
        return [
            self.get_artist(),
            self.get_year() + self.file[ALBUM_TAG][0] + self.get_extras()
        ]

    def bit_rate(self):
        pass

    def get_artist(self):
        if ARTITS2_TAG in self.file:
            return self.file[ARTITS2_TAG][0]
        # todo: handle compilation here
        return self.file[ARTIST_TAG][0]

    def real_year(self):
        return self.file[YEAR_TAG][0] if YEAR_TAG in self.file else u''

    def get_year(self):
        if self.album:
            return self.album.get_year() + u'-'
        else:
            return self.real_year()

    def get_extras(self):
        disc = self.get_disc() 
        live = self.get_live()
        if disc or live:
            return u' ' + disc + live
        else:
            return u''

    def get_disc(self):
        return u''

    def get_live(self):
        return u''


def tag(container, tag):
    return container[tag].text[0] if tag in container else None


class Mp3File:
    def __init__(self, filename, album=None):
        self.album = album
        self.filename = filename
        self.file = mutagen.mp3.EasyMP3(open(filename))

    # artist|compilation/[year-]album [suffix]* 
    def path_components(self):
        return [
            self.get_artist(),
            self.get_year() + self.file[ALBUM_TAG][0] + self.get_extras()
        ]

    def bit_rate(self):
        pass

    def get_artist(self):
        if ARTITS2_TAG in self.file:
            return self.file[ARTITS2_TAG][0]
        # todo: handle compilation here
        return self.file[ARTIST_TAG][0]

    def real_year(self):
        return self.file[YEAR_TAG][0] if YEAR_TAG in self.file else u''

    def get_year(self):
        if self.album:
            return self.album.get_year() + u'-'
        else:
            return self.real_year()

    def get_extras(self):
        disc = self.get_disc() 
        live = self.get_live()
        if disc or live:
            return u' ' + disc + live
        else:
            return u''

    def get_disc(self):
        return u''

    def get_live(self):
        return u''


class FlacFile:
    def __init__(self, filename, album=None):
        self.album = album
        self.filename = filename
        self.file = mutagen.flac.FLAC(open(filename))

    def path_components(self):
        return [
            self.get_artist(),
            self.get_year() + self.file[ALBUM_TAG][0] + self.get_extras()
        ]

    def get_artist(self):
        # todo: handle compilation here
        return self.file[ARTIST_TAG][0]

    def bit_rate(self):
        pass

    def real_year(self):
        return self.file[YEAR_TAG][0] if YEAR_TAG in self.file else u''

    def get_year(self):
        if self.album:
            return self.album.get_year() + u'-'
        else:
            return self.real_year()

    def get_extras(self):
        disc = self.get_disc() 
        live = self.get_live()
        if disc or live:
            return u' ' + disc + live
        else:
            return u''

    def get_disc(self):
        return u''

    def get_live(self):
        return u''


def read_info(filename, album=None):
    upcase = filename.upper()
    if upcase.endswith('.FLAC'):
        return FlacFile(filename, album)
    elif upcase.endswith('.MP3'):
        return Mp3File(filename, album)
    else:
        return None

def scan_album(path, files):
    print "Processing directory %s" % path
    album = Album()
    tags = []
    for name in files:
        infos = read_info(os.path.join(path, name), album)
        if infos:
            album.add(infos)
            tags.append(infos)
    return tags

def escape(part):
    return part

def move_tags(tags):
    dst = os.path.join(
        DST_DIR,
        os.path.join(*[escape(name) for name in tags[0].path_components()])
    )
    print "Moving album to %s" % dst
    if not os.path.isdir(dst):
        os.makedirs(dst)
    for tag in tags:
        shutil.copy(tag.filename, dst)

def scan_tree(root):
    for (path, dirs, names) in os.walk(root):
        tags = scan_album(path, names)
        if not tags:
            continue
        move_tags(tags)

scan_tree(SRC_DIR)

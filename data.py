import os
from mutagen.mp3 import MP3
from mutagen.id3 import ID3, TIT2, TALB, TPE1, TPE2, COMM, USLT, TCOM, TCON, TDRC
import mutagen.flac

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

class Album:
    def __init__(self, path):
        # contains orig_filename, new_filename, tags object
        self._files = []
        self._path = path

    def add(self, filename, tags):
        self._files.append([filename, '', tags])

    def empty(self):
        return len(self._files) == 0

    def all_off(self, read):
        vals = self.all_values(read)
        return None if len(vals)!=1 else vals[0]

    def all_values(self, read):
        return filter(lambda x: x, set(map(lambda x: read(x[2]), self._files)))

    def analyze_tags(self):
        try:
            self._artist = self._target_artist()
            self._album = self._target_album()
            for file in self._files:
                title = self._target_name(file[2])
                file[1] = escape(title)
                file[2].setArtist(self._artist)
                file[2].setTitle(self._album)
            return True
        except Exception as e:
            print "Ignoring album : " + e.message
            return False

    def files(self):
        return self._files

    def path(self):
        return self._path

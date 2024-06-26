import os
import re
from mutagen.mp3 import MP3
from mutagen.id3 import ID3, TIT2, TALB, TPE1, TPE2, COMM, USLT, TCOM, TCON, TDRC
import mutagen.flac


class UpdatableTag:
    def setArtist(self, artist):
        self._newArtist = artist

    def getNewArtist(self):
        return self._newArtist if hasattr(self, '_newArtist') else self.albumArtist()

    def setAlbum(self, album):
        self._newAlbum = album

    def getNewAlbum(self):
        return self._newAlbum if hasattr(self, '_newAlbum') else self.albumName()

    def setTrackName(self, trackName):
        self._newTrackName = trackName

    def getNewTrackName(self):
        return self._newTrackName if hasattr(self, '_newTrackName') else self.trackName()

    def setTrackNumber(self, trackNum):
        self._newTrackNumber = trackNum

    def getNewTrackNumber(self):
        return self._newTrackNumber if hasattr(self, '_newTrackNumber') else self.trackNumber()


class Mp3Tags(UpdatableTag):
    
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
        return self._comm_tag('live')

    def bonus(self):
        return self._comm_tag('bonus')

    def soundtrack(self):
        return self._comm_tag('soundtrack')

    def type(self):
        return ".mp3"

    def _tag(self, name):
        return self.tags[name][0] if name in self.tags else None

    def _comm_tag(self, token):
        for name in self.tags.keys():
            if name.startswith('COMM'):
                if self.tags[name][0].lower().find(token) != -1:
                    return True
        return False

            
YEAR_EXTRACT = re.compile(".*(\\d{4}).*")


class FlacTags(UpdatableTag):
    NEW_TAG_MAP = {
        '_newArtist': 'artist',
        '_newTrackName': 'title',
        '_newAlbum': 'album',
        '_newTrackNumber': 'tracknumber'
    }

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
        date = self._tag('date')
        if date is None:
            # work around some weird tracks that use year instead or date
            return self._tag('year')
        m = YEAR_EXTRACT.match(date)
        return m.group(1) if m else date

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
        return self._comm_tag('live')

    def bonus(self):
        return self._comm_tag('bonus')

    def soundtrack(self):
        return self._comm_tag('soundtrack')

    def type(self):
        return ".flac"

    def _tag(self, name):
        return self.tags[name][0] if name in self.tags else None

    def _comm_tag(self, name):
        comm = self._tag('comment')
        desc = self._tag('description')
        return comm and comm.lower().find(name) != -1 or desc and desc.lower().find(name) != -1

            
# Aggregation result
class Aggregate:
    # values as collected from files, unique
    def __init__(self, values):
        self._values = list(values)
        self._values.sort()

    # No tracks has no value
    def empty(self):
        return len(self._values) == 1 and self._values[0] is None

    # All tracks have the same value
    def singleValue(self):
        return len(self._values) == 1 and self._values[0] is not None

    def inconsistent(self):
        return len(self._values) > 1

    # All unique values including none
    def values(self):
        return self._values

    def nonEmpty(self):
        return filter(lambda x: x, self._values)

    
class Query:
    MULTIPLE = object()


class AlbumTrack:
    # TODO: filename is full path, need to refactor
    def __init__(self, filename, tags):
        self.filename = filename
        self.newFilename = None
        self.tags = tags
        
    
class Album:
    def __init__(self, path):
        # contains orig_filename, new_filename, tags object
        self._files = []
        self._path = path

    def add(self, filename, tags):
        self._files.append(AlbumTrack(filename, tags))

    def empty(self):
        return len(self._files) == 0

    def all_same(self, attribute):
        vals = self.query(attribute)
        return vals[0] if len(vals) == 1 else Query.MULTIPLE

    def all_off(self, read):
        vals = self.query(read)
        return None if len(vals)!=1 else vals[0]

    # All values excluding Nulls
    def all_values(self, read):
        return filter(lambda x: x, self.query(read))

    def all_values(self, read):
        return filter(lambda x: x, set(map(lambda x: read(x.tags), self._files)))

    # All unique values including Nulls, utility fn
    def query(self, read):
        func = (lambda x: getattr(x.tags, read)()) if isinstance(read, str) else (lambda x: read(x.tags))
        return list(set(map(func, self._files)))

    def files(self):
        return self._files

    def path(self):
        return self._path


class FlacUpdater:
    NEW_TAG_MAP = {
        '_newArtist': 'artist',
        '_newTrackName': 'title',
        '_newAlbum': 'album',
        '_newTrackNumber': 'tracknumber'
    }

    def __init__(self, destination):
        self._destination = destination

    def apply_tags(self, update):
        new_tags = mutagen.flac.FLAC(self._destination)
        updated = False
        for k,v in FlacUpdater.NEW_TAG_MAP.items():
            if hasattr(update, k):
                new_tags[v] = getattr(update, k)
                updated = True
        if updated:
            new_tags.save(self._destination)


class Mp3Updater:
    def __init__(self, destination):
        self._destination = destination

    def apply_tags(self, update):
        new_tags = mutagen.mp3.MP3(self._destination)
        updated = False
        if hasattr(self, '_newArtist'):
            new_tags['TPE1'] = mutagen.id3.TPE1(encoding=3, text=self._newArtist)
            updated = True
        if hasattr(self, '_newTrackName'):
            new_tags['TIT2'] = mutagen.id3.TIT2(encoding=3, text=self._newTrackName)
            updated = True
        if hasattr(self, '_newAlbum'):
            new_tags['TALB'] = mutagen.id3.TALB(encoding=3, text=self._newAlbum)
            updated = True
        # we are overwriting total tracks with empty
        if hasattr(self, '_newTrackNumber'):
            new_tags['TRCK'] = mutagen.id3.TRCK(encoding=3, text=self._newTrackNumber)
            updated = True
        if updated:
            new_tags.save(self._destination)

                   
def apply_tags(updateable_tags, destination_name):
    upcase = destination_name.upper()
    if upcase.endswith('.MP3'):
        updater = Mp3Updater(destination_name)
    elif upcase.endswith('.FLAC'):
        updater = FlacUpdater(destination_name)
    else:
        return
    updater.apply_tags(updateable_tags)

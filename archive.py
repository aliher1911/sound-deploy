import re
import os
from data import Query


BLACKLIST = ["Various Artists", "Original Soundtrack", None, "", Query.MULTIPLE]
DISALLOWED = re.compile('[\\\\/:?*]')


def escape(filename):
    print(u"Escaping '{}'".format(filename))
    return DISALLOWED.sub('_', filename)


def isset(value):
    return value != None and value != '' and value != Query.MULTIPLE and value != False


def as_int(value):
    try:
        return int(value)
    except ValueError:
        return 0


class ArchiveNaming:
    def updateArtist(self, album, file):
        return True

    def updateAlbum(self, album, file):
        return True

    def updateTitle(self, album, file):
        return True

    def updateTrackNum(self, album, file):
        return True

    # This should update both album base and files
    def setPath(self, album, file, destination):
        artist = album.all_same('trackArtist')
        album_artist = album.all_same('albumArtist')
        compilation = album.all_same('compilation')
        soundtrack = album.all_same('soundtrack')
        year = album.all_same('year')
        disc = album.all_same('discNumber')
        total_discs = album.all_same('totalDiscs')
        live = album.all_same('live')
        bonus = album.all_same('bonus')

        # make artist location
        if album_artist in BLACKLIST:
            if isset(soundtrack):
                atrist_path = 'Soundtracks'
            elif isset(compilation):
                atrist_path = 'Compilations'
            elif not artist in BLACKLIST:
                atrist_path = artist
            else:
                # Fallback to compilations in that case
                atrist_path = 'Compilations'
        else:
            atrist_path = album_artist

        # make disc location
        if isset(year):
            album_path = year + "-" + file.getNewAlbum()
        else:
            album_path = file.getNewAlbum()
        if isset(total_discs) and as_int(total_discs) > 1 or isset(disc) and as_int(disc) > 1:
            album_path += " [Disc {}]".format(disc)
        if isset(live):
            album_path += " [Live]"
        if isset(bonus):
            album_path += " [Bonus]"

        # new artist + new album / new track names
        try:
            trackNum = "{:02}".format(int(file.getNewTrackNumber()))
        except:
            trackNum = file.getNewTrackNumber()
        file.newFilename = escape(trackNum + '-' + file.getNewTrackName())

        # need to build proper path
        album.newPath = os.path.join(destination, escape(atrist_path), escape(album_path))
        return True

import re
import os
from data import Query

BLACKLIST = ["Various Artists", "Original Soundtrack", None, "", Query.MULTIPLE]
DISALLOWED = re.compile('[\\\\/:?*]')

def escape(filename):
    print u"Escaping '{}'".format(filename)
    return DISALLOWED.sub('_', filename)

class FiioNaming:
    def updateArtist(self, album, file):
        artist = album.all_same('trackArtist')
        album_artist = album.all_same('albumArtist')
        compilation = album.all_same('compilation')
        soundtrack = album.all_same('soundtrack')
        print 'Soundtrack {}'.format(soundtrack)

        # if compilation
        print "Compilation '{}'".format(compilation)
        if compilation != None or artist == Query.MULTIPLE or album_artist == Query.MULTIPLE:
            print "Detected compilation"
            # if soundtrack set artist to soundtrack
            if soundtrack:
                print "Soundtrack goes to separate location"
                file.setArtist("Soundtracks")
            # if album artist is set on all tracks, set album artist as artist, don't go special
            elif not album_artist in BLACKLIST:
                print "Album artist is same or track artist is set {}/{}".format(album_artist, artist)
                file.setArtist(album_artist)
            # else set artist to compilation
            else:  
                print "Plain compilation goes to separate location"
                file.setArtist("Compilations")
        else:
            print "Detected Artist disc"
            # else if artist not same, set artist to album artist
            if artist == Query.MULTIPLE:
                file.setArtist(album_artist)
            else:
                file.setArtist(artist)
        return True

    def updateAlbum(self, album, file):
        artist = album.all_same('trackArtist')
        album_artist = album.all_same('albumArtist')
        soundtrack = album.all_same('soundtrack')
        year = album.all_same('year')
        total_discs = album.all_same('totalDiscs')
        disc = album.all_same('discNumber')
        live = album.all_same('live')
        bonus = album.all_same('bonus')

        # if soundtrack and album artist is set, set album to artist - album
        if soundtrack == True:
            if artist != Query.MULTIPLE:
                newAlbum = file.albumName() + '/' + artist
            elif not album_artist in BLACKLIST:
                newAlbum = file.albumName() + '/' + album_artist
            else:
                newAlbum = file.albumName()
        else:
            newAlbum = file.albumName()

        # if date is set on all tracks, add year prefix to album
        if year != Query.MULTIPLE:
            newAlbum = year + "-" + newAlbum

        # optional disknum, live, bonus
        if total_discs != Query.MULTIPLE and total_discs != None and total_discs != '1':
            newAlbum = newAlbum + " [Disc " + disc + "]"
        if bonus:
            newAlbum = newAlbum + " [Bonus]"
        if live:
            newAlbum = newAlbum + " [Live]"

        # set on file object
        file.setAlbum(newAlbum)
        return True

    def updateTitle(self, album, file):
        artist = album.all_same('trackArtist')
        album_artist = album.all_same('albumArtist')
        current_artist = file.trackArtist()
        print u"Atrist {}".format(artist)
        print u"AAtrist {}".format(album_artist)
        print u"CAtrist {}".format(current_artist)
        # if album artist is different from artist or track artist is different, set title to title/track artist
        if (current_artist and album_artist and current_artist != album_artist) or artist == Query.MULTIPLE:
            file.setTrackName(file.trackName() + "/" + current_artist)
        else:
            file.setTrackName(file.trackName())
        return True

    def updateTrackNum(self, album, file):
        # if total cd > 1, add 100 * cdnum to track num
        total_discs = album.all_same('totalDiscs')
        if total_discs != Query.MULTIPLE and total_discs != '1' and total_discs is not None:
            file.setTrackNumber("{:02}".format(int(file.discNumber()) * 100 + int(file.trackNumber())))
        else:
            file.setTrackNumber("{:02}".format(int(file.trackNumber())))
        return True

    # This should update both album base and files
    def setPath(self, album, file, destination):
        # new artist + new album / new track names
        file.newFilename = escape(file.getNewTrackNumber() + '-' + file.getNewTrackName())

        # workaround case where album artist and artist are consistent and different
        artist = album.all_same('trackArtist')
        album_artist = album.all_same('albumArtist')
        if not album_artist in [Query.MULTIPLE, "", None]:
            artistPath = album_artist
        else:
            artistPath = artist

        album.newPath = os.path.join(destination, escape(artistPath), escape(file.getNewAlbum()))
        return True

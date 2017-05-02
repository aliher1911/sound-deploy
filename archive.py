import re
import os
from data import Query

BLACKLIST = ["Various Artists", "Original Soundtrack", None, "", Query.MULTIPLE]
DISALLOWED = re.compile('[\\\\/:?*]')

def escape(filename):
    print u"Escaping '{}'".format(filename)
    return DISALLOWED.sub('_', filename)

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
        # new artist + new album / new track names
        file.newFilename = escape(file.getNewTrackNumber() + '-' + file.getNewTrackName())
        # need to build proper path
        album.newPath = os.path.join(destination, escape(file.getNewArtist()), escape(file.getNewAlbum()))
        return True

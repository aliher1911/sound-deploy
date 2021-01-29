import os
import re
import shutil
from data import apply_tags


# # Validate tags and return list of dicts with all new things
# def validate_tags(album):
#     try:
#         # All soundtracks are the same?
#         soundtrack = album.all_off(lambda x: x.soundtrack())
#         if soundtrack is None:
#             print "Soundtrack values are inconsistent. Ignoring %s" % (album.path())
#             return None
#         # All compilations are the same?
#         compilation = album.all_off(lambda x: x.compilation())
#         if compilation is None:
#             print "Compilation values are inconsistent. Ignoring %s" % (album.path())
#             return None
#         # All album artists are the same?
#         albumArtist = album.all_off(lambda x: x.albumArtist())
#         if albumArtist is None and not soundtrack and not compilation:
#             print "Album artist values are inconsistent and not soundtrack/compilation. Ignoring %s" % (album.path())
#             return None
#         # Different track artists?
#         track_artists = album.all_values2(lambda x: x.trackArtist())
#         atristInTracks = len(track_artists) > 1
#         # All album titles are the same?
#         albumTitle = album.all_off(lambda x: x.albumName())
#         if albumTitle is None:
#             print "Album title values are inconsistent. Ignoring %s" % (album.path())
#             return None
#         # Check all tracks numbers set
#         tracks = album.all_values2(lambda x: x.trackNumber())
#         if None in tracks:
#             print "Not all tracks has track number. Ignoring %s" % (album.path())
#             return None
#         # Track numbers to reflect double albums
#         totalDiscs = album.all_off2(lambda x: x.totalDiscs())
#         totalDiscs.extend(album.all_off2(lambda x: x.discNumber()))
#         totalDiscs.sort()
#         usePrefix = totalDiscs[-1] > 1
#         # Release year
#         releaseDates = album.all_values2(lambda x: x.year())
#         if len(releaseDates) > 1:
#             if not soundtrack and not compilation:
#                 print "Release date values are inconsistent and not soundtrack/compilation. Ignoring %s" % (album.path())
#                 return None
#             releaseDate = None
#         else:
#             releaseDate = releaseDates[0]

#         # Form locations:
#         updates = {}
#         # Setup Artist Dir:
#         if soundtrack:
#             updates[UpdateKeys.ARTIST_DIR] = "Soundtracks"
#             updates[UpdateKeys.ARTIST] = "Soundtracks"
#             artist = "Soundtracks"
#         elif compilation:
#             updates[UpdateKeys.ARTIST_DIR] = "Compilations"
#             updates[UpdateKeys.ARTIST] = "Compilations"
#             artist = "Compilations"
#         else:
#             updates[UpdateKeys.ARTIST_DIR] = escape(albumArtist)
#             artist = albumArtist
#         # Setup Album Dir:
#         album_dir = []
#         if releaseDate:
#             album_dir.append(releaseDate)
#         album_dir.append(albumTitle)
#         if albumArtist and (soundtrack or compilation):
#             album_dir.append(albumArtist)
#         updates[UpdateKeys.ALBUM_DIR] = '-'.join(map(escape, album_dir))
#         updates[UpdateKeys.ALBUM_TITLE] = '-'.join(album_dir)
#         # Build files       
#         track_updates = []
#         for file in album.files():
#             tupdates = dict(updates)
#             if compilation or soundtrack:
#                 tupdates[UpdateKeys.COMPILATION] = True
#             if usePrefix:
#                 tracknum = file.discNumber() * 100 + file.trackNumber()
#                 tupdates[UpdateKeys.TRACKNUM] = str(tracknum)
#             else:
#                 tracknum = file.trackNumber()
#             if (compilation or soundtrack) and atristInTracks:
#                 title = file.trackName() + "-" + file.trackArtist()
#                 tupdates[UpdateKeys.TRACK_TITLE] = title
#             else:
#                 title = file.trackName()
#             tupdates[UpdateKeys.FILE_NAME] = str(tracknum) + "-" + escape(title)
#             updates.append(tupdates)
#         return updates
#     except Exception as e:
#         print "Ignoring album : " + e.message
#         return False


def trim(filename, extension):
    max_len = 255 - len(extension)
    return filename if len(filename) < max_len else filename[0:max_len]


class Deployer:
    def __init__(self, naming, destination):
        """
        naming - naming scheme to apply to files
        process - function that would transform the file and provide new destination name
        destination - base destination for processing???
        """
        self._naming = naming
        #self._process = process
        self._destination = destination

    # need to: set artist, album, track, tracknum
    # updates is a list of files
    def prepare(self, album):
        album.updates = []
        for record in album.files():
            file = record[2]
            # those bits should come from naming
            if not self._naming.updateArtist(album, file): return False
            if not self._naming.updateAlbum(album, file): return False
            if not self._naming.updateTitle(album, file): return False
            if not self._naming.updateTrackNum(album, file): return False
            if not self._naming.setPath(album, file, self._destination): return False
        return True

    def process(self, album, file_filter=None):
        print("Moving album to %s" % album.newPath)
        if not os.path.isdir(album.newPath):
            os.makedirs(album.newPath)
        for record in album.files():
            file = record[2]
            if file_filter is None or file_filter(file):
                dest = os.path.join(album.newPath, trim(file.newFilename, file.type()) + file.type())
                shutil.copy(record[0], dest)
                apply_tags(file, dest)

        # print "======================================"
        # print album.newPath
        # print "======================================"
        # for file in album.files():
        #     print "Filename  : " + file[2].newFilename
        #     print "Artist    : " + file[2].newArtist
        #     print "Album     : " + file[2].newAlbum
        #     print "Tracknum  : " + file[2].newTrackNumber
        #     print "Trackname : " + file[2].newTrackName
        #     print "======================================"
        return True

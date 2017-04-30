import os
import re
import shutil
from data import Query

class UpdateKeys:
    ARTIST_DIR = 'artist_dir'
    ALBUM_DIR = 'album_dir'
    FILE_NAME = 'file_name'

    ALBUM_TITLE = 'album'
    TRACK_TITLE = 'track'
    TRACKNUM = 'tracknum'
    ARTIST = 'artist'
    COMPILATION = 'compilation'

def move_function(destination):
    def move_valid(album):
        print "Moving %s" % (album.path())
        updates = validate_tags(album)
        if updates:
            move_album(album, destination, updates)
            return True
        return False
    return move_valid

def move_album(album, destination, updates):
    dst = fiio_destination(destination, album, updates)
    print "Moving album to %s" % dst
    if not os.path.isdir(dst):
        os.makedirs(dst)
    all_files = album.files()
    for i in range(len(all_files)):
        file = all_files[i]
        update = updates[i]
        dest = os.path.join(dst, update[UpdateKeys.FILE_NAME])
        shutil.copy(file[0], dest)
        # Set tags
        if UpdateKeys.ALBUM_TITLE in update:
            file[2].setTitle(update[UpdateKeys.ALBUM_TITLE])
        if UpdateKeys.TRACK_TITLE in update:
            file[2].setTrackName(update[UpdateKeys.TRACK_TITLE])
        if UpdateKeys.TRACKNUM in update:
            file[2].setTrackNum(update[UpdateKeys.TRACKNUM])
        if UpdateKeys.ARTIST in update:
            file[2].setArtist(update[UpdateKeys.ARTIST])
        if UpdateKeys.COMPILATION in update:
            file[2].setCompilation(update[UpdateKeys.COMPILATION])
        # Save tags to file
        file[2].save(dest)

DISALLOWED = re.compile('[\\\\/:?*]')

def escape(filename):
    return DISALLOWED.sub('_', filename)

def fiio_destination(destination, album):
    artist = escape(target_artist(album))
    album = escape(target_album(album))
    return os.path.join(destination, artist, album)

def fiio_filename(album, file):
    pass

def target_artist(album):
    if album.all_off(lambda x: x.compilation()):
        return 'Compilations'
    if album.all_off(lambda x: x.soundtrack()):
        return 'Soundtracks'
    artist = album.all_off(lambda x: x.trackArtist())
    if artist:
        return artist
    artist = album.all_off(lambda x: x.albumArtist())
    if artist:
        return artist
    # maybe fix atist from directory?
    raise Exception("Can't identify artist for " + album.files()[0][0])

#def fiio_destination(destination, updates):
#    first_track = updates[0]
#    return os.path.join(destination, first_track[UpdateKeys.ARTIST_DIR], first_track[UpdateKeys.ALBUM_DIR])

# Validate tags and return list of dicts with all new things
def validate_tags(album):
    try:
        # All soundtracks are the same?
        soundtrack = album.all_off(lambda x: x.soundtrack())
        if soundtrack is None:
            print "Soundtrack values are inconsistent. Ignoring %s" % (album.path())
            return None
        # All compilations are the same?
        compilation = album.all_off(lambda x: x.compilation())
        if compilation is None:
            print "Compilation values are inconsistent. Ignoring %s" % (album.path())
            return None
        # All album artists are the same?
        albumArtist = album.all_off(lambda x: x.albumArtist())
        if albumArtist is None and not soundtrack and not compilation:
            print "Album artist values are inconsistent and not soundtrack/compilation. Ignoring %s" % (album.path())
            return None
        # Different track artists?
        track_artists = album.all_values2(lambda x: x.trackArtist())
        atristInTracks = len(track_artists) > 1
        # All album titles are the same?
        albumTitle = album.all_off(lambda x: x.albumName())
        if albumTitle is None:
            print "Album title values are inconsistent. Ignoring %s" % (album.path())
            return None
        # Check all tracks numbers set
        tracks = album.all_values2(lambda x: x.trackNumber())
        if None in tracks:
            print "Not all tracks has track number. Ignoring %s" % (album.path())
            return None
        # Track numbers to reflect double albums
        totalDiscs = album.all_off2(lambda x: x.totalDiscs())
        totalDiscs.extend(album.all_off2(lambda x: x.discNumber()))
        totalDiscs.sort()
        usePrefix = totalDiscs[-1] > 1
        # Release year
        releaseDates = album.all_values2(lambda x: x.year())
        if len(releaseDates) > 1:
            if not soundtrack and not compilation:
                print "Release date values are inconsistent and not soundtrack/compilation. Ignoring %s" % (album.path())
                return None
            releaseDate = None
        else:
            releaseDate = releaseDates[0]

        # Form locations:
        updates = {}
        # Setup Artist Dir:
        if soundtrack:
            updates[UpdateKeys.ARTIST_DIR] = "Soundtracks"
            updates[UpdateKeys.ARTIST] = "Soundtracks"
            artist = "Soundtracks"
        elif compilation:
            updates[UpdateKeys.ARTIST_DIR] = "Compilations"
            updates[UpdateKeys.ARTIST] = "Compilations"
            artist = "Compilations"
        else:
            updates[UpdateKeys.ARTIST_DIR] = escape(albumArtist)
            artist = albumArtist
        # Setup Album Dir:
        album_dir = []
        if releaseDate:
            album_dir.append(releaseDate)
        album_dir.append(albumTitle)
        if albumArtist and (soundtrack or compilation):
            album_dir.append(albumArtist)
        updates[UpdateKeys.ALBUM_DIR] = '-'.join(map(escape, album_dir))
        updates[UpdateKeys.ALBUM_TITLE] = '-'.join(album_dir)
        # Build files       
        track_updates = []
        for file in album.files():
            tupdates = dict(updates)
            if compilation or soundtrack:
                tupdates[UpdateKeys.COMPILATION] = True
            if usePrefix:
                tracknum = file.discNumber() * 100 + file.trackNumber()
                tupdates[UpdateKeys.TRACKNUM] = str(tracknum)
            else:
                tracknum = file.trackNumber()
            if (compilation or soundtrack) and atristInTracks:
                title = file.trackName() + "-" + file.trackArtist()
                tupdates[UpdateKeys.TRACK_TITLE] = title
            else:
                title = file.trackName()
            tupdates[UpdateKeys.FILE_NAME] = str(tracknum) + "-" + escape(title)
            updates.append(tupdates)
        return updates
    except Exception as e:
        print "Ignoring album : " + e.message
        return False

def updateArtist(album, file):
    artist = album.all_same('trackArtist')
    album_artist = album.all_same('albumArtist')
    compilation = album.all_same('compilation')
    soundtrack = album.all_same('soundtrack')

    # if compilation
    if compilation == True:
        # if soundtrack set artist to soundtrack
        if soundtrack:
            file.newArtist = "Soundtrack"
        # if album artist is set on all tracks, set album artist as artist, don't go special
        elif album_artist != Query.MULTIPLE or artist :
            file.newArtist = album_artist
        # else set artist to compilation
        else:  
            file.newArtist = "Compilation"
    else:
        # else if artist not same, set artist to album artist
        if artist == Query.MULTIPLE:
            file.newArtist = album_artist
        else:
            file.newArtist = artist
    return True

def updateAlbum(album, file):
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
            file.newAlbum = file.albumName() + '/' + artist
        elif album_artist != Query.MULTIPLE:
            file.newAlbum = file.albumName() + '/' + album_artist
        else:
            file.newAlbum = file.albumName()
    else:
        file.newAlbum = file.albumName()

    # if date is set on all tracks, add year prefix to album
    if year != Query.MULTIPLE:
        file.newAlbum = year + "-" + file.newAlbum

    # optional disknum, live, bonus
    if total_discs != Query.MULTIPLE and total_discs != None and total_discs != '1':
        file.newAlbum = file.newAlbum + " [Disc " + disc + "]"
    if bonus:
        file.newAlbum = file.newAlbum + " [Bonus]"
    if live:
        file.newAlbum = file.newAlbum + " [Live]"

    return True

def updateTitle(album, file):
    artist = album.all_same('trackArtist')
    album_artist = album.all_same('albumArtist')
    current_artist = file.trackArtist()
    # if album artist is different from artist or track artist is different, set title to title/track artist
    if current_artist != file.newArtist or artist == Query.MULTIPLE:
        file.newTrackName = file.trackName() + "/" + current_artist
    else:
        file.newTrackName = file.trackName()
    return True

def updateTrackNum(album, file):
    # if total cd > 1, add 100 * cdnum to track num
    total_discs = album.all_same('totalDiscs')
    if total_discs != Query.MULTIPLE and total_discs != '1' and total_discs is not None:
        file.newTrackNumber = str(int(file.discNumber()) * 100 + int(file.trackNumber()))
    else:
        file.newTrackNumber = file.trackNumber()
    return True

# This should update both album base and files
def setPath(album, file, destination):
    # new artist + new album / new track names
    file.newFilename = escape(file.newTrackNumber + '-' + file.newTrackName)
    album.newPath = os.path.join(destination, escape(file.newArtist), escape(file.newAlbum))
    return True

class Deployer:
    def __init__(self, naming, destination):
        self._naming = naming
        self._destination = destination

    # need to: set artist, album, track, tracknum
    # updates is a list of files
    def prepare(self, album):
        album.updates = []
        for record in album.files():
            file = record[2]
            # those bits should come from naming
            if not updateArtist(album, file): return False
            if not updateAlbum(album, file): return False
            if not updateTitle(album, file): return False
            if not updateTrackNum(album, file): return False
            if not setPath(album, file, self._destination): return False
        return True

    def process(self, album):
        print "Moving album to %s" % album.newPath
        if not os.path.isdir(album.newPath):
            os.makedirs(album.newPath)
        for record in album.files():
            file = record[2]
            dest = os.path.join(album.newPath, file.newFilename + file.type())
            shutil.copy(record[0], dest)
            file.apply_tags(dest)

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

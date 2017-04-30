import os
import re
import shutil

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

class FiioNaming:
    def __init__(self):
        pass


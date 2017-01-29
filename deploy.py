import os
import re
import shutil

def move_function(destination):
    def move_valid(album):
        if enrich_tags(album):
            move_album(album, destination)
            return True
        return False
    return move_valid

def move_album(album, destination):
    dst = fiio_destination(destination, album)
    print "Moving album to %s" % dst
    if not os.path.isdir(dst):
        os.makedirs(dst)
    for file in album.files():
        dest = os.path.join(dst, file[1])
        shutil.copy(file[0], dest)
        file[2].save(dest)

DISALLOWED = re.compile('[\\\\/:?*]')

def escape(filename):
    return DISALLOWED.sub('_', filename)

def fiio_destination(destination, album):
    artist = escape(target_artist(album))
    album = escape(target_album(album))
    return os.path.join(destination, artist, album)

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

def target_name(tags, add_artist):
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
    if add_artist:
        path.append(tags.trackArtist())        
    return '-'.join(path) + tags.type()

def target_album(album):
    album_name = album.all_off(lambda x: x.albumName())
    if album_name:
        path = []
        year = album.all_off(lambda x: x.year())
        if year:
            path.append(year)
        path.append(album_name)
        discs = album.all_off(lambda x: x.totalDiscs())
        disc = album.all_off(lambda x: x.discNumber())
        if discs and discs > 1 or disc and disc > 1:
            path.append('[Disc ' + disc + ']')
        if album.all_off(lambda x: x.live()):
            path.append('Live')
        return '-'.join(path)
    raise Exception("Can't identify album for " + album.files()[0][0])

def enrich_tags(album):
    try:
        artist = target_artist(album)
        album_name = target_album(album)
        for file in album.files():
            title = target_name(file[2], False)
            file[1] = escape(title)
            file[2].setArtist(artist)
            file[2].setTitle(album_name)
        return True
    except Exception as e:
        print "Ignoring album : " + e.message
        return False

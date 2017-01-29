import os

class FixResult:
    VALID = 1
    FIXED = 2
    SKIPED = 3
    ABORT = 4

class UserChoice:
    SKIP = -1
    ABORT = -2

class TagSettings:
    ARTIST = 'Artist'
    COMMENT = 'Comment'
    TITLE = 'Title'

# Up 0 is dir itself (e.g. probably album name)
def get_dir_up(album_path, up):
    full = os.path.abspath(album_path)
    while full != '/' and up >= 0:
        full, name = os.path.split(full)
    return name

def only_value(list):
    return None if len(list)!=1 else list[0]

def ask_user(album, field, options):
    print "Choose %s for %s:" % (field, album.path())
    for i in range(1, len(options) + 1):
        print "%i) %s" % (i, options[i-1])
    print "a) Abort"
    print "s) Skip"
    while True:
        choice = raw_input().strip()
        if choice == 'a':
            return UserChoice.ABORT
        if choice == 's':
            return UserChoice.SKIP
        try:
            index = int(choice)
            if index < 1 or index > len(options):
                print "Invalid input %s" % (choice)
            return index - 1
        except:
            print "Invalid input %s" % (choice)

def do_fix(album, field, values, interactive, check_validity, guess_options, update):
    if field in values:
        options = [values[field]]
        choice = ask_user(album, field, options) if interactive else 0
    else:
        if not check_validity(album):
            if not interactive:
                print "Invalid %s in %s, skipping" % (field, album.path)
                return FixResult.SKIPED
            options = guess_options(album, field)
            choice = ask_user(album, field, options)
        else:
            return FixResult.VALID
    if choice == UserChoice.SKIP:
        return FixResult.SKIPED
    if choice == UserChoice.ABORT:
        return FixResult.ABORT
    value = options[choice]
    update(album, field, value)
    return FixResult.FIXED

# Fixing album title
def is_title_valid(album):
    # All tracks have same name and not empty
    vals = album.all_values(lambda x: x.albumName())
    return len(vals) == 1 and vals.pop()

def guess_title(album, field):
    options = list(album.all_values(lambda x: x.albumName()))
    options.append(get_dir_up(album.path(), 0))
    return filter(lambda x: x, options)

def update_title(album, field, value):
    for track in album.files():
        track[2].setTitle(value)

# Fixing artist/compilation
#...
def is_artist_valid(album):
    track_artists = album.all_values(lambda x: x.trackArtist())
    if only_value(track_artists):
        return True
    album_artists = album.all_values(lambda x: x.trackArtist())
    if only_value(album_artists):
        return True
    return False

def guess_artist(album, field):
    options = list(set(album.all_values(lambda x: x.trackArtist())) \
              .union(album.all_values(lambda x: x.trackArtist())))
    options.append(get_dir_up(album.path(), 1))
    return filter(lambda x: x, options)

def update_artist(album, field, value):
    for track in album.files():
        track[2].setArtist(value)

# Fixing track names ?
#...

# Fixing year
#...

# Fixing track numbers
#...

# Fixing CD numbers
#...

def fix_function(values, interactive):
    def fix_directory(album):
        need_save = False;
        fixed = do_fix(album, TagSettings.TITLE, values, interactive, is_title_valid, guess_title, update_title)
        if fixed == FixResult.ABORT: return False
        need_save = need_save or fixed == FixResult.FIXED
        fixed = do_fix(album, 'Artist', values, interactive, is_artist_valid, guess_artist, update_artist)
        if fixed == FixResult.ABORT: return
        need_save = need_save or fixed == FixResult.FIXED
        # Track names
        # Track numbers
        # CD Number
        # Year

        if need_save:
            for track in album.files():
                print "Updating %s" % (track[0])
                track[2].save(track[0])
        return True
    return fix_directory

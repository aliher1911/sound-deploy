import os
import shutil

def move_function(destination):
    def move_valid(album):
        if album.analyze_tags():
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

def fiio_destination(destination, album):
    dst = os.path.join(destination, album.destination())
    return dst

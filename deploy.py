import os
import re
import shutil
from data import apply_tags


def trim(filename, extension):
    max_len = 255 - len(extension)
    return filename if len(filename) < max_len else filename[0:max_len]


class Deployer:
    def __init__(self, naming, destination, processor):
        """
        naming - naming scheme to apply to files
        process - function that would transform the file and provide new destination name
        destination - base destination for processing???
        """
        self._naming = naming
        #self._process = process
        self._destination = destination
        self._processor = processor

    # need to: set artist, album, track, tracknum
    # updates is a list of files
    def prepare(self, album):
        album.updates = []
        for record in album.files():
            file = record.tags
            # those bits should come from naming
            if not self._naming.updateArtist(album, file): return False
            if not self._naming.updateAlbum(album, file): return False
            if not self._naming.updateTitle(album, file): return False
            if not self._naming.updateTrackNum(album, file): return False
            if not self._naming.setPath(album, record, self._destination): return False
        return True

    def process(self, album, file_filter=None):
        print("Moving album to %s" % album.newPath)
        if not os.path.isdir(album.newPath):
            os.makedirs(album.newPath)
        for record in album.files():
            if file_filter is None or file_filter(album.path(), record.filename):
                dest_template = os.path.join(album.newPath,
                                    trim(record.newFilename, record.tags.type()))
                dest = self._processor.process_file(record.filename, dest_template)
                if dest is None:
                    raise ValueError()
                apply_tags(record.tags, dest)
        return True

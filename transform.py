import shutil
import os
import subprocess as proc

class CopyProcessor:
    def process_file(self, source_path, destination_path):
        """
        source_path - path of original file
        destination_path - destination path with extension stripped
        """
        _, src_ext = os.path.splitext(source_path)
        dest = destination_path + src_ext.lower()
        shutil.copy(source_path, dest)
        return dest


class Mp3Processor:
    def process_file(self, source_path, destination_path):
        _, src_ext = os.path.splitext(source_path)
        src_ext = src_ext.lower()
        dest = destination_path + ".mp3"
        if src_ext == ".mp3":
            shutil.copy(source_path, dest)
        else:
            print(f"Encoding {source_path} to {dest}")
            result = proc.run(
                ["ffmpeg", "-y", "-i", source_path, "-b:a", "320K", "-qscale:a", "0", dest],
                capture_output=True
            )
            if result.returncode != 0:
                print("Failed to encode:\n" + result.stderr.decode("utf-8"))
                return None
        return dest

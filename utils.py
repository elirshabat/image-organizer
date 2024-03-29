import os
from hashlib import md5
import exifread
from datetime import datetime
import imghdr
import logging
import time

video_file_extensions = (".webm", ".mkv", ".flv", ".vob", ".ogv", ".ogg", ".drc", ".gif", ".gifv", ".mng", ".avi",
                         ".mts", ".m2ts", ".ts", ".mov", ".qt", ".wmv", ".yuv", ".rm", ".rmvb", ".asf", ".amv", ".mp4",
                         ".m4p", ".m4v", ".mpg", ".mpeg", ".m2v", ".m4v", ".svi", ".3gp", ".3g2", ".mxf", ".roq",
                         ".nsv", ".flv", ".f4v", ".f4p", ".f4a", ".f4b")


def list_subtree(root_dir, recursive):
    if os.path.isfile(root_dir):
        return [root_dir]
    elif recursive:
        subtree_files = []
        for dir, _, files in os.walk(root_dir):
            for file in files:
                subtree_files.append(os.path.abspath(os.path.join(dir, file)))
        return subtree_files
    else:
        all_paths = [os.path.join(root_dir, filename)
                                  for filename in os.listdir(root_dir)]
        return [path for path in all_paths if os.path.isfile(path)]


def list_subtree_dirs(root_dir, recursive):
    if os.path.isfile(root_dir):
        return []
    elif recursive:
        subtree_dirs = []
        for curr_dir, _, _ in os.walk(root_dir):
            subtree_dirs.append(curr_dir)
        return subtree_dirs
    else:
        all_paths = [os.path.join(root_dir, filename)
                                  for filename in os.listdir(root_dir)]
        return [path for path in all_paths if os.path.isdir(path)]


def is_image(file_path):
    return imghdr.what(file_path) is not None


def is_video(file_path):
    ext = os.path.splitext(file_path)[1]
    return ext.lower() in video_file_extensions


def is_media(file_path):
    return is_video(file_path) or is_image(file_path)


def get_modification_time(file_path):
    mod_time_float = os.path.getmtime(file_path)
    return datetime.strptime(time.ctime(mod_time_float), "%a %b %d %H:%M:%S %Y")


def get_media_time(img_file, valid_mod_time=False):
    try:
        with open(img_file, 'rb') as fh:
            tags = exifread.process_file(fh, stop_tag="EXIF DateTimeOriginal")
    except ValueError:
        tags = None

    if tags is not None and "EXIF DateTimeOriginal" in tags:
        date_taken = tags["EXIF DateTimeOriginal"]
        return datetime.strptime(str(date_taken), "%Y:%m:%d %H:%M:%S")
    elif valid_mod_time:
        return get_modification_time(img_file)
    else:
        raise ValueError("Failed to get creation time")


def create_logger(log_file, logger_name):
    logger = logging.getLogger(logger_name)
    logger.setLevel(logging.DEBUG)
    # create file handler which logs even debug messages
    # TODO remove: log_filename = datetime.now().strftime("%Y_%m_%d-%H_%M_%S-organization.log")
    # fh = logging.FileHandler(os.path.join(log_dir, "image_organization.log"), encoding='utf-8')
    fh = logging.FileHandler(log_file, encoding='utf-8')
    fh.setLevel(logging.DEBUG)
    # create console handler with a higher log level
    ch = logging.StreamHandler()
    ch.setLevel(logging.ERROR)
    # create formatter and add it to the handlers
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    fh.setFormatter(formatter)
    ch.setFormatter(formatter)
    # add the handlers to the logger
    logger.addHandler(fh)
    logger.addHandler(ch)
    return logger


def file_hash(file_path, chunk_size=2**24):
    """
    Compute the MD5 hash of the given file.
    """
    hash_md5 = md5()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(chunk_size), b""):
            hash_md5.update(chunk)
    return hash_md5.hexdigest()


def delete_empty_dirs(root_dir, recursive):
    if not os.path.isdir(root_dir):
        raise ValueError("First input is not a directory")
    
    for name in os.listdir(root_dir):
        path = os.path.join(root_dir, name)
        if os.path.isdir(path):
            if recursive:
                delete_empty_dirs(path, recursive=True)
            
            if len(os.listdir(path)) == 0:
                os.rmdir(path)

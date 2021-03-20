import os
from hashlib import md5
import exifread
from datetime import datetime
import imghdr
import logging
import time
from tqdm import tqdm
import re

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


# TODO: verify that the logger exists
def get_logger(logger_name):
    return logging.getLogger(logger_name)


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


def list_media_files(repo_path, show_progress=False):
    ls = list_subtree(repo_path, recursive=True)
    ls_iterator = tqdm(ls, desc="Listing media files") if show_progress else ls
    media_files = []
    for f in ls_iterator:
        try:
            if is_media(f):
                media_files.append(f)
        except:
            print(f"ERROR - failed to check if a file is a media file '{f}'")

    return media_files


def list_new_media_files(repo_path, last_update_time, show_progress=False):
    all_media_files = list_media_files(repo_path, show_progress=show_progress)
    new_media_files = []
    all_media_iterator = tqdm(all_media_files, desc="Identifying new media") if show_progress else all_media_files
    for f in all_media_iterator:
        try:
            mtime = datetime.fromtimestamp(os.stat(f).st_mtime)
            ctime = datetime.fromtimestamp(os.stat(f).st_ctime)

            if mtime > last_update_time or ctime > last_update_time:
                new_media_files.append(f)

        except:
            print(f"ERROR - failed to get stats from '{f}'")

    return new_media_files


def list_modified_media_folders(repo_path, last_update_time, show_progress=False):
    media_dirs = list_subtree_dirs(repo_path, recursive=False)
    mod_dirs = []
    dirs_iterator = tqdm(media_dirs, desc="Listing modified folders") if show_progress else media_dirs
    for d in dirs_iterator:
        try:
            mtime = datetime.fromtimestamp(os.stat(d).st_mtime)
            ctime = datetime.fromtimestamp(os.stat(d).st_ctime)
            if mtime > last_update_time or ctime > last_update_time:
                mod_dirs.append(d)
        except:
            print(f"ERROR - failed to get stats from '{d}'")

    return mod_dirs


def get_media_dirs(repo_dir):
    all_dirs = list_subtree(repo_dir, recursive=False)
    media_dirs = [dir_path for dir_path in all_dirs if
                  re.search(r"\d{4}_\d{2}", os.path.basename(dir_path)) is not None]
    return media_dirs


def get_last_update_time(path):
    mtime = datetime.fromtimestamp(os.stat(path).st_mtime)
    ctime = datetime.fromtimestamp(os.stat(path).st_ctime)
    if mtime > ctime:
        return mtime
    else:
        return ctime


def is_path_in_list(path, path_list):
    norm_path = os.path.normpath(path)
    for p in path_list:
        if norm_path == os.path.normpath(p):
            return True
    return False


def order_files(file1, file2):
    """
    Compute the order between two files, return the earlier file.
    :param file1: The first file.
    :param file2: The second file.
    :return: 1 if the first file precede the second file,
             2 if the second file precede the first file,
             0 if the two files are actually the same file
    """
    mtime1 = datetime.fromtimestamp(os.stat(file1).st_mtime)
    mtime2 = datetime.fromtimestamp(os.stat(file2).st_mtime)
    ctime1 = datetime.fromtimestamp(os.stat(file1).st_ctime)
    ctime2 = datetime.fromtimestamp(os.stat(file2).st_ctime)

    if mtime1 < mtime2:
        return 1
    elif mtime1 > mtime2:
        return 2
    elif ctime1 < ctime2:
        return 1
    elif ctime1 > ctime2:
        return 2
    elif file1 < file2:
        return 1
    elif file1 > file2:
        return 2
    else:
        return 0

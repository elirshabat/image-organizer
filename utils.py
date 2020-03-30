import os
import exifread
from datetime import datetime
import imghdr
import logging


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
        all_paths = [os.path.join(root_dir, filename) for filename in os.listdir(root_dir)]
        return [path for path in all_paths if os.path.isfile(path)]


def is_image(file_path):
    return imghdr.what(file_path) is not None


def get_image_date(img_file):
    with open(img_file, 'rb') as fh:
        tags = exifread.process_file(fh, stop_tag="EXIF DateTimeOriginal")
        if "EXIF DateTimeOriginal" in tags:
            date_taken = tags["EXIF DateTimeOriginal"]
            return datetime.strptime(str(date_taken), "%Y:%m:%d %H:%M:%S")
        else:
            raise ValueError(f"Cannot get original time from image {img_file}")


def create_logger(log_dir, logger_name):
    logger = logging.getLogger(logger_name)
    logger.setLevel(logging.DEBUG)
    # create file handler which logs even debug messages
    # TODO remove: log_filename = datetime.now().strftime("%Y_%m_%d-%H_%M_%S-organization.log")
    fh = logging.FileHandler(os.path.join(log_dir, "image_organization.log"))
    fh.setLevel(logging.DEBUG)
    # create console handler with a higher log level
    ch = logging.StreamHandler()
    ch.setLevel(logging.ERROR)
    # create formatter and add it to the handlers
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    fh.setFormatter(formatter)
    ch.setFormatter(formatter)
    # add the handlers to the logger
    logger.addHandler(fh)
    logger.addHandler(ch)
    return logger

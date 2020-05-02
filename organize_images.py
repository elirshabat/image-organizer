from argparse import ArgumentParser
import os
import shutil
from tqdm import tqdm
from utils import list_subtree, is_media, get_media_time, create_logger
import filecmp


def _main():
    out_dir = args.out_dir
    if not os.path.exists(out_dir):
        os.mkdir(out_dir)

    log_dir = args.log_dir if args.log_dir is not None else out_dir
    logger = create_logger(log_dir, "image_organizer")

    logger.info("started new session")

    print("Listing subtree...")
    all_files = list_subtree(args.source_dir, recursive=args.recursive)

    media_files = []
    for f in tqdm(all_files, desc="Filtering non-media files"):
        try:
            if is_media(f):
                media_files.append(f)
        except OSError:
            logger.warning(f"OS error while checking if '{f}' is a media file")

    for src_file in tqdm(media_files, desc="Organizing Media"):
        try:
            time_taken = get_media_time(src_file, args.valid_mod_time)
        except ValueError:
            logger.warning(f"failed to get time from '{src_file}'")
            continue

        dst_dir = os.path.join(out_dir, f"{time_taken.year:04}_{time_taken.month:02}")
        if not os.path.exists(dst_dir):
            os.mkdir(dst_dir)
        dst_filename = os.path.basename(src_file)
        dst_file = os.path.join(dst_dir, dst_filename)

        if os.path.exists(dst_file):
            if filecmp.cmp(src_file, dst_file):
                if not args.copy:
                    if args.dry_run:
                        logger.info(f"Would remove '{src_file}' - duplicate of '{dst_file}'")
                    else:
                        os.remove(src_file)
                        logger.info(f"Remove '{src_file}' - duplicate of '{dst_file}'")
                else:
                    logger.info(f"Ignoring '{src_file}' - duplicate of '{dst_file}'")
            else:
                logger.warning(f"failed to handle '{src_file}' - destination file '{dst_file}' already exists")
            continue

        if args.dry_run:
            if args.copy:
                logger.info(f"Would copy '{src_file}' to '{dst_file}'")
            else:
                logger.info(f"Would move '{src_file}' to '{dst_file}'")
        else:
            if args.copy:
                logger.info(f"Copy '{src_file}' to '{dst_file}'")
                shutil.copyfile(src_file, dst_file)
            else:
                logger.info(f"Move '{src_file}' to '{dst_file}'")
                shutil.move(src_file, dst_file)


if __name__ == '__main__':
    arg_parser = ArgumentParser()
    arg_parser.add_argument("source_dir", help="path to source image directory")
    arg_parser.add_argument("out_dir", help="path to output directory")
    arg_parser.add_argument("--recursive", "-r", action="store_true",
                            help="indicate to apply recursively on source directory")
    arg_parser.add_argument("--copy", "-c", action="store_true",
                            help="indicate to copy file instead of moving them")
    arg_parser.add_argument("--dry-run", "-d", action="store_true",
                            help="indicate to run try run (i.e. print to console what would have been done")
    arg_parser.add_argument("--log-dir", help="path to logs directory")
    arg_parser.add_argument("--valid-mod-time", "--mod", action='store_true',
                            help="Indicate to use file's modification time if the EXIF does not contain creation time")
    args = arg_parser.parse_args()
    _main()

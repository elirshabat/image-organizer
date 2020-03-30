from argparse import ArgumentParser
import os
from utils import create_logger, list_subtree, is_image, get_image_date
from tqdm import tqdm
import filecmp


def _main():
    out_dir = args.dst_dir
    if not os.path.exists(out_dir):
        raise ValueError("Destination directory does not exist")

    log_dir = args.log_dir if args.log_dir is not None else out_dir
    logger = create_logger(log_dir, "image_organizer")

    logger.info("started new remove-duplicate session")

    print("Listing subtree...")
    all_files = list_subtree(args.source_dir, recursive=args.recursive)

    img_files = []
    for f in tqdm(all_files, desc="Filtering non-image files"):
        try:
            if is_image(f):
                img_files.append(f)
        except OSError:
            logger.warning(f"OS error while checking if '{f}' is an image")

    for src_file in tqdm(img_files, desc="Removing duplicates"):
        try:
            date_taken = get_image_date(src_file)
        except ValueError:
            logger.warning(f"failed to get date from '{src_file}'")
            continue

        dst_dir = os.path.join(out_dir, f"{date_taken.year:04}_{date_taken.month:02}")
        dst_filename = os.path.basename(src_file)
        dst_file = os.path.join(dst_dir, dst_filename)

        if os.path.exists(dst_file):
            binary_equals = filecmp.cmp(src_file, dst_file)
            if binary_equals:
                if args.dry_run:
                    logger.info(f"Would remove '{src_file}'")
                else:
                    logger.info(f"Remove source duplicate '{src_file}'")
                    os.remove(src_file)


if __name__ == '__main__':
    arg_parser = ArgumentParser()
    arg_parser.add_argument("source_dir", help="path to source image directory")
    arg_parser.add_argument("dst_dir", help="path to destination directory")
    arg_parser.add_argument("--recursive", "-r", action="store_true",
                            help="indicate to apply recursively on source directory")
    arg_parser.add_argument("--dry-run", "-d", action="store_true",
                            help="indicate to run try run (i.e. print to console what would have been done")
    arg_parser.add_argument("--log-dir", help="path to logs directory")
    args = arg_parser.parse_args()
    _main()

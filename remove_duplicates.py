from argparse import ArgumentParser
import os
from mediaorg.utils import create_logger, list_subtree, is_media, file_hash
from tqdm import tqdm
import filecmp


def _main():
    media_dirs = args.media_dirs
    for media_dir in media_dirs:
        if not os.path.exists(media_dir):
            raise ValueError(f"Media directory '{media_dir}' does not exist")

    log_file = args.log_file if args.log_file is not None else os.path.join(media_dirs[0], "image_organization.log")
    logger = create_logger(log_file, "duplicate_detector")

    logger.info("started new remove-duplicate session")

    print("Listing subtree...")
    all_files = []
    for media_dir in media_dirs:
        all_files.extend(list_subtree(media_dir, recursive=args.recursive))

    media_files = []
    for f in tqdm(all_files, desc="Filtering non-media files"):
        try:
            if is_media(f):
                media_files.append(f)
        except OSError:
            logger.warning(f"OS error while checking if '{f}' is a media file")

    hash_dict = dict()

    n_duplicates_found = n_duplicates_removed = 0
    for file_path in tqdm(media_files, desc="Removing duplicates"):
        try:
            h = file_hash(file_path)
        except PermissionError:
            logger.error(f"Permission error while computing the hash of '{file_path}'")
            continue

        if h in hash_dict:
            dup_candidates = hash_dict[h]
            dup_file = None
            for candidate_file in dup_candidates:
                if filecmp.cmp(file_path, candidate_file):
                    dup_file = candidate_file
                    break
            if dup_file is not None:
                n_duplicates_found += 1
                if args.dry_run:
                    logger.info(f"Would remove {file_path} - duplication of {dup_file}")
                else:
                    logger.info(f"Remove {file_path} - duplication of {dup_file}")
                    os.remove(file_path)
                    n_duplicates_removed += 1
            else:
                hash_dict[h].append(file_path)
        else:
            hash_dict[h] = [file_path]

    print(f"Done - removed {n_duplicates_removed}/{n_duplicates_found} duplicates")


if __name__ == '__main__':
    arg_parser = ArgumentParser()
    arg_parser.add_argument("media_dirs", nargs='+', help="directories with duplicates to remove (order is important)")
    arg_parser.add_argument("--recursive", "-r", action="store_true",
                            help="indicate to apply recursively on source directory")
    arg_parser.add_argument("--dry-run", "-d", action="store_true",
                            help="indicate to run try run (i.e. print to console what would have been done")
    arg_parser.add_argument("--log-file", help="path to log file (default to the first media directory)")
    args = arg_parser.parse_args()
    _main()

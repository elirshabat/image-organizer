from argparse import ArgumentParser
import exifread
from datetime import datetime
import os
import imghdr
import shutil


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


def _main():
    out_dir = args.out_dir
    if not os.path.exists(out_dir):
        os.mkdir(out_dir)

    all_files = list_subtree(args.source_dir, recursive=args.recursive)
    img_files = [f for f in all_files if is_image(f)]
    for src_file in img_files:
        try:
            date_taken = get_image_date(src_file)
        except ValueError:
            print(f"WARNING - failed to get date from {src_file}")
            continue

        dst_dir = os.path.join(out_dir, f"{date_taken.year:04}_{date_taken.month:02}")
        if not os.path.exists(dst_dir):
            os.mkdir(dst_dir)
        dst_filename = os.path.basename(src_file)
        dst_file = os.path.join(dst_dir, dst_filename)

        if os.path.exists(dst_file):
            print(f"WARNING - destination file already exists - {dst_file}")
            continue

        if args.dry_run:
            if args.copy:
                print(f"Would copy {src_file} to {dst_file}")
            else:
                print(f"Would move {src_file} to {dst_file}")
        else:
            if args.copy:
                print(f"Copy {src_file} to {dst_file}")
                shutil.copyfile(src_file, dst_file)
            else:
                print(f"Move {src_file} to {dst_file}")
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
    args = arg_parser.parse_args()
    _main()

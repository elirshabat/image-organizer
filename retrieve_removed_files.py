from argparse import ArgumentParser
import re
from tqdm import tqdm
import os
import shutil


def _main():
    log_file = args.log_file
    
    with open(log_file, 'rt') as f:
        content = f.read()
    
    lines = content.splitlines()

    pattern = r"image_organizer - INFO - Remove \'(.+)\' - duplicate of \'(.+)\'"

    for curr_line in tqdm(lines, desc="Iterating over log lines"):
        m = re.search(pattern, curr_line)
        if m is not None:
            dst_file = m.group(1)
            src_file = m.group(2)
            dst_dir = os.path.abspath(os.path.dirname(dst_file))
            os.makedirs(dst_dir, exist_ok=True)
            shutil.copyfile(src_file, dst_file)


if __name__ == '__main__':
    arg_parser = ArgumentParser(description="Retrive files that was removed during organization using the given log file")
    arg_parser.add_argument("log_file", help="Organization's log file")
    args = arg_parser.parse_args()

    _main()

from argparse import ArgumentParser
import os
from mediaorg.utils import create_logger
from mediaorg.index import LOGGER_NAME, LOGGER_FILENAME, update_index, create_index


def _main():
    repo_dir = args.repo_dir

    logs_dir = args.logs_dir if args.logs_dir is not None else os.path.join(repo_dir, ".logs")
    if not os.path.exists(logs_dir):
        os.mkdir(logs_dir)

    log_file = os.path.join(logs_dir, LOGGER_FILENAME)
    create_logger(log_file, LOGGER_NAME)

    index_path = os.path.join(repo_dir, ".index")

    if os.path.exists(index_path):
        update_index(repo_dir, show_progress=True)
    else:
        create_index(repo_dir)


if __name__ == '__main__':
    arg_parser = ArgumentParser(description="Create or update the repo index")
    arg_parser.add_argument("repo_dir", help="Path to the organized repository")
    arg_parser.add_argument("--logs-dir", help="Path to logs directory")
    args = arg_parser.parse_args()

    _main()

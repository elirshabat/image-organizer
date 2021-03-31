from mediaorg.utils import file_hash, list_media_files, get_logger, list_new_media_files, is_path_in_list, order_files
from tqdm import tqdm
import filecmp
import json
from datetime import datetime
import os


TIME_FORMAT = "%d/%m/%Y %H:%M:%S.%f"
LOGGER_NAME = "index"
LOGGER_FILENAME = f"{LOGGER_NAME}.log"


def find_file(filepath, repo_dir, hash_dict, digest=None):
    """
    Checks if a file already exists in the repo.
    :param filepath: File to check.
    :param repo_dir: Repo directory.
    :param hash_dict: Hash dict.
    :param digest: Digest of the input file (optional).
    :return: Relative path to the file if it exists and None otherwise.
    """
    if digest is None:
        digest = file_hash(filepath)

    if digest in hash_dict:
        for f in hash_dict[digest]:
            candidate_file = os.path.join(repo_dir, f)
            if filecmp.cmp(filepath, candidate_file):
                return f

    return None


def _add_repo_file_to_index(filepath, repo_dir, hash_dict, meta):
    """
    Adds the input file to the index.
    Note: the  input file must be contained in the repo.
    """
    logger = get_logger(LOGGER_NAME)

    rel_path = os.path.relpath(filepath, repo_dir)
    if ".." in rel_path:
        msg = f"Tried adding a non-repo file to index = path='{filepath}'"
        logger.error(msg)
        raise IOError(msg)

    digest = file_hash(filepath)
    if digest not in hash_dict:
        logger.info(f"Add file to index - file='{rel_path}' digest={digest}")
        hash_dict[digest] = [rel_path]
        meta['counters']['num_files'] += 1

    elif is_path_in_list(rel_path, hash_dict[digest]):
        logger.warning(f"Attempted to index an already existing file - file='{rel_path}' digest={digest}")

    else:
        hash_dict[digest].append(rel_path)
        dup_file = find_file(filepath, repo_dir, hash_dict, digest=digest)
        if dup_file is not None:
            # TODO: consider solving duplicates here
            logger.warning(f"Identified duplicate file - file1='{dup_file}' file2='{rel_path}'")
        else:
            logger.info(f"Hash collision - files={hash_dict[digest]}")
            meta['counters']['num_collisions'] += 1


def _register_error_file(filepath, repo_dir, meta):
    rel_path = os.path.relpath(filepath, repo_dir)
    if not is_path_in_list(rel_path, meta['error_files']):
        get_logger(LOGGER_NAME).info(f"Register error file - '{rel_path}'")
        meta['error_files'].append(rel_path)
        meta['counters']['num_errors'] += 1


def _register_duplicate_file(filepath, repo_dir, meta):
    rel_path = os.path.relpath(filepath, repo_dir)
    if not is_path_in_list(rel_path, meta['duplicate_files']):
        get_logger(LOGGER_NAME).info(f"Register duplicate file - '{rel_path}'")
        meta['duplicate_files'].append(rel_path)
        meta['counters']['num_duplicates'] += 1


def _add_multiple_repo_files_to_index(hash_dict, meta, media_files, repo_dir, show_progress=False, progress_msg=None):
    logger = get_logger(LOGGER_NAME)

    progress_msg = progress_msg if progress_msg is not None else "Indexing files"

    files_iterator = tqdm(media_files, desc=progress_msg) if show_progress else media_files
    for filepath in files_iterator:
        try:
            _add_repo_file_to_index(filepath, repo_dir, hash_dict, meta)

        except:
            logger.error(f"Failed to process a file - file='{filepath}'")
            _register_error_file(filepath, repo_dir, meta)


def _save_index(repo_dir, hash_dict, meta):
    index_path = os.path.join(repo_dir, ".index")

    hash_file = os.path.join(index_path, "hash.json")
    with open(hash_file, 'wt') as f:
        json.dump(hash_dict, f, indent=4, sort_keys=True)

    meta_file = os.path.join(index_path, "meta.json")
    with open(meta_file, 'wt') as f:
        json.dump(meta, f, indent=4, sort_keys=True)


def load_index(repo_dir):
    index_path = os.path.join(repo_dir, ".index")

    hash_file = os.path.join(index_path, "hash.json")
    with open(hash_file, 'rt') as f:
        hash_dict = json.load(f)

    meta_file = os.path.join(index_path, "meta.json")
    with open(meta_file, 'rt') as f:
        meta = json.load(f)

    return hash_dict, meta


def create_index(repo_dir):
    index_path = os.path.join(repo_dir, ".index")
    if os.path.exists(index_path):
        raise IOError(f"Cannot create index - already exists under '{index_path}'")

    logger = get_logger(LOGGER_NAME)
    os.mkdir(index_path)

    logger.info(f"Start creating index under '{index_path}'")

    media_files = list_media_files(repo_dir, show_progress=True)

    now = datetime.now()
    meta = dict()
    meta['last_update_time'] = now.strftime(TIME_FORMAT)
    meta['counters'] = dict()
    meta['counters']['num_files'] = 0
    meta['counters']['num_collisions'] = 0
    meta['counters']['num_duplicates'] = 0
    meta['counters']['num_errors'] = 0
    meta['error_files'] = []
    meta['duplicate_files'] = []

    hash_dict = dict()
    _add_multiple_repo_files_to_index(hash_dict, meta, media_files, repo_dir,
                                      show_progress=True, progress_msg="Creating index")

    _update_duplicates(hash_dict, repo_dir, meta)

    _save_index(repo_dir, hash_dict, meta)
    logger.info(f"Saved index - path='{index_path}' last_update_time={meta['last_update_time']}")


def _is_error_file(filepath, repo_dir, meta):
    rel_path = os.path.relpath(filepath, repo_dir)
    return is_path_in_list(rel_path, meta['error_files'])


def _is_duplicate(filepath, repo_dir, hash_dict):
    digest = file_hash(filepath)
    if digest not in hash_dict:
        return False

    rel_paths = hash_dict[digest]
    if len(rel_paths) <= 1:
        return False

    curr_filename = os.path.relpath(filepath, repo_dir)
    for other_filename in rel_paths:
        if curr_filename != other_filename:
            other_path = os.path.join(repo_dir, other_filename)
            if filecmp.cmp(filepath, other_path) and order_files(filepath, other_path) == 2:
                return True

    return False


# TODO: make sure we know when the index is up-to-date and that we make sure it is up-to-date before taking an action
def _update_duplicates(hash_dict, repo_dir, meta):
    dups = []
    for digest, rel_paths in hash_dict.items():
        if len(rel_paths) > 1:
            for curr_filename in rel_paths:
                curr_path = os.path.join(repo_dir, curr_filename)
                if _is_duplicate(curr_path, repo_dir, hash_dict):
                    dups.append(curr_filename)

    meta['duplicate_files'] = dups
    meta['counters']['num_duplicates'] = len(meta['duplicate_files'])


def _remove_deleted_files_from_index(hash_dict, meta, repo_dir, show_progress=False, progress_msg=None):
    logger = get_logger(LOGGER_NAME)

    for digest, rel_paths in hash_dict.items():
        for file_i in range(len(rel_paths) - 1, -1, -1):
            r_path = rel_paths[file_i]
            full_path = os.path.join(repo_dir, r_path)
            if not os.path.exists(full_path):
                logger.info(f"Removed deleted file from index - '{r_path}'")
                del rel_paths[file_i]
                meta['counters']['num_files'] -= 1

        if len(rel_paths) == 0:
            del hash_dict[digest]


def _update_error_files(repo_dir, hash_dict, meta):
    logger = get_logger(LOGGER_NAME)

    error_files = meta['error_files']
    for i in range(len(error_files) - 1, -1, -1):
        r_path = error_files[i]
        full_path = os.path.join(repo_dir, r_path)
        if not os.path.exists(full_path):
            logger.info(f"Removed deleted error file - '{r_path}'")
            del error_files[i]
        else:
            try:
                _add_repo_file_to_index(full_path, repo_dir, hash_dict, meta)

            except:
                logger.error(f"Failed to recover error file - '{r_path}'")


def is_up_to_date(repo_dir):
    hash_dict, meta = load_index(repo_dir)
    last_update_time = datetime.strptime(meta['last_update_time'], TIME_FORMAT)
    ls = os.listdir(repo_dir)
    for dir_name in ls:
        if not dir_name.startswith("."):
            dir_path = os.path.join(repo_dir, dir_name)
            mtime = datetime.fromtimestamp(os.stat(dir_path).st_mtime)
            if mtime > last_update_time:
                return False
    return True


def update_index(repo_dir, show_progress=False, force=False):
    logger = get_logger(LOGGER_NAME)

    if not force and is_up_to_date(repo_dir):
        logger.info("Index is already up-to-date")
        return

    hash_dict, meta = load_index(repo_dir)

    last_update_time = datetime.strptime(meta['last_update_time'], TIME_FORMAT)
    now = datetime.now()

    new_media_files = list_new_media_files(repo_dir, last_update_time, show_progress=show_progress)
    _add_multiple_repo_files_to_index(hash_dict, meta, new_media_files, repo_dir,
                                      show_progress=show_progress, progress_msg="Indexing new files")

    _remove_deleted_files_from_index(hash_dict, meta, repo_dir,
                                     show_progress=show_progress, progress_msg="Removing deleted files from index")

    _update_error_files(repo_dir, hash_dict, meta)
    _update_duplicates(hash_dict, repo_dir, meta)

    meta['last_update_time'] = now.strftime(TIME_FORMAT)

    _save_index(repo_dir, hash_dict, meta)
    logger.info(f"Done updating index = last_update_time={meta['last_update_time']}")

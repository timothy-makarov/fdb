#!/usr/bin/env python


import argparse
import binascii
import csv
import hashlib
import io
import logging
import os
import platform

from datetime import datetime


BUFFER_SIZE = io.DEFAULT_BUFFER_SIZE

ENCODING = 'utf8'

DELIMITER = ','

COLUMNS = [
    'filename',
    'extension',
    'created',
    'modified',
    'size',
    'hash'
]


def setup_logging(log_level, log_format):
    level = logging.getLevelName(log_level)
    logging.basicConfig(level=level, format=log_format)


def setup_args():
    parser = argparse.ArgumentParser(
        description='fdb - File Database Utility'
    )
    parser.add_argument(
        '--log-level',
        default='WARNING',
        help='desired log level'
    )
    parser.add_argument(
        '--log-format',
        default='%(asctime)s - %(levelname)s - %(message)s',
        help='desired log message format'
    )
    parser.add_argument(
        '--ignore',
        default='',
        type=lambda x: [
            bytes(y, ENCODING).decode('unicode_escape') for y in x.split(',')
        ],
        help='comma delimited list of files to ignore ' +
             '(supports escape characters)'
    )

    subparsers = parser.add_subparsers(
        help='commands'
    )

    # mk
    mk_parser = subparsers.add_parser(
        'mk',
        help='make a file database from a specified directory'
    )
    mk_parser.add_argument(
        'input_directory',
        help='directory to make a file database for'
    )
    mk_parser.add_argument(
        'output_file',
        help='output file with a file database'
    )
    mk_parser.set_defaults(which='mk')

    # fd
    fd_parser = subparsers.add_parser(
        'fd',
        help='find duplicates in a file database using file hashes'
    )
    fd_parser.add_argument(
        'input_file',
        help="input CSV file with a file database"
    )
    fd_parser.add_argument(
        'output_file',
        help='output file with a duplicate file database'
    )
    fd_parser.set_defaults(which='fd')

    # diff
    diff_parser = subparsers.add_parser(
        'diff',
        help='find diff between two databases'
    )
    diff_parser.add_argument(
        'source_db',
        help='CSV file with a file database of the source directory'
    )
    diff_parser.add_argument(
        'destination_db',
        help='CSV file with a file database of the destination directory'
    )
    diff_parser.add_argument(
        'output_file',
        help='output file with a diff database'
    )
    diff_parser.set_defaults(which='diff')

    # hd
    hd_parser = subparsers.add_parser(
        'hd',
        help='compute hash of all directory contents'
    )
    hd_parser.add_argument(
        'directory',
        help='directory to compute hash of'
    )
    hd_parser.set_defaults(which='hd')

    # hdb
    hdb_parser = subparsers.add_parser(
        'hdb',
        help='compute hash of all file database contents'
    )
    hdb_parser.add_argument(
        'input_file',
        help="input CSV file with a file database"
    )
    hdb_parser.set_defaults(which='hdb')

    args = parser.parse_args()
    return args


def hash_file(path):
    hasher = hashlib.md5()
    with open(path, 'rb') as afile:
        buff = afile.read(BUFFER_SIZE)
        while len(buff) > 0:
            hasher.update(buff)
            buff = afile.read(BUFFER_SIZE)
    digest = hasher.digest()
    return digest


def bin2str(barray):
    return binascii.hexlify(barray).decode(ENCODING)


def get_file_list(directory, ignore):
    if (not ignore):
        raise ValueError('Ignore list is none!')
    logging.info('Scanning directory: {}'.format(directory))
    file_list = []
    for root, dirs, files in os.walk(directory):
        logging.info('Scanning contents: {}'.format(root))
        logging.info('Found files: {}'.format(len(files)))
        for fn in files:
            if (fn in ignore):
                continue
            file_name = os.path.join(root, fn)
            file_list.append(file_name)
    return file_list


def create_db(directory, ignore):
    logging.info('Creating database for directory: {}'.format(directory))
    db = []
    file_list = get_file_list(directory, ignore)
    inx = 0
    list_length = len(file_list)
    logging.info('Number of files in directory: {}'.format(list_length))
    for file_name in file_list:
        logging.info(
            'Processing ({}/{}, {:.2f}%) file: {}'.format(
                inx + 1, list_length, (inx + 1) / list_length * 100, file_name
            )
        )
        try:
            file_ext = os.path.splitext(file_name)[1]
            file_stat = os.stat(file_name)
            file_ct = datetime.fromtimestamp(file_stat.st_ctime)
            file_mt = datetime.fromtimestamp(file_stat.st_mtime)
            file_size = file_stat.st_size
            file_hash = bin2str(hash_file(file_name))
            db.append([
                file_name,
                file_ext,
                file_ct,
                file_mt,
                file_size,
                file_hash
            ])
            inx += 1
        except PermissionError:
            logging.warning('File permission error: {}'.format(file_name))
            db.append([
                file_name,
                'NA',
                'NA',
                'NA',
                'NA',
                'NA'
            ])
    if (inx != list_length):
        logging.warning(
            'Not all files were processed ({}/{})!'.format(inx, list_length)
        )
    return db


def mk(input_directory, output_file, ignore):
    if (not os.path.exists(input_directory)):
        raise ValueError('Path does not exist: {}'.format(input_directory))

    if (os.path.exists(output_file)):
        raise ValueError('File already exists: {}'.format(output_file))

    db = create_db(input_directory, ignore)
    logging.info('Number of rows in file database: {}'.format(len(db)))

    logging.info('Writing database to file: {}'.format(output_file))
    fout = open(output_file, 'w', encoding=ENCODING, newline='')
    fout_writer = csv.writer(fout, delimiter=DELIMITER)
    fout_writer.writerow(COLUMNS)
    fout_writer.writerows(db)
    fout.close()


def pack_hash_db(database):
    hash_db = {}
    for row in database:
        if (row['hash'] in hash_db):
            existing_occurrences = hash_db[row['hash']]
            existing_occurrences.append(row)
        else:
            new_occurrence = []
            new_occurrence.append(row)
            hash_db[row['hash']] = new_occurrence
    return hash_db


def unpack_hash_db(hash_db):
    database = []
    for key in hash_db:
        for row in hash_db[key]:
            database.append(row)
    return database


def find_duplicates(database):
    logging.info('Rows to look for duplicates: {}'.format(len(database)))
    hash_db = pack_hash_db(database)
    keys = list(hash_db.keys())
    for key in keys:
        count = len(hash_db[key])
        if (count == 1):
            hash_db.pop(key, None)
    duplicates = unpack_hash_db(hash_db)
    logging.info(
        'Number of duplicates: {} ({:.2f}%)'.format(
            len(duplicates),
            len(duplicates) / len(database) * 100
        )
    )
    return duplicates


def read_database(file_name):
    logging.info('Reading database from file: {}'.format(file_name))
    fin = open(file_name, 'r', encoding=ENCODING)
    fin_reader = csv.DictReader(fin)
    database = []
    for row in fin_reader:
        database.append(row)
    fin.close()
    return database


def write_database(database, file_name):
    logging.info(
        'Writing database with {} rows to file: {}'.format(
            len(database), file_name
        )
    )
    fout = open(file_name, 'w', encoding=ENCODING, newline='')
    fout_writer = csv.DictWriter(fout, fieldnames=COLUMNS, delimiter=DELIMITER)
    fout_writer.writeheader()
    fout_writer.writerows(database)
    fout.close()


def fd(input_file, output_file):
    if (not os.path.exists(input_file)):
        raise ValueError('Path does not exist: {}'.format(input_file))

    if (os.path.exists(output_file)):
        raise ValueError('File already exists: {}'.format(output_file))

    database = read_database(input_file)
    duplicates = find_duplicates(database)

    write_database(duplicates, output_file)


def diff(source_db, destination_db, output_file):
    if (not os.path.exists(source_db)):
        raise ValueError('Path does not exist: {}'.format(source_db))

    if (not os.path.exists(destination_db)):
        raise ValueError('Path does not exist: {}'.format(destination_db))

    if (os.path.exists(output_file)):
        raise ValueError('File already exists: {}'.format(output_file))

    src_db = read_database(source_db)
    dst_db = read_database(destination_db)

    src_hash_db = pack_hash_db(src_db)
    dst_hash_db = pack_hash_db(dst_db)

    diff_db = []
    for src_key in src_hash_db:
        if (src_key in dst_hash_db):
            continue
        inx = 0
        for row in src_hash_db[src_key]:
            diff_db.append(row)
            inx += 1
        if (inx != 1):
            logging.warning(
                'Duplicates were found in source database: {} ({})'.format(
                    source_db, src_key
                )
            )
    logging.info('Files in diff: {}'.format(len(diff_db)))

    write_database(diff_db, output_file)


def hd(directory, ignore):
    if (not os.path.exists(directory)):
        raise ValueError('Path does not exist: {}'.format(directory))

    file_list = get_file_list(directory, ignore)
    list_length = len(file_list)
    logging.info("Number of files: {}".format(list_length))

    contents_digest = []
    inx = 0
    for file_name in file_list:
        logging.info(
            "Processing ({}/{}, {:.2f}%) file: {}".format(
                inx + 1, list_length, (inx + 1) / list_length * 100, file_name
            )
        )
        file_digest = hash_file(file_name)
        logging.info("{} *{}".format(bin2str(file_digest), file_name))
        contents_digest.extend(file_digest)
        inx += 1
    contents_digest.sort()
    hasher = hashlib.md5()
    hasher.update(bytes(contents_digest))
    directory_digest = hasher.hexdigest()
    print("{} *{} ({})".format(directory_digest, directory, inx))


def hdb(input_file):
    if (not os.path.exists(input_file)):
        raise ValueError("Path does not exist: {}".format(input_file))

    db = read_database(input_file)

    contents_digest = []
    for row in db:
        file_hash = row["hash"]
        file_digest = binascii.unhexlify(file_hash)
        contents_digest.extend(file_digest)
    contents_digest.sort()
    hasher = hashlib.md5()
    hasher.update(bytes(contents_digest))
    db_digest = hasher.hexdigest()
    print("{} *{} ({})".format(db_digest, input_file, len(contents_digest)))


def hook_convenience(args):
    curros = platform.system()
    if (curros == "Darwin"):
        if (args.ignore == [""]):
            ans = input(
                "Detected macOS: " +
                "Exclude files '.DS_Store' and 'Icon' from search? (y/n)" +
                "\n> "
            )
            if (ans.lower() == "y"):
                args.ignore = ".DS_Store,Icon\r"
            return args
    return args


def main():
    args = setup_args()
    setup_logging(args.log_level, args.log_format)
    args = hook_convenience(args)
    logging.info(args)

    if ("which" not in args):
        raise ValueError("Command not specified!")

    if (args.which == "mk"):
        mk(args.input_directory, args.output_file, args.ignore)
    elif (args.which == "fd"):
        fd(args.input_file, args.output_file)
    elif (args.which == "diff"):
        diff(args.source_db, args.destination_db, args.output_file)
    elif (args.which == "hd"):
        hd(args.directory, args.ignore)
    elif (args.which == "hdb"):
        hdb(args.input_file)
    else:
        raise ValueError('Unknown command!')


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        logging.critical(e)

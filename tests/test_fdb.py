from .. import fdb


def test_hash_file_1():
    file_name = 'tests/md5_test_file_1'
    file_hash = b'\xb0\x83\xdd@\xe1\xf2\xb4zS\r\x135\xfd\xd9\xa4\xbd'

    calc_hash = fdb.hash_file(file_name)

    assert calc_hash == file_hash


def test_hash_file_2():
    file_name = 'tests/md5_test_file_2'
    file_hash = b'gj\xeb\t\xec\xdb\xa9\xa0ac\xf6\x8a\x07\x0c\xd3\x17'

    calc_hash = fdb.hash_file(file_name)

    assert calc_hash == file_hash

# fdb

Utility for creating and working with file databases.


## Commands

mk      - make a file database from a specified directory.

fd      - find duplicates in a file database using file hashes.

diff    - find diff between two databases.

hd      - compute hash of all directory contents.

hdb     - compute hash of all file database contents.


## Usage

For finding duplicate files:

```
python fdb.py mk some_directory/ some_directory_db.csv

python fdb.py fd some_directory_db.csv  some_directory_db.d.csv
```

Print out the diff between the two databases:

```
python fdb.py diff source_db.csv destination_db.csv diff.csv
```

The obtained above diff file can be processed with the following Bash command:

```
tail -n +2 diff.csv | cut -d ',' -f1 | xargs -I % cp -p "%" some_destination_directory/
```

This will copy all the files that are missing in the destination_db.

## Notes

See help for information.
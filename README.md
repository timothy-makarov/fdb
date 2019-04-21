# fdb

Utility for creating and working with file databases.


## Commands

mk      - make a file database from a specified directory.

fd      - find duplicates in a file database using file hashes.

diff    - find diff between two databases.

hd      - compute hash of all directory contents.

hdb     - compute hash of all file database contents.


## Usage Example

For finding duplicate files:

```
python fdb.py mk some_directory/ some_directory_db.csv

python fdb.py fd some_directory_db.csv  some_directory_db.d.csv
```

Print out the diff between the two databases:

```
python fdb.py diff source_db.csv destination_db.csv diff.csv
```


## Notes

See help for information.
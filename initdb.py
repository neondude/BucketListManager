import sqlite3

try:
    conn = sqlite3.connect('BucketSuper.db')
    conn.execute("CREATE TABLE IF NOT EXISTS `userdb` (	`username`	TEXT,	`password`	TEXT NOT NULL,	PRIMARY KEY(`username`));")
    conn.execute("CREATE TABLE IF NOT EXISTS `BucketListItemDB` (	`username`	TEXT,	`ListID`	TEXT,	`ListItem`	TEXT);")
    conn.execute("CREATE TABLE IF NOT EXISTS `BucketListDB` (	`username`	TEXT,	`ListID`	TEXT);")
except Exception as e:
    print e

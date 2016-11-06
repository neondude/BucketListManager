CREATE TABLE `userdb` (
	`username`	TEXT,
	`password`	TEXT NOT NULL,
	PRIMARY KEY(`username`)
);

CREATE TABLE `BucketListItemDB` (
	`username`	TEXT,
	`ListID`	TEXT,
	`ListItem`	TEXT
);

CREATE TABLE `BucketListDB` (
	`username`	TEXT,
	`ListID`	TEXT
);
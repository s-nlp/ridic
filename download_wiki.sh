#!/bin/bash

mkdir -p wikidump

wget https://dumps.wikimedia.org/enwiki/latest/enwiki-latest-pagelinks.sql.gz
wget https://dumps.wikimedia.org/enwiki/latest/enwiki-latest-linktarget.sql.gz
wget https://dumps.wikimedia.org/zhwiki/latest/zhwiki-latest-pagelinks.sql.gz
wget https://dumps.wikimedia.org/zhwiki/latest/zhwiki-latest-linktarget.sql.gz

mv enwiki-latest-pagelinks.sql.gz wikidump/
mv enwiki-latest-linktarget.sql.gz wikidump/
mv zhwiki-latest-pagelinks.sql.gz wikidump/
mv zhwiki-latest-linktarget.sql.gz wikidump/

gzip -d wikidump/enwiki-latest-pagelinks.sql.gz wikidump/
gzip -d wikidump/enwiki-latest-linktarget.sql.gz wikidump/

gzip -d wikidump/zhwiki-latest-pagelinks.sql.gz wikidump/
gzip -d wikidump/zhwiki-latest-linktarget.sql.gz wikidump/

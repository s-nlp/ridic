#!/bin/bash

set -e

DATASET_TITLE=$1
OUTPUT_CSV=${DATASET_TITLE}_en_zh_full.json

#bash download_wiki.sh

if [ "$DATASET_TITLE" == "rivers" ]; then
  python dataset_dumper.py --dataset_path rivers.csv --output_dataset_path $OUTPUT_CSV --dataset_title $DATASET_TITLE
elif [ "$DATASET_TITLE" == "cars" ] || [ "$DATASET_TITLE" == "disasters" ]; then
  # For cars and disasters, we generate the initial CSV from a SPARQL query.
  # dataset_dumper.py needs a path for this initial file, which it will create.
  SPARQL_OUTPUT_CSV=${DATASET_TITLE}_sparql.csv
  python dataset_dumper.py --dataset_path $SPARQL_OUTPUT_CSV --output_dataset_path $OUTPUT_CSV --dataset_title $DATASET_TITLE --no-sparql-dataset-cache
else
  python dataset_dumper.py --dataset_path ${DATASET_TITLE}.csv --output_dataset_path $OUTPUT_CSV --dataset_title $DATASET_TITLE
fi

python dataset_popularity_sampler.py --dataset_path $OUTPUT_CSV --dataset_title $DATASET_TITLE
python information_gatherer.py --dataset_title $DATASET_TITLE
python link_crawler.py --dataset_title $DATASET_TITLE --output_path 1000_${DATASET_TITLE}_final.json

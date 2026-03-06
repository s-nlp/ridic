#!/bin/bash


python3 dataset_llm_gen.py --dataset_path datasets/1000_cars.json --dataset_title cars
python3 dataset_llm_gen.py --dataset_path datasets/1000_disasters.json --dataset_title 1000_disasters
python3 dataset_llm_gen.py --dataset_path datasets/1000_rivers.json --dataset_title 1000_rivers

import argparse
import csv
import json
import random

from joblib import Memory


def divide_dataset(sorted_items):
    total_popularity = 0
    for item in sorted_items:
        total_popularity += int(item['page_view'])

    cummul_popularity = 0
    items_by_levels = {
        0: [],
        1: [],
        2: []
    }
    amounts = {
        0: 0,
        1: 0,
        2: 0
    }
    cummul_popularity_total = {
        0: 0,
        1: 0,
        2: 0
    }
    total = 0
    for item in sorted_items:
        total += 1
        cummul_popularity += int(item['page_view'])
        popularity_part = 100 * cummul_popularity / total_popularity
        popularity_part_sector = int(popularity_part) // 33
        popularity_part_sector = popularity_part_sector if popularity_part_sector < 2 else 2
        cummul_popularity_total[popularity_part_sector] += int(item['page_view'])
        item["popularity_part_sector"] = popularity_part_sector
        items_by_levels[popularity_part_sector].append(item)
        amounts[popularity_part_sector] += 1

    print(f"Amount of items by popularity, high: {amounts[0]}, medium: {amounts[1]}, low: {amounts[2]}")
    ratio_by_popularity = [
        cummul_popularity_total[0] / total_popularity * 100,
        (cummul_popularity_total[0] + cummul_popularity_total[1]) / total_popularity * 100,
        (cummul_popularity_total[0] + cummul_popularity_total[1] + cummul_popularity_total[2]) / total_popularity * 100
    ]
    print(f"Ratio of items by popularity, high: {ratio_by_popularity[0]}%, medium: {ratio_by_popularity[1]}%, low: {ratio_by_popularity[2]}%")

    for level, items in items_by_levels.items():
        for item in items:
            item_continent_wdid = item['continent_wdid']
            if item_continent_wdid != '' and item_continent_wdid is not None:
                item['world_part'] = world_wdid_to_world[item_continent_wdid]
            else:
                item['world_part'] = ''

    return items_by_levels[0], items_by_levels[1], items_by_levels[2]


def get_random_elements(arr, n, allow_duplicates=False):
    """
    Returns `n` random elements from the array.

    Args:
        arr (list): The input array.
        n (int): Number of elements to return.
        allow_duplicates (bool): If True, allows duplicates when n > len(arr).

    Returns:
        list: Randomly selected elements.
    """
    if n <= 0 or len(arr) == 0:
        return []

    if allow_duplicates:
        # Allows duplicates via random.choices()
        return random.choices(arr, k=n)
    else:
        # Ensures no duplicates via random.sample()
        n = min(n, len(arr))  # Avoid exceeding array length
        return random.sample(arr, n)


location = './cachedir'
memory = Memory(location, verbose=0)

world_wdid_to_world = {
    'Q48': "Asia",
    'Q46': "Europe",
    'Q15': "Africa",
    'Q18': "South America",
    'Q55643': "Australia and Oceania",
    'Q538': "Australia and Oceania",
    'Q3960': "Australia and Oceania",
    'Q49': "North America",
    'Q5401': "Europe",  # Eurasia for russian empire
}

dataset_title_to_parts_list = {
    "cars": ["North America", "Europe", "Asia"],
    "rivers": ["North America", "Europe", "Asia", "Africa"],
    "disasters": ["North America", "Europe", "Asia", "Africa"],
    "other": ["North America", "Europe", "Asia", "Africa"]
}


def process_dataset(
    dataset_path,
    dataset_title,
    reuse_dataset
):
    if not reuse_dataset:
        dataset = []
        with open(dataset_path, 'r', encoding='utf8') as f:
            if '.csv' in dataset_path:
                reader = csv.DictReader(f)
                for row in reader:
                    dataset.append(row)
            else:
                dataset = json.load(f)

        # drop all items with redirects
        dataset_without_redirects = list(filter(lambda x: x['redirect_to'] == '' or x['redirect_to'] is None, dataset))
        # drop all items with disambiguation
        dataset_without_disamb = list(filter(lambda x: x['is_disambiguation'] == False or x['is_disambiguation'] == 'False', dataset_without_redirects))
        # drop all items without en wiki page views popularity
        dataset_with_popularity = list(filter(lambda x: x['page_view'] != '' and x['page_view'] is not None, dataset_without_disamb))

        # divide dataset by popularity
        sorted_dataset = sorted(dataset_with_popularity, key=lambda x: -int(x['page_view']))
        top_items, medium_items, low_items = divide_dataset(sorted_dataset)
        with open("dataset_divided_popularity_level.csv", 'w', encoding='utf8', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=sorted_dataset[0].keys())
            writer.writeheader()
            writer.writerows(sorted_dataset)

        # Gather data for hystogram of content min size
        wiki_min_length = {
            "0": {},
            "1": {},
            "2": {},
        }
        for item in dataset_with_popularity:
            popularity_part = str(item["popularity_part_sector"])
            if (item['is_stub'] == 'False' or item['is_stub'] == False) and (item['is_disambiguation'] == 'False' or item['is_disambiguation'] == False):
                river_content_group = int(item['content_min_size']) // 50
                key = f"{river_content_group * 50}-{(river_content_group + 1) * 50}"
                if key not in wiki_min_length[popularity_part]:
                    wiki_min_length[popularity_part][key] = 0
                wiki_min_length[popularity_part][key] += 1
        print(wiki_min_length)

        # random selection
        top_items_requested_size = 100
        # drop all items without chinese title
        top_items = list(filter(lambda x: x['title_zh'] != '' and x['title_zh'] is not None, top_items))
        # drop stub pages
        top_items = list(filter(lambda x: x['is_stub'] == False or x['is_stub'] == 'False', top_items))
        top_items_selected = get_random_elements(top_items, top_items_requested_size)

        medium_items_requested_size = 200
        medium_items_selected = []
        # drop all items without chinese title
        medium_items = list(filter(lambda x: x['title_zh'] != '' and x['title_zh'] is not None, medium_items))
        # drop stub pages
        medium_items = list(filter(lambda x: x['is_stub'] == False or x['is_stub'] == 'False', medium_items))
        for world_part in ["North America", "Europe", "Asia", "Africa"]:
            allowed_parts = [world_part]
            if world_part == "North America":
                allowed_parts.append("South America")
            elif world_part == "Asia":
                allowed_parts.append("Australia and Oceania")
            items_by_part = list(filter(lambda x: x['world_part'] in allowed_parts, medium_items))
            selection = get_random_elements(items_by_part, medium_items_requested_size // 4)
            medium_items_selected.extend(selection)
        if len(medium_items_selected) < medium_items_requested_size and len(medium_items) > len(medium_items_selected):
            extra_required = min(
                len(medium_items) - len(medium_items_selected),
                medium_items_requested_size - len(medium_items_selected)
            )
            # here country leaks -- can be null
            choice_source = [i for i in medium_items if i not in medium_items_selected]
            extra_selection = get_random_elements(choice_source, extra_required)
            medium_items_selected.extend(extra_selection)

        low_items_selected = []
        # drop all items without chinese title
        low_items = list(filter(lambda x: x['title_zh'] != '' and x['title_zh'] is not None, low_items))
        # drop stub pages
        low_items = list(filter(lambda x: x['is_stub'] == False or x['is_stub'] == 'False', low_items))
        # drop super short pages
        low_items = list(filter(lambda x: int(x['content_min_size']) >= 200, low_items))
        low_items_requested_size = 1000 - len(top_items_selected) - len(medium_items_selected)
        world_part_list_key = dataset_title if dataset_title in dataset_title_to_parts_list else 'other'
        for world_part in dataset_title_to_parts_list[world_part_list_key]:
            allowed_parts = [world_part]
            if world_part == "North America":
                allowed_parts.append("South America")
            elif world_part == "Asia":
                allowed_parts.append("Australia and Oceania")
            items_by_part = list(filter(lambda x: x['world_part'] in allowed_parts, low_items))
            selection = get_random_elements(items_by_part, low_items_requested_size // len(dataset_title_to_parts_list[world_part_list_key]))
            low_items_selected.extend(selection)
        if len(low_items_selected) < low_items_requested_size and len(low_items) > len(low_items_selected):
            extra_required = min(
                len(low_items) - len(low_items_selected),
                low_items_requested_size - len(low_items_selected)
            )
            choice_source = [i for i in low_items if i not in low_items_selected]
            extra_selection = get_random_elements(choice_source, extra_required)
            low_items_selected.extend(extra_selection)

        print(f"Ratio of sampled items for 1000 (10%-20%-70%): high: {len(top_items_selected) / 1000 * 100}, medium: {len(medium_items_selected) / 1000 * 100}, low: {len(low_items_selected) / 1000 * 100}")
        total_dataset = top_items_selected + medium_items_selected + low_items_selected

        with open(f"1000_{dataset_title}_without_llm_equal_world_parts.csv", 'w', encoding='utf8', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=total_dataset[0].keys())
            writer.writeheader()
            writer.writerows(total_dataset)

    total_dataset = []
    with open(f"1000_{dataset_title}_without_llm_equal_world_parts.csv", 'r', encoding='utf8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            total_dataset.append(row)

    # Drop extra fields
    for item in total_dataset:
        if "description_zh" in item:
            del item["description_zh"]
        if "item" in item:
            del item["item"]
        if "itemLabel" in item:
            del item["itemLabel"]
        if "wikipedia_url" in item:
            del item["wikipedia_url"]
        if "redirect_to" in item:
            del item["redirect_to"]
        if "page_size_bytes" in item:
            del item["page_size_bytes"]
        if "page_size_words" in item:
            del item["page_size_words"]
        if "incoming_links" in item:
            del item["incoming_links"]
        if "is_stub" in item:
            del item["is_stub"]
        if "content_min_size" in item:
            del item["content_min_size"]
        if "is_disambiguation" in item:
            del item["is_disambiguation"]

    with open(f"1000_{dataset_title}_without_refs.json", 'w', encoding='utf8') as f:
        json.dump(total_dataset, f, indent=2, ensure_ascii=False)


def create_parser():
    parser = argparse.ArgumentParser(
        description='Build rivers wikipedia popularity dataset',
    )
    parser.add_argument(
        '--dataset_path',
        type=str,
        help='path to the original rivers dataset in csv format with wikidata urls'
    )
    parser.add_argument(
        '--dataset_title',
        type=str,
        help='title of the dataset with enitity types',
        default='rivers'
    )
    parser.add_argument(
        '--reuse-dataset',
        action='store_true',
        help='Load cached dataset of 1000 rivers'
    )
    return parser


if __name__ == "__main__":
    parser = create_parser()
    args = parser.parse_args()
    process_dataset(
        dataset_path=args.dataset_path,
        dataset_title=args.dataset_title,
        reuse_dataset=args.reuse_dataset
    )
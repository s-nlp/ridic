import csv
import itertools
import json
import os
import sys

import argparse
import requests
import tqdm

from joblib import Memory

location = './cachedir'
memory = Memory(location, verbose=0)


@memory.cache()
def get_wikipedia_page_content_by_title(urls, language):
    url = f"https://{language}.wikipedia.org/w/api.php"
    params = {
        "action": "query",
        "format": "json",
        "titles": '|'.join(urls),
        "prop": "revisions",
        "rvprop": "content",
    }
    headers = requests.utils.default_headers()
    headers.update(
        {
            'User-Agent': "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36"
        }
    )
    try:
        response = requests.get(url, params=params, headers=headers)
        response.raise_for_status()  # Raise exception for HTTP errors
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Request failed: {e}")
        return None


@memory.cache()
def get_wikipedia_page_content_by_id(page_ids, language):
    url = f"https://{language}.wikipedia.org/w/api.php"
    params = {
        "action": "query",
        "format": "json",
        "pageids": '|'.join(page_ids),
        "prop": "revisions",
        "rvprop": "content",
    }
    headers = requests.utils.default_headers()
    headers.update(
        {
            'User-Agent': "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36"
        }
    )
    try:
        response = requests.get(url, params=params, headers=headers)
        response.raise_for_status()  # Raise exception for HTTP errors
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Request failed: {e}")
        return None


def batched(iterable, n):
    """
    Backport of itertools.batched() for Python < 3.12
    Split an iterable into tuples of size n. The last batch may be smaller.

    Example:
    >>> list(batched('ABCDEFG', 3))
    [('A', 'B', 'C'), ('D', 'E', 'F'), ('G',)]

    Args:
        iterable: An iterable to batch
        n: Batch size (must be positive integer)

    Yields:
        Tuples of size up to n containing items from the iterable
    """
    if n < 1:
        raise ValueError("n must be at least one")

    it = iter(iterable)
    while True:
        batch = tuple(itertools.islice(it, n))
        if not batch:
            return
        yield batch


def get_wiki_url_short(s, language):
    if not s.startswith(f'https://{language}.wikipedia.org/wiki/'):
        print(f'INCORRECT WIKI URL: {s}')
    return s[len(f'https://{language}.wikipedia.org/wiki/'):]


def get_wiki_url_page_id(s, language):
    if not s.startswith(f'https://{language}.wikipedia.org/?curid='):
        print(f'INCORRECT WIKI URL: {s}')
    return s[len(f'https://{language}.wikipedia.org/?curid='):]


def load_wiki_page(dataset, output_dir, info_languages):
    for language in info_languages:
        wiki_url_key = f"wikipedia_url_{language}"
        try:
            for item in dataset:
                if item[wiki_url_key] is not None and item[wiki_url_key] != '':
                    get_wiki_url_short(item[wiki_url_key], language)
            url_to_item = {get_wiki_url_short(item[wiki_url_key], language): item for item in dataset if item[wiki_url_key] is not None and item[wiki_url_key] != ''}
        except:
            print(item)
            raise
        for batch in tqdm.tqdm(batched(dataset, 50), total=len(dataset) // 50, desc='Gathering wiki pages'):
            items_urls = {get_wiki_url_short(item[wiki_url_key], language) for item in batch if item[wiki_url_key] is not None and item[wiki_url_key] != ''}
            if len(items_urls) == 0:
                continue
            response = get_wikipedia_page_content_by_title(items_urls, language)
            if "query" not in response or "pages" not in response["query"] or "-1" in response["query"]["pages"]:
                print(f"Errors in page size loading. {response}")

            normalizations = {}
            if "normalized" in response["query"]:
                for normalization in response["query"]["normalized"]:
                    normalizations[normalization["to"]] = normalization["from"]

            for page in response["query"]["pages"].values():
                title = page["title"]
                content = page["revisions"][0]["*"]
                title_normalized = title if title not in normalizations else normalizations[title]
                item = url_to_item[title_normalized]
                wd_id = item["wdid"].split('/')[-1]
                river_folder = os.path.join(output_dir, wd_id)
                with open(os.path.join(river_folder, f"wikipedia_page_{language}.txt"), 'w', encoding='utf8') as f:
                    f.write(content)


stat_dicts = {
    "incoming_links": {},
    "wiki_search": {}
}


def count_links_stats(item, links, link_type, language):
    popularity_part = item["popularity_part_sector"]
    stat_dict = stat_dicts[link_type]
    if language not in stat_dict:
        stat_dict[language] = {
            "-1": [],
            "0": [],
            "1": [],
            "2": []
        }
    stat_dict[language]['-1'].append(len(links))
    stat_dict[language][popularity_part].append(len(links))


def print_stats():
    for name, dict in stat_dicts.items():
        for language, lang_dict in dict.items():
            for popularity, links in lang_dict.items():
                total_count = sum(links)
                total_avg = total_count / (len(links) if len(links) != 0 else 1)
                print(f"{name}_{language}. Popularity: {popularity}: Total count: {total_count}, Total avg: {total_avg}")
            print("--------")


def load_wiki_page_content(links, language):
    result = {}
    for batch in batched(links, 50):
        page_ids = {get_wiki_url_page_id(item, language).split(",")[0] for item in batch}
        stub_by_id = {
            get_wiki_url_page_id(item, language).split(",")[0]:
                ("True" in get_wiki_url_page_id(item, language).split(",")[1] if len(get_wiki_url_page_id(item, language).split(",")) > 1 else False)
            for item in batch
        }
        response = get_wikipedia_page_content_by_id(page_ids, language)
        if "query" not in response or "pages" not in response["query"] or "-1" in response["query"]["pages"]:
            print(f"Errors in page size loading. {response}")

        if "continue" in response:
            print("Continue detected in incoming links loading")

        for page in response["query"]["pages"].values():
            page_id = str(page["pageid"])
            if 'revisions' in page:
                content = page["revisions"][0]["*"]
                result[page_id] = (stub_by_id[page_id], content)
            else:
                result[page_id] = (stub_by_id[page_id], "")

    return result


def load_incoming_links_wikipages(rivers, output_dir, info_languages):
    for language in info_languages:
        for river in tqdm.tqdm(rivers, total=len(rivers), desc='Gathering incoming links'):
            wd_id = river["wdid"].split('/')[-1]
            item_folder = os.path.join(output_dir, wd_id)
            links_source_filename = os.path.join(item_folder, f"wiki_pages_ref_to_this_{language}.txt")
            if not os.path.exists(links_source_filename):
                continue
            with open(links_source_filename, 'r', encoding='utf8') as f:
                incoming_links = list(map(lambda x: x.strip(), f.readlines()))

            count_links_stats(river, incoming_links, "incoming_links", language)
            result = load_wiki_page_content(incoming_links, language)
            incoming_links_folder = os.path.join(item_folder, f"incoming_links_content_{language}")
            if not os.path.exists(incoming_links_folder):
                os.makedirs(incoming_links_folder)
            for page_id, content in result.items():
                is_stub, text = content
                stub_title = "_stub" if is_stub else ""
                with open(os.path.join(incoming_links_folder, f"pageid_{page_id}{stub_title}.txt"), 'w', encoding='utf8') as f:
                    f.write(text)


def load_wiki_search_results(dataset, output_dir, info_languages):
    for language in info_languages:
        for item in tqdm.tqdm(dataset, total=len(dataset), desc='Gathering wiki search results'):
            wd_id = item["wdid"].split('/')[-1]
            item_folder = os.path.join(output_dir, wd_id)
            search_results_source_filename = os.path.join(item_folder, f"wiki_search_results_{language}.txt")
            if not os.path.exists(search_results_source_filename):
                continue
            with open(search_results_source_filename, 'r', encoding='utf8') as f:
                wiki_search_results_links = list(map(lambda x: x.strip(), f.readlines()))

            count_links_stats(item, wiki_search_results_links, "wiki_search", language)
            result = load_wiki_page_content(wiki_search_results_links, language)
            wiki_search_results_links_folder = os.path.join(item_folder, f"wiki_search_content_{language}")
            if not os.path.exists(wiki_search_results_links_folder):
                os.makedirs(wiki_search_results_links_folder)
            for page_id, content in result.items():
                is_stub, text = content
                stub_title = "_stub" if is_stub else ""
                with open(os.path.join(wiki_search_results_links_folder, f"pageid_{page_id}{stub_title}.txt"), 'w', encoding='utf8') as f:
                    f.write(text)


def dump_to_json(dataset, output_dir, info_languages, output_path):
    for item in tqdm.tqdm(dataset, total=len(dataset), desc='Dumping'):
        wdid = item["wdid"].split("/")[-1]
        item_folder = os.path.join(output_dir, wdid)

        for language in info_languages:
            incoming_links_file = os.path.join(item_folder, f"wiki_pages_ref_to_this_{language}.txt")
            item[f"incoming_links_{language}"] = []
            if os.path.exists(incoming_links_file):
                with open(incoming_links_file, "r", encoding='utf8') as f:
                    incoming_links = f.readlines()
                pages_incoming_links_folder = os.path.join(item_folder, f"incoming_links_content_{language}")
                for link in incoming_links:
                    link, is_stub = link.strip().split(",")
                    is_stub = "True" in is_stub
                    page_id = get_wiki_url_page_id(link, language)
                    filepath = os.path.join(pages_incoming_links_folder, f"pageid_{page_id}" + ("_stub" if is_stub else "") + ".txt")
                    with open(filepath, "r", encoding='utf8') as t:
                        text = t.read()
                    item[f"incoming_links_{language}"].append({
                        "page_id": page_id,
                        "is_stub": is_stub,
                        "content": text,
                    })

            wiki_search_file = os.path.join(item_folder, f"wiki_search_results_{language}.txt")
            item[f"wiki_search_results_{language}"] = []
            if os.path.exists(wiki_search_file):
                with open(wiki_search_file, "r", encoding='utf8') as f:
                    wiki_search_results = f.readlines()
                pages_wiki_search_folder = os.path.join(item_folder, f"wiki_search_content_{language}")
                for link in wiki_search_results:
                    page_id = get_wiki_url_page_id(link, language).strip()
                    filepath = os.path.join(pages_wiki_search_folder, f"pageid_{page_id}.txt")
                    with open(filepath, "r", encoding='utf8') as t:
                        text = t.read()
                    item[f"wiki_search_results_{language}"].append({
                        "page_id": page_id,
                        "content": text,
                    })

    with open(output_path, 'w', encoding='utf8') as f:
        json.dump(dataset, f)


def process_dataset(dataset_filename, output_dir, info_languages, output_path):
    dataset = []
    with open(dataset_filename, 'r', encoding='utf8') as f:
        dataset = json.load(f)

    # river wikipedia page
    load_wiki_page(dataset, output_dir, info_languages)

    # river incoming wikipedia links
    load_incoming_links_wikipages(dataset, output_dir, info_languages)

    # wikipedia search results
    load_wiki_search_results(dataset, output_dir, info_languages)

    # dump to json
    dump_to_json(dataset, output_dir, info_languages, output_path)

    print_stats()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description='This script gathers links to the item wikipage, pages that links to it and wiki top-10 search results with title of the item wiki page as query',
    )

    parser.add_argument(
        '--dataset_title',
        type=str,
        help='Title of the dataset, e.g. "rivers", "cars", "disasters".'
    )
    parser.add_argument(
        '--output_path',
        type=str,
        default=f'./res.csv',
        help='Output path.'
    )

    args = parser.parse_args()

    process_dataset(f"1000_{args.dataset_title}_without_refs.json", f"./{args.dataset_title}_content", ['en', 'zh'], args.output_path)


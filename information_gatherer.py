import csv
import itertools
import json
import os
import argparse

import requests
import tqdm

from joblib import Memory

location = './cachedir'
memory = Memory(location, verbose=0)


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


@memory.cache()
def get_wikipedia_page_content(ids, language):
    url = f"https://{language}.wikipedia.org/w/api.php"
    params = {
        "action": "query",
        "format": "json",
        "pageids": '|'.join(ids),
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


def get_wikipedia_page_content_no_cache(ids, language):
    url = f"https://{language}.wikipedia.org/w/api.php"
    params = {
        "action": "query",
        "format": "json",
        "pageids": '|'.join(ids),
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
def get_wikipedia_page_props(ids, language):
    url = f"https://{language}.wikipedia.org/w/api.php"
    params = {
        "action": "query",
        "format": "json",
        "pageids": '|'.join(ids),
        "prop": "pageprops",
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


def get_wikipedia_page_props_no_cache(ids, language):
    url = f"https://{language}.wikipedia.org/w/api.php"
    params = {
        "action": "query",
        "format": "json",
        "pageids": '|'.join(ids),
        "prop": "pageprops",
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
def get_wikipedia_redirects(ids, language):
    url = f"https://{language}.wikipedia.org/w/api.php"
    params = {
        "action": "query",
        "format": "json",
        "pageids": '|'.join(ids),
        "redirects": "1"
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


def get_wikipedia_redirects_no_cache(ids, language):
    url = f"https://{language}.wikipedia.org/w/api.php"
    params = {
        "action": "query",
        "format": "json",
        "pageids": '|'.join(ids),
        "redirects": "1"
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
def get_wikipedia_titles(ids, language):
    url = f"https://{language}.wikipedia.org/w/api.php"
    params = {
        "action": "query",
        "format": "json",
        "pageids": '|'.join(ids),
        "prop": "info"
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


def get_wikipedia_titles_no_cache(ids, language):
    url = f"https://{language}.wikipedia.org/w/api.php"
    params = {
        "action": "query",
        "format": "json",
        "pageids": '|'.join(ids),
        "prop": "info"
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


def load_page_props(ids, language):
    response_content = get_wikipedia_page_content(ids, language)
    if response_content is None:
        response_content = get_wikipedia_page_content_no_cache(ids, language)
    response_props = get_wikipedia_page_props(ids, language)
    if response_props is None:
        response_props = get_wikipedia_page_props_no_cache(ids, language)
    response_redirs = get_wikipedia_redirects(ids, language)
    if response_redirs is None:
        response_redirs = get_wikipedia_redirects_no_cache(ids, language)
    response_titles = get_wikipedia_titles(ids, language)
    if response_titles is None:
        response_titles = get_wikipedia_titles_no_cache(ids, language)
    result = {}
    if "query" not in response_content or "pages" not in response_content["query"] or "-1" in response_content["query"]["pages"]:
        print(f"Errors in page content loading. {response_content}")
        return result
    if "query" not in response_props or "pages" not in response_props["query"] or "-1" in response_props["query"]["pages"]:
        print(f"Errors in page props loading. {response_props}")
        return result
    if "query" not in response_redirs or "pages" not in response_redirs["query"] or "-1" in response_redirs["query"]["pages"]:
        print(f"Errors in page redirects loading. {response_redirs}")
        return result
    if "query" not in response_titles or "pages" not in response_titles["query"] or "-1" in response_titles["query"]["pages"]:
        print(f"Errors in page redirects loading. {response_titles}")
        return result

    page_props = response_props["query"]["pages"]
    page_titles = response_titles["query"]["pages"]
    id_to_title = {str(item["pageid"]): item["title"] for item in page_titles.values() if "title" in item}
    for page in response_content["query"]["pages"].values():
        id = str(page["pageid"])
        redirs_dict = {item['from'] for item in response_redirs["query"]["redirects"]} if "redirects" in response_redirs["query"] else set()
        is_disamb = id in page_props and "pageprops" in page_props[id] and "disambiguation" in page_props[id]["pageprops"]
        if id not in id_to_title:
            print(f"ALARM: {id}")
            is_redirect = True  # bad page
        else:
            is_redirect = id_to_title[id] in redirs_dict
        if "missing" not in page:
            content = page["revisions"][0]["*"]
            is_stub = "-stub}}" in content.lower()
            is_disambiguation = "{{disamb" in content.lower()
            if not is_disamb and is_disambiguation:
                print(f"ALARM: {page_props[id]}\n-------------\n{content}")
        else:
            is_stub = True
        result[str(id)] = (is_stub, is_disamb, is_redirect)

    return result


def gather_incoming_pagelinks(dataset, dataset_title, linktarget_path, pagelinks_path, language, disable_links_cache):
    wiki_url_key = f"wikipedia_url_{language}"
    items_urls = {get_wiki_url_short(item[wiki_url_key], language) for item in dataset if item[wiki_url_key] is not None and item[wiki_url_key] != ''}
    dataset_items_total = []
    try:
        if disable_links_cache:
            raise Exception
        with open(f"links_index_{dataset_title}_{language}.json", 'r', encoding='utf8') as f:
            links_index = json.load(f)
        print("Used cache instead of loading links targets from wikipedia dump!")
    except:
        with open(linktarget_path, 'r', encoding='utf-8') as file:
            for line in tqdm.tqdm(file, desc='Loading links targets'):
                if not line.startswith("INSERT INTO"):
                    continue
                line_items = line[len("INSERT INTO `linktarget` VALUES "):].split("'),(")
                dataset_items = []
                for item in line_items:
                    subitems = item.split(",")
                    title = ",".join(subitems[2:])
                    if title.endswith("')"):
                        item = item[:-2]
                        title = title[1:-2]
                    else:
                        title = title[1:]
                    title = title.replace("\\'", "'")
                    if subitems[0].startswith('('):
                        item = item[1:]
                    if title in items_urls:
                        dataset_items.append(item)
                dataset_items_total += dataset_items

        links_index = {
            item.split(",")[0]: (item.split(",")[1], ",".join(item.split(",")[2:])[1:]) for item in dataset_items_total
        }

        with open(f"links_index_{dataset_title}_{language}.json", 'w', encoding='utf8') as f:
            json.dump(links_index, f)

    # Load links from wikipedia dump (only with targets in rivers with language wikipedia url!!!)
    try:
        if disable_links_cache:
            raise Exception
        with open(f"title_to_links_{dataset_title}_{language}.json", 'r', encoding='utf8') as f:
            title_to_links = json.load(f)
        print("Used cache instead of loading links from wikipedia dump!")
    except:
        title_to_links = {}
        with open(pagelinks_path, 'r', encoding='utf-8') as file:
            for line in tqdm.tqdm(file, desc='Loading links'):
                if not line.startswith("INSERT INTO"):
                    continue
                line_items = line[len("INSERT INTO `pagelinks` VALUES "):].split("),(")
                for index, item in enumerate(line_items):
                    if index == 0:
                        item = item[1:]
                    if item.endswith(")"):
                        item = item[:-1]
                    subitems = item.split(",")
                    from_id = subitems[0]
                    from_ns = subitems[1]
                    target_id = subitems[2]

                    if target_id not in links_index:
                        continue
                    ns, title = links_index[target_id]
                    if title not in title_to_links:
                        title_to_links[title] = {}
                    if ns not in title_to_links[title]:
                        title_to_links[title][ns] = []
                    title_to_links[title][ns].append((from_id, from_ns))

        with open(f"title_to_links_{dataset_title}_{language}.json", 'w', encoding='utf8') as f:
            json.dump(title_to_links, f)

    # Get links to each wikipedia page about item with en url (only links from NS=0 and for pages in NS=0)
    pages_with_incoming_links_amount = 0
    for item in tqdm.tqdm(dataset, desc='Gathering incoming'):
        item[f"wiki_pages_links_to_this_{language}"] = []

        if item[wiki_url_key] is None or item[wiki_url_key] == '':
            continue
        # gather incoming links only for rare ones
        if item["popularity_part_sector"] != "2":
            continue
        url = get_wiki_url_short(item[wiki_url_key], language)
        url_json_encoded = url.replace("'", "\\'")
        if url_json_encoded in title_to_links and '0' in title_to_links[url_json_encoded]:
            ns_0_links = list(filter(lambda x: x[1] == '0', title_to_links[url_json_encoded]['0']))
        elif url in title_to_links and '0' in title_to_links[url]:
            ns_0_links = list(filter(lambda x: x[1] == '0', title_to_links[url]['0']))
        else:
            ns_0_links = []
        if len(ns_0_links) > 0:
            pages_with_incoming_links_amount += 1

        for link_from_id, link_from_ns in ns_0_links:
            link_from_url = f"https://{language}.wikipedia.org/?curid={link_from_id}"
            item[f"wiki_pages_links_to_this_{language}"].append(link_from_url)

        # filter incoming links
        links_to_filter = item[f"wiki_pages_links_to_this_{language}"]
        filtered_links = []
        for batch in tqdm.tqdm(batched(links_to_filter, 50), total=len(links_to_filter) // 50, desc='Loading page props'):
            ids = list(map(lambda x: get_wiki_url_page_id(x, language), batch))
            props = load_page_props(ids, language)
            for link in batch:
                link_id = get_wiki_url_page_id(link, language)
                if not props[link_id][1] and not props[link_id][2]:
                    filtered_links.append((link, f"is_stub={props[link_id][0]}"))

        item[f"wiki_pages_links_to_this_{language}"] = filtered_links

    print(f"Totally {pages_with_incoming_links_amount} items with en wikipedia url has at least 1 incoming link")


@memory.cache
def wiki_search_request(query, language):
    url = f"https://{language}.wikipedia.org/w/api.php"
    params = {
        "action": "query",
        "list": "search",
        "format": "json",
        "srnamespace": 0,
        "srsearch": query,
        "srlimit": 20,
        "srinfo": "totalhits",
        "srenablerewrites": False,
        "srinterwiki": False,
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


def gather_wiki_search_results(dataset, language):
    wiki_url_key = f"wikipedia_url_{language}"
    for item in tqdm.tqdm(dataset, total=len(dataset), desc='Gathering wiki search results'):
        item[f"wiki_search_results_{language}"] = []
        if item[wiki_url_key] is None or item[wiki_url_key] == '':
            continue
        query = get_wiki_url_short(item[wiki_url_key], language).replace("_", " ")
        response = wiki_search_request(query, language)
        if "query" not in response or "search" not in response["query"]:
            print(f"Errors in wiki page search. {response}")
            continue
        for result_item in response["query"]["search"]:
            if result_item["title"] == query:
                continue
            page_id = result_item['pageid']
            item[f"wiki_search_results_{language}"].append(f"https://{language}.wikipedia.org/?curid={page_id}")
            if len(item[f"wiki_search_results_{language}"]) == 10:
                break


def process_dataset(dataset_input_name: str, dataset_title: str, info_languages, output_dir, wikipedia_dump_path):
    dataset = []
    with open(dataset_input_name, 'r', encoding='utf8') as f:
        reader = json.load(f)
        for row in reader:
            if 'llama3.1:8b' in row:
                del row['llama3.1:8b']
            if 'qwen2.5:7b' in row:
                del row['qwen2.5:7b']
            if 'qwen2.5:7b_zh' in row:
                del row['qwen2.5:7b_zh']
            dataset.append(row)

    # get duplicated items names
    items_names = {}
    duplicated_item_names = {}
    for language in info_languages:
        items_names[language] = {}
        duplicated_item_names[language] = []
        for item in dataset:
            if item[f'title_{language}'] not in items_names:
                items_names[language][item[f'title_{language}']] = []
                items_names[language][item[f'title_{language}']].append(item)
        for item_name, items_t in items_names[language].items():
            if len(items_t) < 2:
                continue
            duplicated_item_names[language].append(item_name)
            print(f"{item_name}: {len(items_t)}")

        # gather wikipedia search results
        gather_wiki_search_results(
            dataset,
            language=language,
        )

        # gather incoming pagelinks
        gather_incoming_pagelinks(
            dataset,
            dataset_title,
            linktarget_path=f'{wikipedia_dump_path}/{language}wiki-latest-linktarget.sql',
            pagelinks_path=f'{wikipedia_dump_path}/{language}wiki-latest-pagelinks.sql',
            language=language,
            disable_links_cache=True
        )

        # create folders
        for item in dataset:
            wd_id = item["wdid"].split('/')[-1]
            dir_name = os.path.join(output_dir, wd_id)
            if not os.path.exists(dir_name):
                os.makedirs(dir_name)
            with open(os.path.join(dir_name, f"wiki_pages_ref_to_this_{language}.txt"), 'w', encoding='utf8') as f:
                f.write("\n".join(list(map(lambda x: ",".join(x), item[f"wiki_pages_links_to_this_{language}"]))))
            with open(os.path.join(dir_name, f"wiki_search_results_{language}.txt"), 'w', encoding='utf8') as f:
                f.write("\n".join(item[f'wiki_search_results_{language}']))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description='This script downloads all links from the previous step.',
    )

    parser.add_argument(
        '--dataset_title',
        type=str,
        help='Title of the dataset, e.g. "rivers", "cars", "disasters".'
    )
    parser.add_argument(
        '--wikipedia_dump_path',
        type=str,
        default='./wikidump',
        help='Path to the wikipedia dump file'
    )

    args = parser.parse_args()
    process_dataset(f'1000_{args.dataset_title}_without_refs.json', args.dataset_title, ['en', 'zh'], f'./{args.dataset_title}_content', args.wikipedia_dump_path)

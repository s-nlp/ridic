import argparse
import csv
import itertools
import json
import re
import urllib
from urllib.parse import unquote

import requests
from bs4 import BeautifulSoup

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
import tqdm

from joblib import Memory
from wikipedia import wikipedia

location = './cachedir'
memory = Memory(location, verbose=0)

dataset_sparql = {
    "disasters": """?item wdt:P31/wdt:P279* wd:Q8065.""",
    "cars": """?item wdt:P31 wd:Q3231690.""",
    "rivers_sparql": """?item wdt:P31 wd:Q4022.""",
}
# for cars      wdt:P176/wdt:P17 ?country

@memory.cache()
def query_wikidata_entities(sparql_query: str):
    url = "https://query.wikidata.org/sparql"
    params = {
        'query': sparql_query,
        'format': 'json'
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
        # Successful response
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Request failed: {e}")
        return None


def query_wikidata_entities_no_cache(sparql_query: str):
    url = "https://query.wikidata.org/sparql"
    params = {
        'query': sparql_query,
        'format': 'json'
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
        # Successful response
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Request failed: {e}")
        return None


def load_dataset_from_sparql(item_condition: str, languages=("en", "zh")):
    if languages is None:
        languages = ["en", "zh"]
    langs_service = "".join([
        'SERVICE wikibase:label { bd:serviceParam wikibase:language "' + language + '" . ?item rdfs:label' + f" ?itemLabel{language} . " + ("?country rdfs:label ?countryLabelen ." if language == 'en' else "") + "}"
        for language in languages
    ])
    langs_select = " ".join([f"?itemLabel{language}" for language in languages])

    query = "SELECT ?item " + langs_select + " WHERE { " + item_condition + " " + langs_service + " }"

    query_encoded = query.replace("\n", " ")
    response = query_wikidata_entities(query_encoded)

    if "results" not in response or "bindings" not in response["results"]:
        print("Error when querying sparql dataset")

    # response = {
    #     "results": {
    #         "bindings": []
    #     }
    # }
    # with open("disasters.json", 'r', encoding='utf8') as f:
    #    response["results"]["bindings"] = json.load(f)

    fields = {
        "item": "wdid"
    }
    for language in languages:
        fields[f"itemLabel{language}"] = f"title_{language}"

    dataset = []
    existing_items = set()
    for binding in response["results"]["bindings"]:
        item = {}
        for field_source, field_dest in fields.items():
            item[field_dest] = binding[field_source]['value']
            if 'itemLabel' in field_source:
                item[field_dest] = item[field_dest] if item[field_dest] != get_wikidata_id_from_url(item['wdid']) else None
        if item['wdid'] not in existing_items:
            dataset.append(item)
            existing_items.add(item["wdid"])

    return dataset


@memory.cache()
def get_wikidata_entities(wikidata_ids, language='en', props='sitelinks/urls|labels|descriptions|claims'):
    """
    Fetches entity data from Wikidata API for given Wikidata IDs.

    Args:
        language: language to work with
        wikidata_ids (list): List of Wikidata IDs (e.g., ['Q42', 'Q1337'])

    Returns:
        dict: JSON response containing entity data or None if request fails
    """
    url = 'https://www.wikidata.org/w/api.php'

    headers = requests.utils.default_headers()
    headers.update(
        {
            'User-Agent': "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36"
        }
    )
    params = {
        'action': 'wbgetentities',
        'ids': '|'.join(wikidata_ids),
        'props': f'{props}',
        'languages': language,
        'languagefallback': '',
        'sitefilter': f'{language}wiki',
        'formatversion': '2',
        'format': 'json'
    }

    try:
        response = requests.get(url, params=params, headers=headers)
        response.raise_for_status()  # Raise exception for HTTP errors
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Request failed: {e}")
        return None


def get_wikidata_entities_no_cache(wikidata_ids, language='en', props='sitelinks/urls|labels|descriptions|claims'):
    """
    Fetches entity data from Wikidata API for given Wikidata IDs.

    Args:
        language: language to work with
        wikidata_ids (list): List of Wikidata IDs (e.g., ['Q42', 'Q1337'])

    Returns:
        dict: JSON response containing entity data or None if request fails
    """
    url = 'https://www.wikidata.org/w/api.php'
    headers = requests.utils.default_headers()
    headers.update(
        {
            'User-Agent': "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36"
        }
    )
    params = {
        'action': 'wbgetentities',
        'ids': '|'.join(wikidata_ids),
        'props': f'{props}',
        'languages': language,
        'languagefallback': '',
        'sitefilter': f'{language}wiki',
        'formatversion': '2',
        'format': 'json'
    }

    try:
        response = requests.get(url, params=params, headers=headers)
        response.raise_for_status()  # Raise exception for HTTP errors
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Request failed: {e}")
        return None


def get_pageviews(pagetile_id):
    def parse_table(html_content):
        soup = BeautifulSoup(html_content, 'html.parser')
        tbody = soup.find('tbody', id='output_list')

        if not tbody:
            return []

        rows = []
        for row in tbody.find_all('tr'):
            columns = row.find_all(['th', 'td'])
            # Extract numeric rank
            rank = int(columns[0].get_text(strip=True))

            # Extract article title and URL
            title_link = columns[1].find('a')
            title = title_link.get_text(strip=True) if title_link else None
            url = title_link['href'] if title_link else None

            # Extract total views (remove non-breaking spaces and commas)
            total_views_text = columns[2].get_text(strip=True)
            total_views = int(re.sub(r'\D', '', total_views_text)) if total_views_text else 0

            # Extract daily average (split value and unit)
            daily_text = columns[3].get_text(strip=True)
            daily_value = re.search(r'^([\d ]+)', daily_text)
            daily_average = int(re.sub(r'\D', '', daily_value.group(1))) if daily_value else 0

            rows.append({
                'rank': rank,
                'title': title,
                'url': url,
                'total_views': total_views,
                'daily_average': daily_average
            })

        return rows

    # Configure Chrome options for headless browsing
    chrome_options = Options()
    chrome_options.add_argument("--headless=new")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument(
        "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36"
    )

    # Initialize WebDriver (make sure chromedriver is in your PATH)
    driver = webdriver.Chrome(options=chrome_options)

    try:
        # Load the target page
        driver.get(
            f"https://pageviews.toolforge.org/massviews?source=pagepile&target={pagetile_id}&range=last-year&view=list")

        # Wait for initial page load and potential dynamic content
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "#output_list"))
        )

        # Additional wait for any JavaScript updates/animations
        time.sleep(10)  # Wait for 10 seconds as specified

        # Get the fully rendered HTML including JavaScript modifications
        full_html = driver.page_source
        parsed_data = parse_table(full_html)

    finally:
        driver.quit()

    return parsed_data


def get_pagetile(page_names, language):
    url = "https://pagepile.toolforge.org/index.php"

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:137.0) Gecko/20100101 Firefox/137.0",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "ru-RU,ru;q=0.8,en-US;q=0.5,en;q=0.3",
        "Accept-Encoding": "gzip, deflate, br, zstd",
        "Content-Type": "application/x-www-form-urlencoded",
        "Origin": "https://pagepile.toolforge.org",
        "Connection": "keep-alive",
        "Referer": "https://pagepile.toolforge.org/?menu=new",
        "Upgrade-Insecure-Requests": "1",
        "Sec-Fetch-Dest": "document",
        "Sec-Fetch-Mode": "navigate",
        "Sec-Fetch-Site": "same-origin",
        "Sec-Fetch-User": "?1",
        "Priority": "u=0, i",
        "Pragma": "no-cache",
        "Cache-Control": "no-cache",
        "TE": "trailers",
    }

    tmp = '\r\n'.join(page_names)
    data = {
        "language": language,
        "project": "wikipedia",
        "manual_list": tmp,
        "sparql": "",
        "pastebin": "",
        "contentmine": "",
        "quarry": "",
        "search_query": "",
        "search_query_ns": "",
        "doit": "%D0%92%D1%8B%D0%BF%D0%BE%D0%BB%D0%BD%D0%B8%D1%82%D1%8C%21",
    }
    try:
        response = requests.post(url, headers=headers, data=data)
        response.raise_for_status()  # Raise exception for HTTP errors
        tmp = response.text[response.text.index("ID is <b>") + len("ID is <b>"):response.text.index("ID is <b>") + len(
            "ID is <b>") + 10]
        pile_id = int(tmp[:tmp.index("</b>")])
        return pile_id
    except requests.exceptions.RequestException as e:
        print(f"Request failed: {e}")
        return None


@memory.cache()
def load_page_views(urls, language):
    pile_id = get_pagetile(urls, language)
    pageviews_data = get_pageviews(pile_id)
    return pageviews_data


def get_wikipedia_page_size_no_cache(urls, language):
    encoded_urls = urls
    url = f"https://{language}.wikipedia.org/w/api.php"
    params = {
        "action": "query",
        "format": "json",
        "titles": '|'.join(encoded_urls),
        "prop": "revisions",
        "rvprop": "size|content",
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
def get_wikipedia_page_size(urls, language):
    encoded_urls = urls
    url = f"https://{language}.wikipedia.org/w/api.php"
    params = {
        "action": "query",
        "format": "json",
        "titles": '|'.join(encoded_urls),
        "prop": "revisions",
        "rvprop": "size|content",
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
def get_wikipedia_page_valuable_text_size(url, language):
    encoded_url = url
    url = f"https://{language}.wikipedia.org/w/api.php"
    params = {
        "action": "query",
        "format": "json",
        "titles": encoded_url,
        "prop": "extracts",
        "exsentences": 10,
        "explaintext": 1,
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


def load_useful_content_min_size(url, language):
    response = get_wikipedia_page_valuable_text_size(url, language)
    if "query" not in response or "pages" not in response["query"] or "-1" in response["query"]["pages"]:
        print(f"Errors in page content min size loading. {response}")
        return -1

    page = list(response["query"]["pages"].values())[0]
    text = page["extract"]
    return len(text)


def load_page_size(urls, language):
    response = get_wikipedia_page_size(urls, language)
    result = {}
    if response is None:
        response = get_wikipedia_page_size_no_cache(urls, language)
    if "query" not in response or "pages" not in response["query"] or "-1" in response["query"]["pages"]:
        print(f"Errors in page size loading. {response}")
        return result

    normalizations = {}
    if "normalized" in response["query"]:
        for normalization in response["query"]["normalized"]:
            normalizations[normalization["to"]] = normalization["from"]

    for page in response["query"]["pages"].values():
        title = page["title"]
        byte_size = page["revisions"][0]["size"]
        content = page["revisions"][0]["*"]
        is_stub = "-stub}}" in content.lower()
        is_disambiguation = "{{disamb" in content.lower()
        words = content.split()
        title_normalized = title if title not in normalizations else normalizations[title]
        result[title_normalized] = (byte_size, len(words), is_stub, is_disambiguation)

    return result


@memory.cache()
def get_wikipedia_redirects(urls, language):
    encoded_urls = urls
    url = f"https://{language}.wikipedia.org/w/api.php"
    params = {
        "action": "query",
        "format": "json",
        "titles": '|'.join(encoded_urls),
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


def load_page_redirects(urls, language):
    response = get_wikipedia_redirects(urls, language)
    result = {}
    if "query" not in response or "pages" not in response["query"] or "-1" in response["query"]["pages"]:
        print(f"Errors in page redirects loading. {response}")
        return result

    if "redirects" not in response["query"]:
        return {}

    normalizations = {}
    if "normalized" in response["query"]:
        for normalization in response["query"]["normalized"]:
            normalizations[normalization["to"]] = normalization["from"]

    for redirect in response["query"]["redirects"]:
        redirect_from = redirect["from"] if redirect["from"] not in normalizations else normalizations[redirect["from"]]
        redirect_to = redirect["to"] if redirect["to"] not in normalizations else normalizations[redirect["to"]]
        result[redirect_from] = redirect_to.replace(" ", "_")

    return result


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


def get_wikidata_id_from_url(s):
    return s.split("/")[-1]


@memory.cache(ignore=["countries_no_continent", "continents", "need_country", "wiki_url_key", "items_by_wd_id"])
def get_country_and_continent(item, countries_no_continent, continents, need_country, key, wiki_url_key, items_by_wd_id):
    if items_by_wd_id[key][wiki_url_key] is not None and need_country and ('P17' in item['claims'] and 'datavalue' in item['claims']['P17'][0]['mainsnak'] or 'P176' in item['claims'] and 'datavalue' in item['claims']['P176'][0]['mainsnak']):
        if 'P176' in item['claims']:
            manufacturer_wd_id = item['claims']['P176'][0]['mainsnak']['datavalue']['value']['id']
            manufacturer_resp = get_wikidata_entities([manufacturer_wd_id], language='en', props='labels|claims')
            manufacturer_item = manufacturer_resp["entities"][manufacturer_wd_id]
            if 'claims' not in manufacturer_item:
                print(manufacturer_item)
                manufacturer_item['claims'] = {}
            if 'P17' in manufacturer_item['claims'] and 'datavalue' in manufacturer_item['claims']['P17'][0]['mainsnak']:
                country_wd_id = manufacturer_item['claims']['P17'][0]['mainsnak']['datavalue']['value']['id']
            else:
                country_wd_id = ""
        else:
            country_wd_id = item['claims']['P17'][0]['mainsnak']['datavalue']['value']['id']
        if country_wd_id != '':
            country_resp = get_wikidata_entities([country_wd_id], language='en', props='labels|claims')
            country_item = country_resp["entities"][country_wd_id]
            if 'en' in country_item["labels"]:
                country_title = unquote(country_item["labels"]['en']['value'])
            else:
                country_title = None
            if 'P30' in country_item['claims'] and 'datavalue' in country_item['claims']['P30'][0]['mainsnak']:
                continent_wdid = country_item['claims']['P30'][0]['mainsnak']['datavalue']['value']['id']
                continents.add(continent_wdid)
            else:
                continent_wdid = None
                countries_no_continent.append(country_wd_id)
            return country_title, continent_wdid
        else:
            return None, None
    else:
        return None, None


def gather_info_title_and_wiki_url(dataset, language, need_country):
    wiki_key = language + "wiki"
    title_language_key = f"title_{language}"
    items_by_wd_id = {item["wdid"].split('/')[-1]: item for item in dataset}
    wiki_url_key = f"wikipedia_url_{language}"

    # check if data already loaded
    has_wiki_url = wiki_url_key in dataset[0]
    has_country = 'country' in dataset[0] or not need_country
    has_title = title_language_key in dataset[0]

    countries_no_continent = []
    continents = set()
    if not has_wiki_url or not has_country or not has_title:
        for batch in tqdm.tqdm(batched(dataset, 50), total=len(dataset) // 50, desc='Loading urls'):
            ids = list(map(lambda x: x["wdid"].split('/')[-1], batch))
            response = get_wikidata_entities(ids, language)
            if response is None:
                response = get_wikidata_entities_no_cache(ids, language)
            for key, item in response["entities"].items():
                # some entities can be outdated
                if 'missing' in item:
                    continue
                if wiki_key in item["sitelinks"]:
                    items_by_wd_id[key][wiki_url_key] = unquote(item["sitelinks"][wiki_key]['url'])
                else:
                    items_by_wd_id[key][wiki_url_key] = None
                if language in item["labels"] and 'for-language' not in item["labels"][language]:
                    items_by_wd_id[key][title_language_key] = unquote(item["labels"][language]['value'])
                else:
                    items_by_wd_id[key][title_language_key] = None
                if not has_country:
                    country_title, continent_wdid = get_country_and_continent(item, countries_no_continent, continents, need_country, key, wiki_url_key, items_by_wd_id)
                    if country_title is not None or 'country' not in items_by_wd_id[key]:
                        items_by_wd_id[key]['country'] = country_title
                    if continent_wdid is not None or 'continent_wdid' not in items_by_wd_id[key]:
                        items_by_wd_id[key]['continent_wdid'] = continent_wdid

    if not has_country:
        print(countries_no_continent)
        print("-----------")
        print(continents)


def process_dataset(
    dataset_path,
    output_path,
    language,
    dataset_title,
    disable_sparql_cache,
    info_languages=("en", "zh")
):
    # Creating dataset from SPARQL request
    if disable_sparql_cache:
        sparql_selection = dataset_sparql[dataset_title]
        dataset = load_dataset_from_sparql(sparql_selection, info_languages)

        with open(dataset_path, 'w', encoding='utf8', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=dataset[0].keys())
            writer.writeheader()
            writer.writerows(dataset)

    # Loading dataset
    dataset = []
    with open(dataset_path, 'r', encoding='utf8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            dataset.append(row)
            if 'country2' in row:
                del row['country2']

    # rename fields if need
    rename_fields = {}
    if "item" in dataset[0]:
        rename_fields["item"] = "wdid"
    if "itemLabel" in dataset[0]:
        rename_fields["itemLabel"] = "title_en"
    if "wikipedia_url" in dataset[0]:
        rename_fields["wikipedia_url"] = "wikipedia_url_en"
    for item in dataset:
        for field_from, field_to in rename_fields.items():
            item[field_to] = item[field_from]

    # Gathering wikipedia urls (base -- for en language)
    wiki_url_key = f"wikipedia_url_{language}"
    gather_info_title_and_wiki_url(dataset, language, need_country=True)
    for info_language in info_languages:
        gather_info_title_and_wiki_url(dataset, info_language, need_country=False)

    items_with_language_urls = list(filter(lambda y: y[wiki_url_key] is not None and y[wiki_url_key] != '', dataset))
    print(f"Totally gathered {len(items_with_language_urls)} items with {language} wikipedia url")
    items_by_wikipedia_url = {get_wiki_url_short(item[wiki_url_key], language): item for item in items_with_language_urls}

    # Gathering wikipedia page views
    for item in dataset:
        item["page_view"] = None
        item["redirect_to"] = None
        item["page_size_bytes"] = None
        item["page_size_words"] = None
        item["is_stub"] = None
        item["is_disambiguation"] = None
        item["content_min_size"] = None
    pages_with_views_amount = 0
    for batch in tqdm.tqdm(batched(items_with_language_urls, 500), total=len(items_with_language_urls) // 500, desc='Loading views'):
        urls = list(map(lambda x: get_wiki_url_short(x[wiki_url_key], language), batch))
        pageviews_data = load_page_views(urls, language)
        for item in pageviews_data:
            url = unquote(get_wiki_url_short(item["url"], language))
            if url not in items_by_wikipedia_url:
                url = get_wiki_url_short(unquote(wikipedia.page(url).url), language)
            items_by_wikipedia_url[url]["page_view"] = item["total_views"]
            if item["total_views"] > 0:
                pages_with_views_amount += 1
    print(f"Totally {pages_with_views_amount} items with {language} wikipedia url has at least 1 view")

    # Gathering items wikipedia pages with redirects
    pages_with_redirect_amount = 0
    for batch in tqdm.tqdm(batched(items_with_language_urls, 50), total=len(items_with_language_urls) // 50, desc='Loading page redirects'):
        urls = list(map(lambda x: get_wiki_url_short(x[wiki_url_key], language), batch))
        redirects = load_page_redirects(urls, language)
        for url in urls:
            if url in redirects:
                items_by_wikipedia_url[url]["redirect_to"] = redirects[url]
                pages_with_redirect_amount += 1
            else:
                items_by_wikipedia_url[url]["redirect_to"] = None
    print(f"Totally {pages_with_redirect_amount} items with {language} wikipedia url are just redirects")

    # Calculating page size in words and bytes for items with language wikipedia url
    for batch in tqdm.tqdm(batched(items_with_language_urls, 50), total=len(items_with_language_urls) // 50, desc='Loading page size'):
        urls = list(map(lambda x: get_wiki_url_short(x[wiki_url_key], language), batch))
        page_sizes = load_page_size(urls, language)
        for url in urls:
            if url in page_sizes:
                items_by_wikipedia_url[url]["page_size_bytes"] = page_sizes[url][0]
                items_by_wikipedia_url[url]["page_size_words"] = page_sizes[url][1]
                items_by_wikipedia_url[url]["is_stub"] = page_sizes[url][2]
                items_by_wikipedia_url[url]["is_disambiguation"] = page_sizes[url][3]
            else:
                items_by_wikipedia_url[url]["page_size_bytes"] = None
                items_by_wikipedia_url[url]["page_size_words"] = None
                items_by_wikipedia_url[url]["is_stub"] = None
                items_by_wikipedia_url[url]["is_disambiguation"] = None

    # Calculating minimal useful page size for items with language wikipedia url
    for item in tqdm.tqdm(items_with_language_urls, desc='Calculating minimal useful page size for items with language wikipedia url'):
        url = get_wiki_url_short(item[wiki_url_key], language)
        content_min_size = load_useful_content_min_size(url, language)
        item["content_min_size"] = content_min_size

    with open(output_path, 'w', encoding='utf8') as f:
        json.dump(dataset, f)


def create_parser():
    parser = argparse.ArgumentParser(
        description='Detects items wikipedia pages and count their popularity and size',
    )
    parser.add_argument(
        '--dataset_path',
        type=str,
        help='path to the original items dataset in csv format with wikidata urls'
    )
    parser.add_argument(
        '--output_dataset_path',
        type=str,
        help='path to the generated dataset with wikipedia pages, their size and popularity'
    )
    parser.add_argument(
        '--language',
        type=str,
        help='language to work with',
        default='en'
    )
    parser.add_argument(
        '--dataset_title',
        type=str,
        help='title of the dataset with enitity types',
        default='cars'
    )
    parser.add_argument(
        '--no-sparql-dataset-cache',
        action='store_true',
        help='disabled reuse of pregenerated dataset'
    )
    return parser


if __name__ == "__main__":
    parser = create_parser()
    args = parser.parse_args()
    process_dataset(
        dataset_path=args.dataset_path,
        output_path=args.output_dataset_path,
        language=args.language,
        dataset_title=args.dataset_title,
        disable_sparql_cache=args.no_sparql_dataset_cache,
    )

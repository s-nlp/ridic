import argparse
import csv
import json

from joblib import Memory

import pandas as pd
import tqdm
import transformers

location = "./cachedir"
memory = Memory(location, verbose=0)

models = [
    transformers.pipeline(
        "text-generation",
        "unsloth/llama-3.1-8b-instruct",
        device="cuda:1",
        torch_dtype="auto",
    ),
    transformers.pipeline(
        "text-generation",
        "Qwen/Qwen2.5-7B-Instruct",
        device="cuda:1",
        torch_dtype="auto",
    ),
]
models = [_ for _ in zip(["llama3.1:8b", "qwen2.5:7b"], models)]

question_template = "In a paragraph, could you tell me what you know about <RIVER>?"

prompt = """
    Write article about the provided river, describe all facts and information about this river that you know.
    Follow the example:
    Task: What do you know about Neva river?
    Answer: The Neva River is a historically and geographically significant waterway in northwestern Russia, best known for its central role in the foundation and identity of Saint Petersburg. Flowing from Lake Ladoga, Europe’s largest freshwater lake, to the Gulf of Finland in the Baltic Sea, the Neva stretches just 74 kilometers in length but ranks among Europe’s most voluminous rivers due to its substantial discharge. With an average flow of around 2,500 cubic meters per second, it carries water from a vast drainage basin that spans much of northwestern Russia and Finland. Despite its short course, the river’s width varies dramatically, from 340 meters at its narrowest to over 1,250 meters at its widest points. As it approaches the Gulf of Finland, the Neva splits into a delta of distributaries and canals, forming the intricate network of islands and waterways that define the urban landscape of Saint Petersburg. The river’s historical importance is inseparable from the story of Saint Petersburg itself. In 1703, Tsar Peter the Great chose the Neva’s marshy delta as the site for his new capital, envisioning it as Russia’s “window to Europe.” The city’s construction was a monumental feat of engineering, requiring canals and embankments to tame the flood-prone river. Over time, the Neva became a symbol of imperial ambition and resilience. During the Great Northern War, the river’s strategic position helped Russia secure access to the Baltic Sea, and centuries later, during World War II, it played a critical role in the survival of Leningrad (as Saint Petersburg was then known) during the 872-day siege by Nazi forces. The frozen Neva and Lake Ladoga became part of the “Road of Life,” a perilous ice route used to transport supplies and evacuate civilians. The Neva’s relationship with Saint Petersburg is both poetic and pragmatic. Its waters flow past some of the city’s most iconic landmarks, including the Winter Palace, the Peter and Paul Fortress, and the Hermitage Museum. The river’s embankments, lined with grand palaces and historic buildings, are connected by over 300 bridges, many of which are architectural marvels. The Palace Bridge, with its nightly drawbridge spectacle, is a defining image of the city. These bridges not only facilitate navigation but also symbolize the connection between the city’s past and present. The Neva is also a vital artery for transportation, forming part of the Volga-Baltic Waterway, which links the Baltic Sea to the Caspian Sea, enabling trade and tourism. River cruises along the Neva offer visitors a unique perspective on Saint Petersburg’s grandeur. Yet the river’s power has long been a double-edged sword. The Neva is notorious for its devastating floods, caused by cyclonic winds pushing seawater from the Gulf of Finland into the river’s delta. Over 300 floods have been recorded since the city’s founding, some submerging streets and buildings under meters of water. To mitigate this threat, a massive flood prevention dam was completed in 2011 after decades of construction, stretching 25 kilometers across the Gulf of Finland. This engineering marvel has largely tamed the river’s destructive potential, safeguarding the city’s cultural heritage. Ecologically, the Neva faces challenges common to urbanized waterways. Industrial pollution and urban runoff have impacted water quality, though conservation efforts aim to restore habitats for fish like Atlantic salmon and lamprey. The river’s seasonal freeze, from December to April, transforms it into a icy corridor maintained by icebreakers, while the summer “White Nights” phenomenon—when the northern sun barely sets—bathes the Neva in ethereal twilight, celebrated in local festivals. The name “Neva” is believed to derive from an ancient Finnish word meaning “swamp” or “marsh,” a nod to the region’s pre-Russian history. Today, the river stands as a testament to human ingenuity and adaptation, entwined with the identity of Saint Petersburg. It is not merely a body of water but a living chronicle of empire, war, art, and survival—a symbol of Russia’s resilience and its enduring dialogue with nature.

    Now do the task yourself
    Task: <QUESTION>
    Answer:
""".strip()


def get_messages(dataset_title, prompt):
    if dataset_title == "cars":
        messages = [
            {
                "role": "system",
                "content": """You are a knowledgeable assistant that writes concise, encyclopedic-style summaries about automobiles. Your goal is to generate paragraphs that reflect the type of factual coverage typically found in Wikipedia articles. For each vehicle, include a variety of verifiable and relevant facts such as:
        - Basic specifications: manufacturer, production years, model years, vehicle class, body style, layout (e.g. FWD, AWD), platform, predecessor or successor if applicable;
        - Design and engineering: engine types, horsepower, transmission options, suspension, dimensions, curb weight, key design features;
        - Historical background: concept origins, launch date, major facelifts or generational changes, key markets;
        - Variants and performance: trim levels, sport or hybrid versions, performance statistics (e.g. top speed, acceleration);
        - Market presence: regions where sold, notable sales figures, market reception, awards;
        - Safety and technology: safety ratings, standard and optional technology or infotainment systems;
        - Cultural impact: appearances in media, public perception, notable usage, origin of model name.
        Present all information in fluent, well-structured prose similar to a concise Wikipedia introduction or overview section. Do not invent facts. Prioritize accuracy and breadth of coverage over narrative storytelling.
        """,
            },
            {"role": "user", "content": prompt},
        ]
    elif dataset_title == "rivers":
        messages = [
            {
                "role": "system",
                "content": (
                    "You are a knowledgeable assistant that writes concise, encyclopedic-style summaries "
                    "about rivers. Your goal is to generate paragraphs that reflect the type of factual coverage "
                    "typically found in Wikipedia articles. For each river, include a variety of verifiable and "
                    "relevant facts such as:\n"
                    "- Geography: origin (source), mouth, length, countries/regions/states it flows through, tributaries,\n"
                    "  basin size, average discharge;\n"
                    "- Cities and infrastructure: major cities along the river, dams, canals, or bridges; \n"
                    "- History and economy: historical significance, trade routes, flood events, use in transport or irrigation; \n"
                    "- Ecology and environment: environmental concerns, protected areas, flora/fauna; \n"
                    "- Cultural aspects: literary references, local traditions, festivals, or origin of the name. \n"
                    "Present all information in fluent, well-structured prose similar to a concise Wikipedia introduction "
                    "or overview section. Do not invent facts. Prioritize accuracy and breadth of coverage over narrative storytelling."
                ),
            },
            {"role": "user", "content": prompt},
        ]
    elif dataset_title == "disasters":
        messages = [
            {
                "role": "system",
                "content": """You are a knowledgeable assistant that writes concise, encyclopedic-style summaries about natural disasters. Your goal is to generate paragraphs that reflect the type of factual coverage typically found in Wikipedia articles. For each event, include a variety of verifiable and relevant facts such as:
- Classification and meteorology: type of disaster (e.g. hurricane, earthquake, wildfire), date of occurrence, location, magnitude or category, development history, path or affected area, key meteorological characteristics (e.g. wind speed, rainfall, pressure);
- Impact and damage: death toll, injuries, economic losses, infrastructure damage, displaced populations, environmental effects;
- Preparations and response: evacuation orders, government responses, emergency declarations, aid efforts, recovery timelines;
- Historical significance: comparison to similar events, records broken, influence on policy or building codes;
- Legacy and aftermath: long-term effects, rebuilding efforts, changes to local communities, anniversaries or memorials;
- Naming and cultural references: naming history, retirement of name (if applicable), presence in media, literature, or public memory.
Present all information in fluent, well-structured prose similar to a concise Wikipedia introduction or overview section. Do not invent facts. Prioritize accuracy and breadth of coverage over narrative storytelling.
""",
            },
            {"role": "user", "content": prompt},
        ]
    else:
        messages = [
            {
                "role": "system",
                "content": """You are a knowledgeable assistant that writes concise, encyclopedic-style summaries. Your goal is to generate paragraphs that reflect the type of factual coverage typically found in Wikipedia articles. For each event, include a variety of verifiable and relevant facts.
       Present all information in fluent, well-structured prose similar to a concise Wikipedia introduction or overview section. Do not invent facts. Prioritize accuracy and breadth of coverage over narrative storytelling.
        """,
            },
            {"role": "user", "content": prompt}
        ]

    return messages


@memory.cache()
def ask_llm(client, model_name, dataset_title, prompt):
    messages = get_messages(dataset_title, prompt)
    if model_name == "qwen2.5:7b":
        response = client.chat.completions.create(
            model="Qwen/Qwen2.5-7B-Instruct", messages=messages
        )
        model_answer = response.choices[0].message.content.strip()
    elif model_name == "llama3.1:8b":
        response = client.chat.completions.create(
            model="meta-llama/Llama-3.1-8B-Instruct", messages=messages
        )
        model_answer = response.choices[0].message.content.strip()

    return model_answer


@memory.cache()
def ask_llm_transformers(pipe, dataset_title, prompt):
    messages = get_messages(dataset_title, prompt)
    model_answer = pipe(messages, max_new_tokens=512)[0]["generated_text"][-1][
        "content"
    ]
    return model_answer


def get_wiki_url_short(s, language):
    if not s.startswith(f"https://{language}.wikipedia.org/wiki/"):
        print(f"INCORRECT WIKI URL: {s}")
    return s[len(f"https://{language}.wikipedia.org/wiki/"):]


def get_title(item, language, dataset_title: str, duplicated_item_names):
    if item[f"title_{language}"] in duplicated_item_names or item[f"title_{language}"] == '' or item[f"title_{language}"] is None:
        item_raw_title = get_wiki_url_short(item[f"wikipedia_url_{language}"], language).replace('_', ' ')
    else:
        item_raw_title = item[f"title_{language}"]
    if dataset_title == "rivers":
        item_title = (
            item_raw_title
            if "river" in item_raw_title.lower()
            else item_raw_title + " river"
        )
    elif dataset_title == "cars":
        item_title = (
            item_raw_title
            if "car" in item_raw_title.lower()
            else item_raw_title + " car"
        )
    elif dataset_title == "disasters":
        item_title = (
            item_raw_title
            if "disaster" in item_raw_title.lower()
            else item_raw_title + " disaster"
        )
    else:
        item_title = item_raw_title
    return item_title


def append_llm_description(
        total_dataset, dataset_title, language, duplicated_item_names
):
    for index, item in tqdm.tqdm(enumerate(total_dataset), total=len(total_dataset)):
        for model_name, pipe in models:
            if model_name in item and item[model_name] != "":
                continue
            item_title = get_title(item, language, dataset_title, duplicated_item_names)
            question = question_template.replace("<RIVER>", item_title)
            model_answer = ask_llm_transformers(
                pipe, dataset_title, prompt.replace("<QUESTION>", question)
            )
            model_answer = model_answer.replace("\n", " ")
            item[model_name] = model_answer


def process_dataset(dataset_path, dataset_title, language):
    dataset = []
    with open(dataset_path, "r", encoding="utf8") as f:
        if ".csv" in dataset_path:
            reader = csv.DictReader(f)
            for index, row in enumerate(reader):
                dataset.append(row)
        else:
            df = pd.read_json(f)
            df.to_csv('.'.join(dataset_path.split('.')[0:-1]) + '.csv')
            with open('.'.join(dataset_path.split('.')[0:-1]) + '.csv', "r", encoding="utf8") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    dataset.append(row)

                del df

    # get duplicated items names
    items_names = {}
    for item in dataset:
        if item[f"title_{language}"] not in items_names:
            items_names[item[f"title_{language}"]] = []
            items_names[item[f"title_{language}"]].append(item)
    duplicated_item_names = []
    for item_name, items_t in items_names.items():
        if len(items_t) < 2:
            continue
        duplicated_item_names.append(item_name)
        print(f"{item_name}: {len(items_t)}")

    append_llm_description(dataset, dataset_title, language, duplicated_item_names)

    with open(f"1000_{dataset_title}_with_llm.json", "w", encoding="utf8") as f:
        json.dump(dataset, f)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="This script uses transformers to provide llm generations",
    )

    parser.add_argument(
        "--dataset_path",
        type=str,
        default="./wikidump/",
        help="Path to the dataset to generate from",
    )
    parser.add_argument(
        "--dataset_title",
        type=str,
        help='Title of the dataset, e.g. "rivers", "cars", "disasters".',
    )
    parser.add_argument(
        "--language",
        type=str,
        help='Language of generations',
        default="en",
    )

    args = parser.parse_args()

    process_dataset(args.dataset_path, args.dataset_title, args.language)

import time
import json
import tiktoken
import openai
import pickle
import numpy as np
from tqdm import tqdm
import dotenv
import os

BLOCK_SIZE = 500
EMBED_MAX_SIZE = 8150

dotenv.load_dotenv()
openai.api_key = os.getenv("OPENAI_API_KEY")
enc = tiktoken.get_encoding("cl100k_base")


def get_size(text):
    "take text, return number of tokens"
    return len(enc.encode(text))


def embed_text(text, sleep_after_success=1):
    "take text, return embedding vector"
    text = text.replace("\n", " ")
    tokens = enc.encode(text)
    if len(tokens) > EMBED_MAX_SIZE:
        text = enc.decode(tokens[:EMBED_MAX_SIZE])

    while True:
        try:
            res = openai.Embedding.create(
                input=[text],
                model="text-embedding-ada-002")
            time.sleep(sleep_after_success)
        except Exception as e:
            print(e)
            time.sleep(1)
            continue
        break

    return res["data"][0]["embedding"]

def load_json_with_seek(file_path):
    with open(file_path, 'r', encoding='utf-8') as file:
        while True:
            current_char = file.read(1)
            if not current_char or current_char == '{' or current_char == '[':
                file.seek(file.tell() - 1)
                break
        json_data = json.load(file)
    return json_data


def update_from_twitter(json_file, out_index, in_index=None):
    """
    out_index: Output index file name
    json_file: Input JSON file name (from twitter)
    in_index: Optional input index file name. It is not modified and is used as cache to reduce API calls.
    out_index: 出力インデックスファイル名
    json_file: 入力JSONファイル名 (twitterからの)
    in_index: オプショナルな入力インデックスファイル名。変更されず、APIコールを減らすためのキャッシュとして使用されます。

    # usage
    ## create new index
    update_from_twitter(
        "from_twitter/ina_ani.json",
        "ina_ani.pickle")

    ## update index
    update_from_twitter(
        "from_twitter/ina_ani-0314.json", "ina_ani-0314.pickle", "ina_ani-0310.pickle")
    """
    if in_index is not None:
        cache = pickle.load(open(in_index, "rb"))
    else:
        cache = None

    vs = VectorStore(out_index)
    data = load_json_with_seek(json_file)
    print(len(data))

    for p in tqdm(data):
        buf = []
        body = p["tweet"]["full_text"]
        title = p["tweet"]["id_str"]
        vs.add_record(body, title, cache)
    vs.save()

class VectorStore:
    def __init__(self, name, create_if_not_exist=True):
        self.name = name
        try:
            self.cache = pickle.load(open(self.name, "rb"))
        except FileNotFoundError as e:
            if create_if_not_exist:
                self.cache = {}
            else:
                raise

    def add_record(self, body, title, cache=None):
        if cache is None:
            cache = self.cache
        if body not in cache:
            # call embedding API
            self.cache[body] = (embed_text(body), title)
        elif body not in self.cache:
            # in cache and not in self.cache: use cached item
            self.cache[body] = cache[body]

        return self.cache[body]

    def get_sorted(self, query):
        q = np.array(embed_text(query, sleep_after_success=0))
        buf = []
        for body, (v, title) in tqdm(self.cache.items()):
            buf.append((q.dot(v), body, title))
        buf.sort(reverse=True)
        return buf
    def get_sorted_from_page(self, query):
        buf = []
        target = None
        for body, (v, title) in tqdm(self.cache.items()):
            if title == query:
                target = np.array(v)
                break
        for body, (v, title) in tqdm(self.cache.items()):
            buf.append((target.dot(v), body, title))
            #buf.append((target.dot(v)/(np.linalg.norm(target)*np.linalg.norm(v)), body, title))
        buf.sort(reverse=True)
        return buf

    def save(self):
        pickle.dump(self.cache, open(self.name, "wb"))


if __name__ == "__main__":
    # Sample default arguments for update_from_twitter()
    JSON_FILE = "from_twitter/tiny_twitter_sample.js"
    INDEX_FILE = "tiny_twitter_sample.pickle"

    update_from_twitter(JSON_FILE, INDEX_FILE)

from make_index import VectorStore
import json
from datetime import datetime, timezone, timedelta

def load_json_with_seek(file_path):
    with open(file_path, 'r', encoding='utf-8') as file:
        while True:
            current_char = file.read(1)
            if not current_char or current_char == '{' or current_char == '[':
                file.seek(file.tell() - 1)
                break
        json_data = json.load(file)
    return json_data

def ask(input_str, index_file):
    out = []
    vs = VectorStore(index_file)
    samples = vs.get_sorted(input_str)

    used_title = []
    count = 0
    for _sim, body, title in samples:
        if title in used_title:
            continue
        count = count + 1
        if count > 2000:
            break;
        out.append([count, title, body.replace("\n"," ")])
        used_title.append(title)
    return out

def print_monthly(unwell_post, tweets):
    tweetMap = {}
    result = [0] * 12
    base_result = [0] * 12
    for t in tweets:
        id_str = t["tweet"]["id_str"]
        d = t["tweet"]["created_at"]
        parsed_date = datetime.strptime(d, "%a %b %d %H:%M:%S %z %Y")
        tweetMap[id_str] = parsed_date
        base_result[parsed_date.month - 1] = base_result[parsed_date.month - 1] + 1
    
    for size in [100, 200, 500, 1000, 1500, 2000]:
        ranking = 2000
        result = [0] * 12
        for post in unwell_posts[:size]:
            target_id = post[1]
            date = tweetMap[target_id]
            result[date.month - 1] = result[date.month - 1] + 1
            ranking = ranking - 1
        line = []
        for a, b in zip(result, base_result):
            if b != 0:
                line.append(str(a/b))
            else:
                line.append(str(0))
        print(",".join(line))

unwell_posts = ask("体調、健康", "tiny_twitter_sample.pickle")
tweets = load_json_with_seek("from_twitter/tweets_ina_ani.js")

print_monthly(unwell_posts, tweets)

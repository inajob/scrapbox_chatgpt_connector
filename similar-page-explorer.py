from flask import Flask
from urllib.parse import quote
from make_index import VectorStore
index_file = "nishio-vector-20230309.pickle"
base = "https://scrapbox.io/nishio/"

app = Flask(__name__)

@app.route('/')
def hello():
    return "Hello, World!"

@app.route('/same/<title>')
def same(title):
    vs = VectorStore(index_file)
    input_str = title
    samples = vs.get_sorted_from_page(input_str)

    to_use = []
    used_title = []
    count = 0
    for _sim, body, title in samples:
        if title in used_title:
            continue
        used_title.append(title)
        count = count + 1
        if count > 20:
            break

    out = "".join(map(lambda x: '<a href="'+quote(x)+'">'+x+'</a> - <a href="' + base + quote(x)+ '" target="inline">open</a><br>', used_title))
    return out


if __name__ == '__main__':
    app.run()


import json


def read_data(path):
    with open(path, 'r', encoding='utf-8') as f:
        data = json.loads(f.read())
    return data

def write_data(data, path):
    with open('large_dedup_sorted.json', 'w', encoding='utf-8') as f:
        f.write(json.dumps(data))

def dedup_data(data):
    class ItemSet():
        def __init__(self):
            self.items = {}

        def add(self, item):
            item_hash = frozenset({'name':item['name'],'author':item['author']}.items())
            self.items[item_hash] = item

        def values(self):
            return self.items.values()

    book_set = ItemSet()
    for b in data:
        book_set.add(b)  
    return list(book_set.values())

def sort_data(data):
    data_sorted = sorted([d for d in data if d['rating_count'] > 2000], key=lambda x: x['avg_rating'], reverse=True)
    return data_sorted

def filter_data(path='results/books_raw.json'):
    raw_data = read_data(path)
    data_dedup = dedup_data(raw_data)
    write_data(data_dedup, 'results/books_cleaned_dedup.json')
    data_sorted = sort_data(data_dedup)
    write_data(data_sorted, 'results/books_cleaned_dedup_sorted.json')


if __name__ == '__main__':
    filter_data('results/books_raw.json')




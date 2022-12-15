from copy import deepcopy

from google.cloud import translate_v2
import requests


translate_client = translate_v2.Client()

base_url = 'http://localhost:8080'
collection_id = '44f8a643-ba14-47fd-a68c-31d8f34fcfd2'
email = 'test@test.edu'
password = 'admin'


# Log into DSpace api
def get_authenticated_session():
    s = requests.Session()
    res = s.post(f'{base_url}/rest/login', data={'email': email, 'password': password})
    res.raise_for_status()
    return s


sess = get_authenticated_session()


# Returns article items enriched with metadata and bitstreams
def find_articles(items):
    articles = []

    for item in items:
        item['metadata'] = sess.get(f'{base_url}{item["link"]}/metadata').json()

        type_meta = next((m for m in item['metadata'] if m['key'] == 'dc.type'), None)
        if not type_meta or type_meta['value'] != 'Article':
            continue

        item['bitstreams'] = sess.get(f'{base_url}{item["link"]}/bitstreams').json()

        articles.append(item)

    return articles


def get_item_meta(item, key):
    return next((m for m in item['metadata'] if m['key'] == key), None)


def get_item_issn(item):
    return get_item_meta(item, 'dc.identifier.issn')


def is_english(item):
    return (get_item_meta(item, 'dc.language.iso').get('value') or '').startswith('en')


# Returns whether there already exists a translated copy of the provided item.
def has_translation(articles, item):
    item_issn = get_item_issn(item)

    for item in articles:
        if get_item_issn(item) == item_issn and not is_english(item):
            return True

    return False


# Finds items that are in english, that don't have a corresponding article in spanish
def find_untranslated_articles(articles):
    untranslated_articles = []

    for item in articles:
        if is_english(item) and not has_translation(articles, item):
            untranslated_articles.append(item)

    return untranslated_articles


def map_metas(metadata):
    new_metas = []
    for m in metadata:
        new_meta = {}
        for k, v in m.items():
            if k in ('key', 'value', 'language'):
                new_meta[k] = v

        new_metas.append(new_meta)

    return new_metas


def translate_content(content):
    res = translate_client.translate(content, source_language='en', target_language='es')
    return res['translatedText']


def delete_item(item):
    res = sess.delete(f'{base_url}{item["link"]}')
    res.raise_for_status()


def create_translated_item(item):
    print(f'Creating translation for {item["name"]}')

    article_bs = next((bs for bs in item['bitstreams'] if bs['mimeType'] == 'text/plain'))

    article_content = sess.get(f'{base_url}{article_bs["retrieveLink"]}').text

    translated_content = translate_content(article_content)

    item_copy = deepcopy(item)
    item_copy['metadata'] = map_metas(item_copy['metadata'])

    # Update item's language
    lang_meta = get_item_meta(item_copy, 'dc.language.iso')
    lang_meta['value'] = 'es'

    # Create new item for translated article.
    res = sess.post(f'{base_url}/rest/collections/{collection_id}/items', json=item_copy, headers={'Accept': 'application/json'})
    res.raise_for_status()

    try:
        new_item = res.json()

        params = {
            k: v 
            for k, v in article_bs.items()
            if k in ('name', 'description', 'year', 'month', 'day')
        }

        res = sess.post(f'{base_url}{new_item["link"]}/bitstreams', params=params, data=translated_content)
        res.raise_for_status()
    except Exception:
        # Delete the partially created item if something fails
        delete_item(item_copy)


# TODO: Pagination
items = sess.get(f'{base_url}/rest/collections/{collection_id}/items').json()
articles = find_articles(items)
untranslated_articles = find_untranslated_articles(articles)
for article in untranslated_articles:
    create_translated_item(article)

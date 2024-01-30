import re, requests

def get_init():
    url = 'https://shop.coop.co.uk/env-config.js'
    response = requests.get(url)
    text = response.text
    api_key = get_value(text, 'REACT_APP_DG_API_KEY')
    org_id = get_value(text, 'REACT_APP_DG_ORG_ID')
    store_id = get_value(text, 'REACT_APP_DG_STORE_ID')
    # store_id = 'd472202a-5d37-4fcf-94fd-1f34a0b17094'
    # store_id = '11ac6536-f8b2-4691-a31b-e80a33a7e651'
    # store_id = 'd472202a-5d37-4fcf-94fd-1f34a0b17094'
    # store_id = 'd472202a-5d37-4fcf-94fd-1f34a0b17094'
    # store_id = 'd472202a-5d37-4fcf-94fd-1f34a0b17094'

    return api_key, org_id, store_id
    

def get_value(text, key):
    pos = text.find(key)
    a = text.find('"', pos) + 1
    z = text.find(',', pos) - 1
    return text[a:z]

def get_post_data(categories, store_id, page):
    data = {
        "filters":
        {
            "category_path_ids": categories
        },
        "language": "en",
        "meta":
            {
                "pagination":
                {
                    "page": page,
                    "page_size": 500}
        },
        "store_id": store_id
    }
    return data

def get_header(api_key, org_id):
    return {
            'DG-Api-Key': api_key,
            'DG-Organization-Id': org_id,
            'Referer' : ''
            }

def clean_name(name):
    name = validate(name)
    result = re.sub(".*?\[(.*?)\]", '', name)
    return result

def validate(text):
    try:
        if text:
            return text.strip()
        return 'NA'
    except:
        return 'NA'

def get_category(categories):
    cats = set()
    for cat in categories:
        category = cat['parent_name']['en']
        sub_category = cat['name']['en']
        if category == 'Coop Home Delivery' or ('View All' in sub_category) : continue
        cats.add((category, sub_category))
        
    return cats
import time

TIME = int(time.time() * 1000)

def get_cats(cats):
    c = []
    for cat in cats:
        if cat.get('child_taxonomies', ""):
            c.extend(get_cats(cat['child_taxonomies']))
        elif 'hierarchy_id' in cat:
            c.append((cat['hierarchy_id'], cat['taxonomy_type']))
    
    return c


# def get_cats(cats):
#     c = []
#     for cat in cats:
#         if cat.get('child_taxonomies', ""):
#             c.extend(get_cats(cat['child_taxonomies']))
#         elif 'hierarchy_id' in cat and cat['taxonomy_type'] == 'aisle':
#             c.append((cat['hierarchy_id'], cat['taxonomy_type']))
    
#     return c


def validate_value(field, keys):
    try:
        for key in keys:
            if key in field:
                field = field[key]
            else:
                return ''
    except:
        return ""
    return field

def get_products_payload(id, page):
    return {
        "requestorigin": "gi",
        "contract": "web/cms/taxonomy-page",
        "variables": {
            "is_eat_and_collect": False,
            "store_id": "4565",
            "type": "content",
            "page_size": 60,
            "page": page,
            "request_origin": "gi",
            "ship_date": TIME,
            "payload": {
                "page_type": id[1],
                "hierarchy_id": id[0],
                "filter_query": [],
                "cart_contents": [],
                "page_meta_info": True,
            }
        }
    }


def get_category_payload():
    return {
            "requestorigin": "gi",
            "contract": "web/cms/taxonomy",
            "variables": {
                "ship_date": TIME,
                "store_id": "4565",
                "special_offer": False,
                "user_segments": [
                                    "NAV_UI"
                                    ],
            }
        }

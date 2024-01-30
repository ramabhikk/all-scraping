def validate(data, keys):
    for key in keys:
        if key in data:
            data = data[key]
        else:
            return ""
    return data


def get_item(product):
    item = {}
    categories = validate(product, ['mainCategory'])
    cat1, cat2 = "", ""
    if categories:
        categories = categories.split('/')
        cat1 = categories[0]
        cat2 = categories[1] if len(categories) > 1 else ""

    item['GTIN'] = validate(product, ['gtin'])
    item['Category'] = cat1
    item['Sub Category'] = cat2
    item['Product'] = validate(product, ['name'])
    item['Brand'] = validate(product, ['brand', 'name'])
    item['Price'] = validate(product, ['price', 'current'])
    item['Unit Price'] = validate(product, ['price', 'unit', 'price'])
    item['Unit'] = validate(product, ['price', 'unit', 'per'])
    item['Offer'] = validate(product, ['offer', 'text'])

    return item
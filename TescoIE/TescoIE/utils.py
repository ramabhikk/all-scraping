import js2py, re

filler = ['valid', 'from', 'tomorrow' , '(' , ')']

POST_URL = 'https://www.tesco.ie/groceries/Ajax/GetNavigationFlyout.aspx'

def get_post_data(timestamp, referer):
    return f'<request xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" timestamp="{timestamp}" referrerUrl="https://www.tesco.ie/groceries/?&amp;icid=homepage_nav_groceries_1Start"><navigationPosition selectedUrl="{referer}" flyoutLevel="3"/></request>'

def get_barcode(url):
    if 'noimage' in url:
        return 'NA'
    url = url.replace('\\','/')
    return url.split('/')[-2] + '\t'

def get_unit_measure(unit):
    unit = unit.split('/')[-1].replace(')','').strip()

    for c in unit:
        if c.isdigit():
            unit = unit.replace(c,'')

    if unit == 'l':
        unit = 'LITRE'
    elif 'each' in unit:
        unit = unit.replace('each', 'EACH')
    return unit

def get_validity(validity):
    for fill in filler:
        validity = validity.replace(fill, '')
    valid = validity.split('until')
    return valid[0].strip(), valid[1].strip()

def get_base_id(metadata):
    index = 1
    while True:
        old_metadata = metadata
        metadata = metadata.replace('new TESCO.sites.UI.entities.Product(', f'P{index}:',1)
        if old_metadata == metadata:
            break
        index += 1

    
    metadata = 'var m = {' + metadata.replace(');',',') + "}; m"
    metadata = js2py.eval_js(metadata)

    base_ids = {}
    for i in range(1, index):
        id_ = metadata[f'P{i}'].productId
        base_ids[id_] = metadata[f'P{i}'].baseProductId

    return base_ids

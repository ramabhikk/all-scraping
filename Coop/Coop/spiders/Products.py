from urllib.parse import scheme_chars

from requests.api import post
import scrapy
import json
from ..utils import get_init, get_post_data, get_header, clean_name, validate, get_category


class ProductsSpider(scrapy.Spider):
    name = 'products'
    allowed_domains = ['shop.coop.co.uk',
                       'retailer-api-coop.foodieservices.com']

    def start_requests(self):
        self.api_key, self.org_id, self.store_id = get_init()
        taxonomy_url = f'https://api.shop.coop.co.uk/cms/taxonomy?store_id={self.store_id}'
        yield scrapy.Request(taxonomy_url)

    def parse(self, response):
        categories = json.loads(response.text)['categories']
        categories = list(categories.keys())
     
        url = 'https://retailer-api-coop.foodieservices.com/v1/search/products'
        headers = get_header(self.api_key, self.org_id)
        for category in categories:
            data = get_post_data([category], self.store_id, 0)

            yield scrapy.Request(url, method='POST', body=json.dumps(data), 
                                    headers=headers, callback=self.parse_products, meta={'categories':category,'cookiejar': category})

    def parse_products(self, response):
        response_data = json.loads(response.text)
        data = response_data['data']
        products = data['products']

        for product in products:
            gtin = validate(product['gtin']) + '\t'
            name = clean_name(product['name']['en'])
            description = validate(product['description']['en']).replace('\n','; ')
            brand = validate(product['brand']['default'])
            price = '£' + str(product['prices']['clicks_unit_price'])
            cats = get_category(product['categories'])
            promo = validate(product['details']['trade_item_marketing_message']['en'])
        
            for cat in cats:
                yield {
                    'G TIN' : gtin,
                    'Category' : cat[0],
                    'Sub Category' : cat[1],
                    'Name' : name,
                    'Price' : price,
                    'Brand' : brand,
                    'Description' : description,
                    'Promotion' : promo
                }

        meta = response_data['meta']
        next_page = meta['pagination']['next_page']
        
        if next_page:
            url = 'https://retailer-api-coop.foodieservices.com/v1/search/products'
            categories = response.meta['categories']
            headers = get_header(self.api_key, self.org_id)
            data = get_post_data([categories], self.store_id, next_page)

            yield scrapy.Request(url, method='POST', body=json.dumps(data), 
                                    headers=headers, callback=self.parse_products, meta=response.meta)

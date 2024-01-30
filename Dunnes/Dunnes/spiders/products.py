import scrapy
import json
from w3lib.html import remove_tags

def validate(data, key):
    if key in data:
        return data[key]
    return ''

class ProductsSpider(scrapy.Spider):
    name = 'products'
    allowed_domains = ['storefrontgateway.dunnesstoresgrocery.com']
    start_urls = ['https://storefrontgateway.dunnesstoresgrocery.com/api/stores']

    def parse(self, response):
        data = json.loads(response.text)
        store_id = data['items'][0]['retailerStoreId']

        url = f'https://storefrontgateway.dunnesstoresgrocery.com/api/stores/{store_id}/categoryHierarchy'

        yield scrapy.Request(url, meta={'storeID':store_id}, callback=self.parse_category)

    def parse_category(self, response):
        data = json.loads(response.text)
        
        store_id = response.meta['storeID']
        for cat in data['children'][0]['children']:
            for sub_cat in cat['children']:
                category = sub_cat['identifier']
                url = f'https://storefrontgateway.dunnesstoresgrocery.com/api/stores/{store_id}/categories/{category}/search?q=*&take=100&skip=0&sort=&f='

                yield scrapy.Request(url, callback=self.parse_product)


    def parse_product(self, response):
        data = json.loads(response.text)

        products = data['items']

        for product in products:
            item = {}
            item['ProductID'] = product['sku']
            item['Category'] = product['categories'][1]['category']
            item['Sub Category'] = product['categories'][2]['category']
            item['Product'] = product['name']

            
            item['Price'] = validate(product, 'price')
            item['Price Per Unit'] = validate(product, 'pricePerUnit')
            item['Description'] =  remove_tags(validate(product, 'description'))
            
            item['Promotion'] = ''
            item['Promo Start Date'] = ''
            item['Promo End Date'] = ''
            if 'promotions' in product:
                promo = product['promotions'][0]
                item['Promotion'] = promo['name']
                item['Promo Start Date'] = promo['startDate']
                item['Promo End Date'] = promo['endDate']

            yield item
            self.logger.info(f"Scraped Product: {item['Product']} {item['ProductID']}")
            
        pagination = data['pagination']['_links']
        if 'next' in pagination:
            url = pagination['next']['href']

            yield response.follow(url, callback=self.parse_product)





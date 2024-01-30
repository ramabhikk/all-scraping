from subprocess import call
from unicodedata import category
import scrapy
import json
from ..utils import *


class MorrisonsProductsSpider(scrapy.Spider):
    name = 'morrisons_products'
    allowed_domains = ['groceries.morrisons.com']
    start_urls = ['https://groceries.morrisons.com/webshop/api/v1/subnavigation?catalogueType=SHOP']

    def parse(self, response):
        categories = json.loads(response.text)
    
        for category in categories[:]:
            url = f'https://groceries.morrisons.com/webshop/api/v1/browse?tags={category["id"]}'
            yield scrapy.Request(url, callback=self.parse_product)

    def parse_product(self, response):
        data = json.loads(response.text)
        sections = data['mainFopCollection']['sections']

        no_details = []
        for section in sections:
            for product in section['fops']:
                if 'product' in product:
                    item = get_item(product['product'])
                    yield item
                    self.logger.info(f"Scraped: {item['Product']} ({item['GTIN']})")
                else:
                    no_details.append(product['sku'])

        if no_details:
            url = 'https://groceries.morrisons.com/webshop/api/v1/products?skus=' 
            more_products = [no_details[i:i + 200] for i in range(0, len(no_details), 200)]
  
            for more in more_products:
                m_url = url + ','.join(more)
                yield scrapy.Request(m_url, callback=self.parse_more_product)


    def parse_more_product(self, response):
        products = json.loads(response.text)

        for product in products:
            item = get_item(product)

            yield item
            self.logger.info(f"Scraped: {item['Product']} ({item['GTIN']})")


                    
                
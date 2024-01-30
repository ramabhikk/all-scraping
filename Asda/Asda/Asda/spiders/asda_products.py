import scrapy
import json
from ..utils import *

class AsdaProductsSpider(scrapy.Spider):
    name = 'asda_products'
    allowed_domains = ['groceries.asda.com']
    headers = {
        'request-origin':'gi',
        'Content-Type':'application/json'
    }

    handle_httpstatus_list  = [400, 404,403,406, 408, 500, 503, 504]

    def start_requests(self):
        yield scrapy.Request('https://groceries.asda.com/')        
       
    def parse(self, response):
        url = 'https://groceries.asda.com/api/bff/graphql'
        yield scrapy.Request(url, method='POST', headers=self.headers, body=json.dumps(get_category_payload()), callback=self.parse_category, dont_filter=True)



    def parse_category(self, response):
        if response.status > 300:
            with open('check.html', 'w') as f:
                f.write(response.text)
                
        data = json.loads(response.text)

        category = data['data']['tempo_taxonomy']['categories']

        cat_ids = get_cats(category)
        url = 'https://groceries.asda.com/api/bff/graphql'

        for id in cat_ids:
            payload = get_products_payload(id, 1)
            yield scrapy.Request(url, method='POST', headers=self.headers, 
                                body=json.dumps(payload), callback=self.parse_product,
                                cb_kwargs={'id': id}, dont_filter=True)

    
    def parse_product(self, response, id):
        # try:
            data = json.loads(response.text)
            zones = data['data']['tempo_cms_content']['zones']

            products = []
            zone = ''
            for z in zones:
                if z.get('type', "") == "ProductListing":
                    zone = z
                    products = validate_value(z, ['configs', 'products', 'items'])

            if not products:
                return

            for product in products:
                item = {}
                item['Product ID'] = validate_value(product, ['item', 'sku_id'])
                item['UPC ID'] = validate_value(product, ['price', 'upc'])
                item['Category'] = validate_value(product, ['item', 'taxonomy_info', 'category_name'])
                item['Department'] = validate_value(product, ['item', 'taxonomy_info', 'dept_name'])
                item['Product'] = validate_value(product, ['item', 'name'])
                item['Price'] = validate_value(product, ['price', 'price_info', 'price'])
                sale_price = validate_value(product, ['price', 'price_info', 'sale_price'])
                item['Sale Price'] = item['Price'] if sale_price == '£0.0' else sale_price
                item['Unit Price'] = validate_value(product, ['price', 'price_info', 'price_per_uom'])
                item['Unit'] = validate_value(product, ['price', 'price_info', 'sales_unit'])

                item['Home Bargains'] = 'YES' if '59600114' in product['item']['icons'] else 'NO'
                
                promotion = ''
                if 'promotion_info' in product and len(product['promotion_info']) > 0:
                    promo = product['promotion_info'][0]['linksave']
                    if promo:
                        promotion = promo.get('promo_detail', "")
                
                item['Promotion'] = promotion

                yield item
                self.logger.info(f"Scraped: {item['Product']} ({item['Product ID']})")

            if zone:
                max_pages = validate_value(zone, ['configs', 'max_pages'])
                current_page = validate_value(zone, ['configs', 'current_page'])

                if max_pages != 0 and current_page < max_pages:
                    url = 'https://groceries.asda.com/api/bff/graphql'
                    payload = get_products_payload(id, current_page+1)
                    yield scrapy.Request(url, method='POST', headers=self.headers, 
                                            body=json.dumps(payload), callback=self.parse_product,
                                            cb_kwargs={'id': id}, dont_filter=True)

        # except Exception as e:
        #     with open('error.json', 'w') as f:
        #         f.write(response.text)
        #     print(response.url)
        #     print(e)
        #     print(z)
        #     print(len(products))
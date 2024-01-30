import scrapy, json
from random import randint
from datetime import datetime, timedelta
from ..utils import get_header, get_taxonomy_formdata, get_cats_formadata

class ProductsSpider(scrapy.Spider):
    name = 'products'
    allowed_domains = ['www.tesco.com']
    start_urls = ['https://www.tesco.com/groceries/?icid=dchp_groceriesshopgroceries']


    def parse(self, response):
        csrf = response.xpath('.//body/@data-csrf-token').get()
        self.form_headers = get_header(csrf)
        
        data = get_taxonomy_formdata()
        url = 'https://www.tesco.com/groceries/en-GB/resources'
        j = json.dumps(data)
        yield scrapy.Request(url, method='POST', headers=self.form_headers, body=json.dumps(data), callback=self.parse_taxonomy)

    def parse_taxonomy(self, response):
        taxonomy = json.loads(response.text)
        datas = taxonomy['taxonomy']['data']

        for data in datas:
            url = data['children'][0]['url']
            department = url.split('/')[1]
            formdata = get_cats_formadata(department, 1, url)
            yield scrapy.Request(response.url, method='POST', headers=self.form_headers, body=json.dumps(formdata), callback=self.parse_products)

   
    def parse_products(self, response):
        data = json.loads(response.text)
     
        productItems = data['productsByCategory']['data']['results']['productItems']

        for item in productItems:
            promotions = item['promotions']
            if len(promotions) > 0:
                start_date = (datetime.strptime(promotions[0]['startDate'], '%Y-%m-%dT%H:%M:%SZ') + timedelta(hours=1)).strftime("%d/%m/%Y")
                end_date = datetime.strptime(promotions[0]['endDate'], '%Y-%m-%dT%H:%M:%SZ').strftime("%d/%m/%Y")
                promo_dates =  start_date + " To " + end_date
                promo = promotions[0]['offerText']
            else:
                promo_dates = 'NA'
                promo = 'NA'

            product = item['product']
            
            barcode = product['gtin'] + '\t'
            tpnb = product['id']
            title = product['title']
            category = product['superDepartmentName']
            department = product['departmentName']
            aisle = product['aisleName']
            price = product['price']
            unit_price = product['unitPrice']
            unit_measure = product['unitOfMeasure']

            try:
                if product['restrictions'][0]['message'] == 'Aldi Price Match':
                    aldi_price_match = 'Yes'
                else:
                    aldi_price_match = 'No'
            except:
                aldi_price_match = 'No'

            yield {
                'Barcode' : barcode,
                'TPNB' : tpnb,
                'Category' : category,
                'Department' : department,
                'Aisle' : aisle,
                'Product Name' : title,
                'Price (£)' : price,
                'Unit Price (£)' : unit_price,
                'Unit Of Measure' : unit_measure,
                'Promo' : promo,
                'Promo Dates' : promo_dates,
                'Aldi Price Match' : aldi_price_match
            }

        page_info = data['productsByCategory']['data']['results']['pageInformation']
        offset = page_info['offset']
        count = page_info['count']
        total = page_info['totalCount']

        if offset + count < total:
            page = page_info['pageNo'] + 1
            url = response.url
            department = data['productsByCategory']['params']['superdepartment']
            
            formdata = get_cats_formadata(department, page, url)
            yield scrapy.Request(url, method='POST', headers=self.form_headers, body=json.dumps(formdata), callback=self.parse_products)





            


        

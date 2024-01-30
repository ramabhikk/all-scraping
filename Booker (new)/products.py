import scrapy
from urllib.parse import parse_qs, quote, urlsplit
from scrapy.crawler import CrawlerProcess
import csv

headers_csv =['Barcode', 'Product ID', 'Product Name', 'Description', 'Wholesale Price', 'Packet Format', 'Vat', 'On Promo', 'Promotional Price']
csvfile = open('bookers.csv', 'w', newline='',encoding='utf-8-sig')
writer = csv.DictWriter(csvfile,fieldnames=headers_csv)
writer.writeheader()
csvfile.flush()

CUST_NO = 310101063
EMAIL = '736679498'
PASS = 'Costcutter.1!'


def get_description(lines):
    description = ''
    for line in lines:
        description += line.strip()
    description = description.replace('\n', ' ').replace('Show less...', '')
    description = ' '.join(description.split())
    description = description if description else 'N/A'
    return description


class ProductsSpider(scrapy.Spider):
    name = 'products'
    # allowed_domains = ['www.booker.co.uk']

    def start_requests(self):
        yield scrapy.Request(url="https://www.booker.co.uk/home")

    def parse(self,response):
        token = response.css("input[name='__RequestVerificationToken']::attr(value)").get()
        formdata = {
            'ReturnUrl': '',
            'uid': '9265a4ca-929d-44b8-96bc-a6d354033f60',
            '__RequestVerificationToken' :token,
            'CustomerNumber': ' 310101063',
            'Email': 'jpchadha@gmail.com',
            'Password': 'gurdwara'
        }
        yield scrapy.FormRequest('https://www.booker.co.uk/login', formdata=formdata, callback=self.parse_data,meta={'token':token})

    def parse_data(self, response):
        yield scrapy.Request('https://www.booker.co.uk/products/categories',callback=self.parse_category,meta={'token':response.meta['token']})

    def parse_category(self, response):
        if 'Website%20Bulletin' in response.url:
            formdata = {
                'ContinueUrl': response.xpath('//input[@id="ContinueUrl"]/@value').get(),
                'Content': response.xpath('//input[@id="Content"]/@value').get(),
                'uid': response.xpath('//input[@id="uid"]/@value').get(),
                'IsRead': 'true'
            }
            yield scrapy.FormRequest('https://www.booker.co.uk/Website%20Bulletin', dont_filter=True, formdata=formdata,
                                     callback=self.parse_category)
        else:
            categories = response.xpath('//a[@class="departmentItemx "]/@href').getall()

            formdata = {
                'ReturnUrl': '',
                'uid': '9265a4ca-929d-44b8-96bc-a6d354033f60',
                '__RequestVerificationToken' :response.meta['token'],
                'CustomerNumber': ' 310101063',
                'Email': 'jpchadha@gmail.com',
                'Password': 'gurdwara'
            }

            ########### Limit Categories here ###########
            for i, cateogry in enumerate(categories):
                parsed = urlsplit(cateogry)
                query_dict = parse_qs(parsed.query)
                categoryName = query_dict['categoryName'][0]
                return_url = quote(cateogry)
                url = f'https://www.booker.co.uk/products/print-product-list-ungroup?printType=ProductList&categoryName={categoryName}&pr=%7BminPrice%3A0%2CmaxPrice%3A0%7D'

                login = 'https://www.booker.co.uk/login'
                # yield scrapy.Request(url='https://www.booker.co.uk'+cateogry ,callback=self.login_again,)
                yield scrapy.FormRequest(login, formdata=formdata,
                                         meta={'Referer': cateogry, 'URL': url, 'cookiejar': i},
                                         callback=self.login_again, dont_filter=True)

    def login_again(self, response):

        token = response.css("input[name='__RequestVerificationToken']::attr(value)").get()
        formdata = {
            'ReturnUrl': '',
            'uid': '9265a4ca-929d-44b8-96bc-a6d354033f60',
            '__RequestVerificationToken': token,
            'CustomerNumber': ' 310101063',
            'Email': 'jpchadha@gmail.com',
            'Password': 'gurdwara'
        }
        login = 'https://www.booker.co.uk/login'
        yield scrapy.FormRequest(login, formdata=formdata,
                                 meta={'Referer': response.meta["Referer"], 'URL': response.meta["URL"], 'cookiejar': response.meta['cookiejar']},
                                 callback=self.new_login, dont_filter=True)

    def new_login(self,response):
        meta = {'Referer': response.meta['Referer'], 'URL': response.meta['URL'],
                'cookiejar': response.meta['cookiejar']}
        yield response.follow(response.meta['Referer'], callback=self.to_print_list, meta=meta)

    def to_print_list(self, response):
        meta = {'Referer': response.meta['Referer'], 'URL': response.meta['URL'],
                'cookiejar': response.meta['cookiejar']}
        yield response.follow(response.meta['URL'], meta=meta, callback=self.parse_print_list)

    def parse_print_list(self, response):
        rows = response.xpath('//table[@class="table-desktop"]/tbody/tr')
        prs = {}
        for row in rows:
            barcode = row.xpath('.//td/*[@class="barcode"]/@jsbarcode-value').get()
            pro_code = int(row.xpath('.//td[not(@id) and not(@class)]/text()').get())
            pack_format = row.xpath('.//td[@id="packsize"]/text()').get()
            tds = row.xpath('.//td[contains(@class,"text-right")]/text()').getall()
            wholesale = tds[1]
            vat = tds[3]
            barcode = barcode + '\t' if barcode else 'N/A'
            prs[pro_code] = {
                'Barcode': barcode,
                'Product ID': pro_code,
                'Wholesale Price': wholesale,
                'Packet Format': pack_format,
                'Vat': vat
            }

        meta = {'Products': prs, 'cookiejar': response.meta['cookiejar']}
        yield response.follow(response.meta['Referer'], meta=meta, callback=self.parse_product_list, dont_filter=True)

    def parse_product_list(self, response):
        meta = {'Products': response.meta['Products'], 'cookiejar': response.meta['cookiejar']}
        products = response.xpath('//div[contains(@class,"product-image")]/a/@href').getall()
        for product in products:
            yield response.follow(product, meta=meta, callback=self.parse_product)

        next = response.xpath('//a[@rel="next"]/@href').get()
        if next:
            yield response.follow(next, meta=meta, callback=self.parse_product_list)

    def parse_product(self, response):
        name = response.xpath('//h4[@class="d-inline pr-2 font-weight-bold"]/text()').get().strip()
        id_ = int(response.xpath('//h4[contains(@class,"product-id")]/text()').get().strip())
        description = get_description(response.xpath('//div[@id="product-details-show-more"]/p/text()').getall())
        promo_price = response.xpath('//span[@class="discount font-weight-bold"]/text()').get()
        if promo_price:
            on_promo = 'Yes'
        else:
            promo_price = 'N/A'
            on_promo = 'No'

        product = response.meta['Products'][id_]
        item = {
            'Barcode': product['Barcode'],
            'Product ID': id_,
            'Product Name': name,
            'Description': description,
            'Wholesale Price': product['Wholesale Price'],
            'Packet Format': product['Packet Format'],
            'Vat': product['Vat'],
            'On Promo': on_promo,
            'Promotional Price': promo_price
        }
        writer.writerow(item)
        csvfile.flush()


process = CrawlerProcess({
    'USER_AGENT': 'Mozilla/4.0 (compatible; MSIE 7.0; Windows NT 5.1)'
})
process.crawl(ProductsSpider)
process.start()
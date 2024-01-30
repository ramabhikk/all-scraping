import scrapy

class ProductsSpider(scrapy.Spider):
    name = 'products'
    allowed_domains = ['www.savageandwhitten.com']
    start_urls = ['https://www.savageandwhitten.com/login']

    USNM = 'b01056'
    PASSWD = 'hamiltonsbawn'
    BASE_URL = 'https://www.savageandwhitten.com'

    def parse(self, response):
        token = response.xpath('//input[@name="__RequestVerificationToken"]/@value').get()
        login_url = response.xpath('//input[@name="__RequestVerificationToken"]/parent::form/@action').get()

        data = {
                '__RequestVerificationToken' : token,
                'Username' : self.USNM,
                'Password' : self.PASSWD,
                'X-Requested-With' : 'XMLHttpRequest'
            }

        login_url = self.BASE_URL + login_url
        yield scrapy.FormRequest(login_url, formdata=data, callback=self.parse_login)
    
    def parse_login(self, response):
        self.logger.info("Logged in")
        url = self.BASE_URL
        yield scrapy.Request(url, callback=self.parse_main_page)
    
    def parse_main_page(self, response):
        departments = response.xpath('//div[@id="department-dropdown"]/a/@href').getall()
    
        for department in departments:
            url = self.BASE_URL + department
            yield scrapy.Request(url, callback=self.parse_department)

    def parse_department(self, response):
        categories = response.xpath('//div[contains(@class,"subnavitem")]//li/a[not(text()="View all")]/@href').getall()

        for category in categories:
            url = self.BASE_URL + category + '&SortingOption=Description%20ascending&PageSize=48&Page=1'
            yield scrapy.Request(url, callback=self.parse_category)

    def parse_category(self, response):
        category = response.xpath('//div[@class="c-breadcrumbs"]//li/p/text()').get()
        category = category.split('-')[-1].strip()

        products = response.xpath('//form[contains(@class,"c-product-item-card")]/a/@href').getall()

        for product in products:
            url = self.BASE_URL + product
            yield scrapy.Request(url, meta={'category':category}, callback=self.parse_product)

        next = response.xpath('//div[contains(@class,"pagination")]//img[not(@class="pageination-prev")]/parent::a/@href').get()
        if next:
            url = self.BASE_URL + next
            yield scrapy.Request(url, callback=self.parse_category)
    
    def parse_product(self, response):
        department = response.xpath('//button[contains(@class,"btn--department-selector")]/text()').get()
        category = response.meta['category']

        title = response.xpath('//h1/text()').get()
        product_code = response.xpath('//span[@class="_product-code"]/text()').get()
        
        pack_size = response.xpath('//td[text()="Size"]/following-sibling::td/text()').get()
        ws_size = response.xpath('//td[text()="Pack Qty."]/following-sibling::td/text()').get()

        ean_code = response.xpath('//td[text()="EAN Code"]/following-sibling::td/text()').get()
        outer_barcode = response.xpath('//td[text()="Outer Barcode"]/following-sibling::td/text()').get()

        ean_code = str(ean_code) + '\t'
        outer_barcode = str(outer_barcode) + '\t'

        price = response.xpath('//td[text()="Price"]/following-sibling::td/text()').get()
        rrp_por = response.xpath('//p[@class="_product-price"]/following-sibling::p/text()').get()
        rrp_por = rrp_por.split('POR')
        rrp = rrp_por[0].replace('RRP', '').strip()
        por = rrp_por[1].replace('%', '').strip()

        shelf_life = response.xpath('//p[@class="_product-size"]/text()').get()
        shelf_life = shelf_life.replace('Min Shelf Life(days)','').strip() if shelf_life else 0

        promo = response.xpath('//*[contains(text(),"Price Promotion")]').get()
        promo = 'Y' if promo else 'N'

        stock = response.xpath('//p[contains(@class,"u-normal u-text-small u-c")]/text()').get()
        stock = stock if stock else "NA"

        yield {
            'ProdCode' : product_code,
            'Description' : title,
            'WS Size' : ws_size,
            'Pack Size' : pack_size,
            'Price' : price,
            'RRP' : rrp,
            'POR' : por,
            'Min Shelf Life (days)' : shelf_life,
            'Marked as Promo' : promo,
            'In Stock' : stock,
            'Inner Barcode' : ean_code,
            'Outer Barcode' : outer_barcode,
            'Product Group' : category,
            'Category' : department
        }

        self.logger.info(f"Scraped: {title} ({product_code})")
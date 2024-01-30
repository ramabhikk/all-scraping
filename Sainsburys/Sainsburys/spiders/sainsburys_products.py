import scrapy

def extract_from_xpath(data, xpath):
    value = data.xpath(xpath).get()
    if value:
        return value.strip()
    return value


class SainsburysProductsSpider(scrapy.Spider):
    name = 'sainsburys_products'
    allowed_domains = ['www.sainsburys.co.uk']
    start_urls = ['https://www.sainsburys.co.uk/shop/gb/groceries']


    def parse(self, response):        
        categories = response.xpath('//ul[@id="megaNavLevelOne"]/li//@href').getall()
        
        for category in categories[:]:
            if 'https' not in category:
                category = 'https://www.sainsburys.co.uk' + category
            yield scrapy.Request(category, callback=self.parse_department)

    
    def parse_department(self, response):
        departments = response.xpath('//ul[@class="categories departments"]/li//@href').getall()
        
        if departments:
            for department in departments:
                if 'https' not in department:
                    department = 'https://www.sainsburys.co.uk' + department
                yield scrapy.Request(department, callback=self.parse_aisle)

        elif response.xpath('//li[@class="gridItem"]'):
            self.parse_product(response)


    
    def parse_aisle(self, response):
        aisles = response.xpath('//ul[@class="categories aisles"]/li//@href').getall()
        
        if aisles:
            for aisle in aisles:
                if 'https' not in aisle:
                    aisle = 'https://www.sainsburys.co.uk' + aisle
                yield scrapy.Request(aisle, callback=self.parse_shelf)
        elif response.xpath('//li[@class="gridItem"]'):
            self.parse_product(response)



    def parse_shelf(self, response):
        shelfs = response.xpath('//ul[@class="categories shelf"]/li//@href').getall()
        
        if shelfs:
            for shelf in shelfs:
                if 'https' not in shelf:
                    shelf = 'https://www.sainsburys.co.uk' + shelf
                yield scrapy.Request(shelf, callback=self.parse_product)
        elif response.xpath('//li[@class="gridItem"]'):
            self.parse_product(response)


    def parse_product(self, response):
        category = extract_from_xpath(response, '//ul[@id="breadcrumbNavList"]/li[1]/a//text()')
        sub_category = extract_from_xpath(response, '//ul[@id="breadcrumbNavList"]/li[2]/a//text()')

        products = response.xpath('//li[@class="gridItem"]')

        for product in products:
            item = {}

            item['Product ID'] = extract_from_xpath(product, './/div[@class="pricingAndTrolleyOptions"]//form[@class="addToTrolleyForm"]/input[@name="SKU_ID"]/@value')
            item['Category'] = category
            item['Sub Category'] = sub_category
            item['Product'] = extract_from_xpath(product, './/h3/a/text()')
            item['Price'] = extract_from_xpath(product, './/div[@class="pricingAndTrolleyOptions"]//p[@class="pricePerUnit"]/text()')
            item['Unit Price'] = extract_from_xpath(product, './/div[@class="pricingAndTrolleyOptions"]//p[@class="pricePerMeasure"]/text()')
            item['Unit'] = extract_from_xpath(product, './/div[@class="pricingAndTrolleyOptions"]//span[@class="pricePerMeasureMeasure"]/text()')

            price_lock = product.xpath('.//img[@alt="Price Lock*"]')
            aldi_price = product.xpath('.//img[@alt="ALDI PRICE MATCH*"]')

            item['Price Lock'] = 'YES' if price_lock else 'NO'
            item['ALDI PRICE MATCH'] = 'YES' if aldi_price else 'NO'

            yield item
            self.logger.info(f"Scraped: {item['Product']} ({item['Product ID']})")

        
        next = response.xpath('//li[@class="next"]/a/@href').get()
        if next:
            yield scrapy.Request(next, callback=self.parse_product)

import scrapy, time, datetime
from ..utils import POST_URL, get_post_data, get_base_id, get_barcode, get_validity, get_unit_measure

TODAY = datetime.datetime.today().strftime('%Y-%m-%d')

class ProductsSpider(scrapy.Spider):
    name = 'products'
    allowed_domains = ['www.tesco.ie']
    start_urls = ['https://www.tesco.ie/groceries/']

    def parse(self, response):
        categories = response.xpath('//ul[@class="navigation Groceries"]/li/a/@href').getall()

        for category in categories:
            timestamp = int(time.time() * 1000)
            category = category.replace('&', '&amp;')
            data = get_post_data(timestamp, category)
            yield scrapy.Request(POST_URL, method='POST', body=data, callback=self.parse_category, dont_filter=True)

    def parse_category(self, response):
        response = scrapy.Selector(text=response.text)
        sub_catagories = response.xpath('.//li/h3/a/@href').getall()
        for link in sub_catagories:
            yield scrapy.Request(link, callback=self.parse_products, dont_filter=True)

    def parse_products(self, response):
        show_more = response.xpath('//div[@class="pagination"]/a/text()').get()
        
        if show_more and 'Show more' in show_more:
            show_more = response.xpath('//div[@class="pagination"]/a/@href').get()
            yield scrapy.Request(show_more, callback=self.parse_products, dont_filter=True)
        else:
            metadata = response.xpath('//span[@type="CSP_DOM_Product_MetaData"]/metadata/text()').get()
            base_ids = get_base_id(metadata)

            products = response.xpath('//ul[@class="cf products line"]/li')
            for product in products:
                name = product.xpath('.//h3/a/text()').get().strip()
                url = response.urljoin(product.xpath('.//h3/a/@href').get().strip())
                product_id = product.xpath('.//h3/a/@id').get().split('-')[1].strip()
                
                base_id = base_ids[product_id]
                barcode = get_barcode(product.xpath('.//h3//span[contains(@class,"image")]/img/@src').get())
                
                available = 'False' if product.xpath('.//p[@class="noStockTxtCentered active"]').get() else 'True'
                
                price = product.xpath('.//span[@class="linePrice"]/text()').get().strip().replace('€','')
                unit_measure = get_unit_measure(product.xpath('.//span[@class="linePriceAbbr"]/text()').get())
                
                promo_text = product.xpath('.//a[@class="promoFlyout"]/em/text()').get()
                promo_text = promo_text if promo_text else 'NA'
                if promo_text != 'NA':
                    valid = product.xpath('.//div[@class="promo"]/span/text()').get()
                    valid_from, valid_to = get_validity(valid)
                else:
                    valid_from, valid_to = 'NA', 'NA'

                yield {
                    'ProductDescription' : name,
                    'TescoProductID' : product_id,
                    'BaseID' : base_id,
                    'SpecialOffer' : promo_text,
                    'OfferStartDate' : valid_from,
                    'OfferEndDate' : valid_to,
                    'WebLink' : url,
                    'CurrentlyAvailable' : available,
                    'Barcode' : barcode,
                    'Price' : price,
                    'UnitOfMeasure' : unit_measure,
                    'DateScraped' : TODAY
                }
                
                 
            next_ = response.xpath('//p[@class="next"]/a/@href').get()
            if next_:
                yield scrapy.Request(next_, callback=self.parse_products, dont_filter=True)
            




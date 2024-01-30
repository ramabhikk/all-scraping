import scrapy, datetime

TODAY = datetime.datetime.today().strftime("%d-%m-%Y")

def validate(field):
    if field:
        return field.strip()
    return 'NA'

def get_corrected_vat(vat_rate, rsp, por, order_size):
    try:
        if vat_rate == 'Standard':
            return round(((float(rsp) / 1 + 0.2) * (1.0 - float(por)/100.0)) *  float(order_size), 2)
        elif vat_rate == '12%':
            return round(((float(rsp) / 1 + 0.12) * (1.0 - float(por)/100.0)) *  float(order_size), 2)
        elif vat_rate == '5%':
            return round(((float(rsp) / 1 + 0.05) * (1.0 - float(por)/100.0)) *  float(order_size), 2)
        elif vat_rate == 'Exempt' or vat_rate == 'Zero':
            return round((float(rsp)) * (1.0 - float(por)/100.0) *  float(order_size), 2)
        return 'NA'
    except:
        return 'NA'
                


class ProductsSpider(scrapy.Spider):
    name = 'products'
    allowed_domains = ['www.bestwaywholesale.co.uk']
    start_urls = ['https://www.bestwaywholesale.co.uk/shop?records_per_page=100']

    def parse(self, response):
        categories = response.xpath('//nav/ul/li[position()>2 and position()<last()]/a/@href').getall()
        for category in categories:
            yield scrapy.Request(response.urljoin(category) , callback=self.parse_product_list)

    def parse_product_list(self, response):
        product_urls = response.xpath('//h2[@class="prodname"]/a/@href').getall()
        for url in product_urls:
            yield scrapy.Request(response.urljoin(url) , callback=self.parse_product)

        next_ = response.xpath('//li[@class="next"]/a[@class="icon-sprite2"]/@href').get()
        if next_:
            yield scrapy.Request(response.urljoin(next_), callback=self.parse_product_list)
        
    def parse_product(self, response):
        category = response.xpath('//div[@class="prodnav desktop"]/h1/text()').get()
        sub_category = response.xpath('//li[@class="toplevel"]/a/text()').get()
        product = validate(response.xpath('//h1[@class="prodname"]/text()').get())
        description = validate(response.xpath('//table[@class="prodtable"]//th[text()="Product:"]/following-sibling::td/text()').get())
        rsp = validate(response.xpath('//table[@class="prodtable"]//th[text()="RSP:"]/following-sibling::td/text()').get())
        por = validate(response.xpath('//table[@class="prodtable"]//th[text()="POR:"]/following-sibling::td/text()').get())
        pack_size = validate(response.xpath('//table[@class="prodtable"]//th[text()="Pack Size:"]/following-sibling::td/text()').get())
        product_code = validate(response.xpath('//table[@class="prodtable"]//th[text()="Product Code:"]/following-sibling::td/text()').get())
        ean = validate(response.xpath('//table[@class="prodtable"]//th[text()="Retail EAN:"]/following-sibling::td/text()').get()) + '\t'
        vat_rate = validate(response.xpath('//table[@class="prodtable"]//th[text()="Vat Rate:"]/following-sibling::td/text()').get())
        brand = validate(response.xpath('//table[@class="prodtable"]//th[text()="Brand:"]/following-sibling::td/text()').get())
        image_url = validate(response.xpath('//img[@id="prodimage"]/@src').get())

        wholesale = response.xpath('//div[@class="productpagedetail-inner"]//p[@class="prodsize"]/text()').get()
        order_size = wholesale.split('×')[1].strip()
        
        on_promo = 'YES' if response.xpath('//span[@class="special"]').get() else 'NO'
        multi_buy = 'YES' if response.xpath('//span[@class="multibuy"]').get() else 'NO'

        multibuy_mechanic = response.xpath('//div[@class="prodmulti-details"]//text()').getall() if multi_buy == 'YES' else 'NA'
    
        rsp_value = rsp.replace('£','')
        por_value = por.replace('%','')
        calc_wholesale =  round((float(rsp_value) * (1.0 - float(por_value)/100.0)) *  float(order_size), 2) if rsp != 'NA' else 'NA'
        corrected_vat = get_corrected_vat(vat_rate, rsp_value, por_value, order_size)

        yield {
            'Product Code' : product_code,
            'Desc' : product,
            'Wholesale Size' : wholesale,
            'Order Size' : order_size,
            'Pack Size' : pack_size,
            'Retail EAN' : ean,
            'Vat Rate' : vat_rate,
            'Brand' : brand,
            'Price Promo' : on_promo,
            'Image URL' : image_url,
            'Subcat' : sub_category,
            'Category' : category,
            'RSP' : rsp,
            'POR' : por,
            'Calculated Wholesale Price': calc_wholesale,
            'Calculated Wholesale Price (Corrected VAT)': corrected_vat,
            'Multi Buy' : multi_buy,
            'Multi Buy Mechanic' : multibuy_mechanic,
            'Date Scraped' : TODAY
        }
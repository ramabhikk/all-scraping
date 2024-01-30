import scrapy, re

EMAIL = 'emmyb48@hotmail.co.uk'
PASSWORD = 'casson48'

def validate(text):
    if text:
        return text.strip()
    else:
        return 'NA'

class ProductsSpider(scrapy.Spider):
    name = 'products'
    allowed_domains = ['order.musgravemarketplace.ie']
    start_urls = ['https://order.musgravemarketplace.ie/easyorder/login']
    
    def parse(self, response):
        parm = response.xpath('//form[@class="login-form"]/input[@name="parm"]/@value').get()
        lang = response.xpath('//form[@class="login-form"]/input[@name="lang"]/@value').get()
        login = response.xpath('//form[@class="login-form"]/input[@name="login"]/@value').get()
        
        data = {'parm':parm, 'lang':lang, 'login':login, 'Email':EMAIL, 'password':PASSWORD, 'saveLogin': 'on'}
     
        yield scrapy.FormRequest('https://order.musgravemarketplace.ie/easyorder/index', formdata=data, callback=self.login)

    def login(self, response):
        with open('smp.html', 'w') as f:
            f.write(response.text)
        parms = response.xpath('//div[@id="listptr"]/ul/li/a/@onclick').getall()
        promotions = response.xpath('//div[@id="listptrcsp"]/ul/li/a/@onclick').getall()

        '''
        for promo in promotions:
            p = re.findall(r"\d+", promo)
            link = f"https://order.musgravemarketplace.ie/easyorder/INFOPR3?parm={p[0]}"
            yield scrapy.Request(link, callback=self.parse_category)
        '''
        for par in parms:
            p = re.findall(r"\d+", par)
            link = f"https://order.musgravemarketplace.ie/easyorder/INFOPR3?parm={p[0]}"
            yield scrapy.Request(link, callback=self.parse_category)
        

    def parse_category(self, response):
        product_links = response.xpath('//div[@class="list_self"]/a/@href').getall()
        
        for link in product_links:
            p_url = 'https://order.musgravemarketplace.ie/easyorder/' + link
            yield scrapy.Request(p_url, callback=self.parse_product)
        
        next_ = response.xpath('//a[contains(@class, "next-page")]')
        if next_:
            parm = re.findall(r"\d+", next_.xpath('@onclick').get())
            next_inputs = response.xpath('//form[@id="products-list"]//input')

            formdata = {}
            for inp in next_inputs:
                if inp.xpath('@name').get():
                    formdata[inp.xpath('@name').get()] = inp.xpath('@value').get()
                else:
                    formdata[inp.xpath('@id').get()] = inp.xpath('@value').get()
            formdata['parm'] = parm
            formdata['subsetaction']= 'PAGEDN'
            formdata['ajax'] = '1'
            formdata['mode'] = ''
            formdata['catSrchTrms'] = ''
        
            yield scrapy.FormRequest('https://order.musgravemarketplace.ie/easyorder/infopr3', formdata=formdata, callback=self.parse_category, dont_filter=True)
        
        
    def parse_product(self, response):
        category = validate(response.xpath('(//div[@class="breadcrumbs-holder"]/ul/li/a/text())[1]').get())
        if category.lower() == 'home':
            category = validate(response.xpath('(//div[@class="breadcrumbs-holder"]/ul/li/a/text())[2]').get())
        title = validate(response.xpath('//h1[@id="prod_desc"]/text()').get()).replace('#html_prod_desc;>', '')
        size = validate(response.xpath('//tr[@id="prd-price"]/td/text()').get())
        rrp = validate(response.xpath('//tr[@id="prod_rrp"]/td/text()').get()).replace(u'\xa0', '')
        pro_code = validate(response.xpath('//tr[@id="prod_code"]/td/text()').get())
        stock = validate(response.xpath('(//div[@id="prod_stock_service"]/text())[2]').get())
        price = validate(response.xpath('//div[@id="prod_price"]//span/text()').get()).replace(u'\xa0', '')
        description = validate(response.xpath('//div[@id="description"]/span/text()').get()).replace('\n', ' ')
        ean_code = validate(response.xpath('//th[text()="EAN code:"]/following-sibling::td/text()').get()) + '\t'
        brand = validate(response.xpath('//th[text()="Brand:"]/following-sibling::td/text()').get())
        vat = validate(response.xpath('//td[text()="VAT:"]/following-sibling::td/text()').get())
          
        yield {
            "Category" : category,
            "Product Code" : pro_code,
            "EAN Code" : ean_code,
            "Product Name" : title,
            "Product Size" : size,
            "RRP" : rrp,
            "Price" : price,
            'VAT' : vat,
            "Stock Service" : stock,
            "Brand" : brand,
            "Description" : description,
        }



 


def get_exact_field(response, field):
    try:
        value = response.xpath(f'//td[text()="{field}"]/following-sibling::td/text()').get()
        return value if value else 'NA'
    except:
        return 'NA'

def get_contains_field(response, field):
    try:
        value = response.xpath(f'//td[contains(text(),"{field}")]/following-sibling::td/text()').get()
        return value if value else 'NA'
    except:
        return 'NA'

def get_dash_field(response, field):
    field = field.replace(' to ','-')
    try:
        value = response.xpath(f'//td[text()="{field}"]/following-sibling::td/text()').get()
        return value if value else 'NA'
    except:
        return 'NA'

def get_people_other(response):
    try:
        value = response.xpath('(//*[@id="people"]//table)[6]//td[text()="Other"]/following-sibling::td/text()').get()
        return value if value else 'NA'
    except:
        return 'NA'

def get_culture_other(response):
    try:
        value = response.xpath('(//*[@id="culture"]//table)[1]//td[text()="Other"]/following-sibling::td/text()').get()
        return value if value else 'NA'
    except:
        return 'NA'

def get_country_other(response):
    try:
        value = response.xpath('(//*[@id="culture"]//table)[2]//td[text()="Other"]/following-sibling::td/text()').get()
        return value if value else 'NA'
    except:
        return 'NA'

def get_emp_other(response):
    try:
        value = response.xpath('(//*[@id="employment"]//table)[1]//td[text()="Other"]/following-sibling::td/text()').get()
        return value if value else 'NA'
    except:
        return 'NA'


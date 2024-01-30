# -*- coding: utf-8 -*-
"""
Created on Mon Feb 17 16:15:36 2020

@author: Advent
"""

class start_bot:
    """
    A bot designed to scrape the NRA website (as of Feb 2020) for traffic and traffic site data and output it to a path.
    """
    def __init__(self, driver, url = r'https://www.nratrafficdata.ie/c2/gmapbasic.asp?sgid=ZvyVmXU8jBt9PJE$c7UXt6'):
        self.url = url
        self.driver = driver
        self.driver.get(self.url)
                
    def find_element_by_id(self, element_id, inplace = True):
        """
        Wrapper function for the find element by id funciton associated with the selenium web driver 
        
        inputs:
            element_id, str: the id of the web element you wish to find
        """
        self.saved_element = self.driver.find_element_by_id(element_id)        
        if inplace == False:
           return self.saved_element
       
    def find_elements_by_id(self, elements_id, inplace = True):
        """
        
        Wrapper function for the find elements by id funciton associated with the selenium web driver 
        
        inputs:
            elements_id, str: the id of the web element you wish to find
            
        same as find element by id but returns list of all found elements
        
        """
        self.saved_elements = self.driver.find_elements_by_id(elements_id)        
        if inplace == False:
           return self.saved_element
           
    def get_site_info(self):
        """
        pulls the geo locations data from the NRA website header and returns a pandas DataFrame of the scraped info.
        """
        import json
        finder_text = 'var sites ='
        cleaned_text = self.driver.find_elements_by_xpath('//script[contains(text(), "' + finder_text + '")]')[0].get_attribute('innerHTML').split('var sites = ')[1].split('var nSites =')[0].split(';')[0]
        site_data = pd.DataFrame(json.loads(cleaned_text))
        return site_data
    
    def scrape_table_for_links(self, table_row_id_contains = 'table_row_NRA' ):
        """
        Scrapes the table containing all the site names etc for the links to all active sites.
        data is stores under self.links as a list.
        inputs:
            table_row_id_contains, str: a string with which to locate the rows in the table via an xpath search. the program also searches for the term 'calendarurl' to disambiguate
        """
        from tqdm import tqdm
        self.xpath = "//*[contains(@id, '"+ table_row_id_contains +"') and contains(@id, 'calendarurl')]"
        self.name_xpath = "//*[contains(@id, 'table_row_NRA_')]/td[2]"
        self.rows = self.driver.find_elements_by_xpath(self.xpath)
        self.names = self.driver.find_elements_by_xpath(self.name_xpath)
        self.links = []
        for i, td in enumerate(tqdm(self.rows)):
            if 'Superceeded' in self.names[i].text or 'Test' in self.names[i].text:
                continue # ignores any superceeded sites or test sites
            else:
                self.links.append(td.get_attribute('href'))
            
    def scrape_data_from_links(self, year, month):
        """
        visits each link in the self.links object created by the self.scrape_table_for_links method.
        
        inputs:
            month, int (1 - 12): The number of the month which data you wish to scrape
        """
        for link in self.links:
            try:
                self.driver.get(link)
                random_wait(wait_max=8, wait_min = 5)
                day_el = self.find_date_el_on_nra_page(year, month, 1)
                random_wait(wait_max=5, wait_min = 3, printq = False)
                day_el.click()
                excel_links = self.driver.find_elements_by_xpath('//img[@src="images/icons/xlsx.png"]')
                month_link = excel_links[4]
                random_wait(wait_max=5, wait_min = 3, printq = False)
                month_link.click()
                random_wait(wait_max=5, wait_min = 3, printq = False)
                try:
                    dissmisswarning = self.driver.find_element_by_xpath('//input[@onclick = "dismissExcelWarning(this)"]')
                    dissmisswarning.click()
                    random_wait(wait_max=4, wait_min = 2, printq = False)
                    continue_button = self.driver.find_element_by_xpath('//button[@onclick = "excelExport()"]')
                    continue_button.click()
                except:
                    #message on website has likely been cleared
                    pass
                    
            except Exception as e:
                print('The following error occured on the link:',link,'\n')
                print(e)
            
    def find_date_el_on_nra_page(self, year, month, day):
        """
        helper function to click on a date in the calender on the NRA website.
        inputs:
            month, int; the number of the month to click on
            day, int; the day of the above month to click on
        """
        year_on_page = self.driver.find_element_by_xpath('//div[@id = "year_0"]/b').text
        years_to_go_back = int(year_on_page) - int(year)
        for i in range(years_to_go_back):
            year_back_button = self.driver.find_element_by_xpath('//div[contains(@id, "year_minus1")]')
            year_back_button.click()
        month_el = self.driver.find_element_by_xpath('//div[@id = "month'+str(month-1)+'days_0"]')
        day_el = month_el.find_element_by_xpath('div[contains(text(), "'+str(day)+'")]')
        return day_el    

  
def random_wait(**kwargs):
    """
    A funciton that randomly samples (uniformly) between 2 ints given as the arguments min and max and waits that time in seconds.
    kwargs:
        wait_min/wait_max (seperate arguments) 2 ints that specify the boundaries for the random wait time. defaults are 2 and 15 seconds respectivley
    """
    import time, random
    min_t = kwargs.get('wait_min', 2); max_t = kwargs.get('wait_max', 15)
    wait_time = random.randrange (min_t,max_t,1)
    printq = kwargs.get('printq', True)
    if printq == True:
        print('waiting for',wait_time,'seconds...')
    time.sleep(wait_time)


if __name__ == '__main__':   
    import pandas as pd
    import datetime
    from selenium import webdriver
    from dateutil.relativedelta import relativedelta
    import sys, os
    
    arguments = sys.argv
    
    print(len(arguments)-1, "Arguments detected. if this isn't correct be careful how spaces are used, pass paths in commas like this: ':path\to\a file with spces in the name\n'")
    #argument layout should be month, download path
    today = datetime.datetime.today()
    try:
        month = int(arguments[1])
        print('Month number given as:',month,'this should be an integer between 1(Jan) - 12(Dec)\n')
    except IndexError:
        default_month = (today + relativedelta(months=-1)).month
        default_year = (today + relativedelta(months=-1)).year
        print('No month given, system says it is month number',default_month,'so using that\n')
        month = default_month 
        year = default_year
    try: 
        download_path = arguments[2]
        print('Download path given as:',download_path,'this should be a path to a folder ending with a / \n')
    except IndexError:
        default_outpath = os.path.join("Q:\WebScraping\Traffic Data IE", str(today.month) + '-' + str(today.year), "")
        try:
            os.mkdir(default_outpath)
        except FileExistsError:
            pass
        print('No path given, so will use default:',default_outpath,'\n')
        download_path = default_outpath
        

    
    # set options for the web scrape
    chrome_options = webdriver.ChromeOptions() 
    prefs = {'download.default_directory' : download_path,
             "profile.default_content_settings.popups": 0,
             "directory_upgrade": True}
    
    chrome_options.add_experimental_option('prefs', prefs)
    driver = webdriver.Chrome(r'C:\Users\Administrator\Documents\ChromeWebDriver\chromedriver', chrome_options=chrome_options)        
    driver.maximize_window()    
    #Run bot
    bot1 = start_bot(driver)
    site_data = bot1.get_site_info()
    site_data.drop(['node', 'parameters'], axis=1)
    site_data.to_csv(os.path.join(download_path,'Location_data.csv'))
    del site_data
    
    bot1.find_element_by_id('gmapbasic_showList')
    bot1.saved_element.click()
    bot1.scrape_table_for_links()
    bot1.scrape_data_from_links(year, month)

    driver.quit()
#%%
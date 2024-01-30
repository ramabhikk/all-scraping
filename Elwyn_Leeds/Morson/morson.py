import requests
import dateparser
import datetime
from lxml.html import fromstring
import urllib.parse
import re
import json
import pandas as pd

import logging
# logging.basicConfig(level=logging.DEBUG, filemode='w', format='%(asctime)s - %(message)s', datefmt='%d-%b-%y %H:%M:%S')

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s",
                        datefmt='%d-%b-%y %H:%M:%S',
                        handlers=[
                            logging.FileHandler("./logs/morson.log"),
                            logging.StreamHandler()
                        ]
                    )

class MorsonCrawler():
    """This is a Crawler class writen to crawl job posts from "www.morson.com"
    All HTTP Request to website are made using Requests module.
    Parsing of HTML Response from the requests made are converted to lxml etree object for parsing
    Extracting facts/fields of the lxml elements using XPATH

    :param start_url: URL to begin the crawl, optimally job posts listing webpage
    :type start_url: str
    :param limit_days: Limiting jobs for x number of days, defaults to 
    :type limit_days: int, optional
    :param sector_file: Path to morson sector mapping json file, defaults to "./morson_sector.json"
    :type sector_file: str, optional
    :param with_session: Additional configuration for request module, enabling session increase crawl ra, defaults to False
    :type with_session: bool, optional
    """
    

    def __init__(self, start_url, limit_days=7, 
                 sector_file="./morson_sector.json", with_session=False) -> None:
        """Constructor method
        Intialising the crawler class.
        All the configurations set while initiaing the class are set as class property.
        Additional properties set are: 
        BASE_URL = 'https://www.morson.com'
        TIMEOUT = 30 --- timeout for fetching http request
        """
        self.BASE_URL = 'https://www.morson.com'
        self.TIMEOUT = 30
        self.start_url = start_url
        self.limit_days = datetime.datetime.today() - datetime.timedelta(days=limit_days)
        self.limit_reached = False
        self.sector_filename = sector_file
        self.sectors = {}
        self.post_urls = []
        self.posts = []

        self.with_session = with_session
        
        # default headers for http requests made
        self.headers = {
            'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/110.0.0.0 Safari/537.36'
        }
        
        if with_session:
            self.session = requests.Session()

        logging.info(f"Intializing the crawler with configurations:")
        logging.info(f"Start URL: {start_url}")
        logging.info(f"Sector File: {sector_file}")
        logging.info(f"Limit Days: {limit_days}")
        logging.info(f"Session: {with_session}")
            
        
    def _request(self, url):
        """Makes HTTP request using requests module.
        Before making the http request url is converted to an absolute URL, with domain names added if not present.
        Returns html response

        :param url: A url to make HTTP Request
        :type url: str
        :return: A response object of Request module
        :rtype: class:`requests.models.Response`
        """
        url = self._absolute_url(url)
        logging.debug(f"[Request]: {url}")
        if self.with_session:
            # is session is enabled while intialising, request is made with a common session
            return self.session.get(url, headers=self.headers, timeout=self.TIMEOUT)
        else:
            return requests.get(url, headers=self.headers, timeout=self.TIMEOUT)


    def _extract_value_from_xpath(self, tree, xpath, default=''):
        """Extracting fact/value from the lxml element

        :param tree: lxml document_fromstring element
        :type tree: class:`lxml.html.HtmlElement`
        :param xpath: string of xpath to select/extract field
        :type xpath: str
        :param default: default value if the xpath selector has no value
        :type default: str
        :return: Extracted field
        :rtype: str
        """
        value = tree.xpath(xpath)
        if value:
            return value[0].strip()

        return default

    def _extract_all_value_from_xpath(self, tree, xpath, sep=' ', default=''):
        """Extracting all fact/value from the lxml element

        :param tree: lxml document_fromstring element
        :type tree: class:`lxml.html.HtmlElement`
        :param xpath: string of xpath to select/extract fields
        :type xpath: str
        :param sep: separator string for combining list of extracted fields
        :type sep: str
        :param default: default value if the xpath selector has no value
        :type default: str
        :return: Extracted field
        :rtype: str
        """
        value = tree.xpath(xpath)
        if value:
            #using string join methods, all strings/fields extracted are combined
            return sep.join(vlu.strip() for vlu in value if vlu.strip())

        return default

    def _elements_from_xpath(self, tree, xpath):
        """Extracting lxml element from source lxml element

        :param tree: lxml document_fromstring element
        :type tree: class:`lxml.html.HtmlElement`
        :param xpath: string of xpath to select/extract fields
        :type xpath: str
        :return: A list of Extracted lxml element if found else empty list
        :rtype: list
        """
        return tree.xpath(xpath)

    def _tree(self, response):
        """Convert HTML response to lxml element

        :param response: reponse obtained from http request made
        :type tree: class:`requests.models.Response`
        :return: converted lxml element
        :rtype: class:`lxml.html.HtmlElement`
        """
        return fromstring(response.text)
    
    def _absolute_url(self, url):
        """Converts relating URL to absolute url with domain name, if not there

        :param url: URL string (relative or absolute)
        :type tree: str
        :return: absolute URL
        :rtype: str
        """
        return urllib.parse.urljoin(self.BASE_URL, url) 
    
    def _fetch_post_urls(self):
        """A Private Funtion crawling from start url (job post lising page) and collects job post urls
            Pagination is also carried out, untill the job posts with limited days are collected.
        """
        url = self.start_url

        while True:
            logging.info(f"Fetching post urls: {url}")
            response = self._request(url)
            tree = self._tree(response)

            #collect posts element from the webpage using xpath
            posts = self._elements_from_xpath(tree, '//li[@class="job-result-item"]')
            for post in posts:
                #extract posts date from the webpage using post html element
                post_date = self._extract_value_from_xpath(post, './/li[@class="results-posted-at"]/text()')
                if post_date:
                    # if post date is found, convert to python datetime object for further comparision
                    post_date = post_date.replace('Posted','').strip()
                    post_date = dateparser.parse(post_date)

                    if post_date < self.limit_days:
                        # if extracted post date is less or comes before limit days, stop extracting further post urls
                        self.limit_reached = True
                        return
                    else:
                        # if extracted post date is after limit days, extract that post url and add to urls list
                        post_url = self._extract_value_from_xpath(post, './/div[@class="job-title"]/a/@href')
                        if post_url: self.post_urls.append(post_url)


            # Extract next page url with the follwoing xpath
            next_page = self._extract_value_from_xpath(tree, '//li[@data-pagination="next"]/a/@href')
            if self.limit_reached or not next_page:
                # if the limit day is reached or next page url is not found, exit from the loop
                break
            
            # set extracted next page url to url variable fro next loop
            url = next_page

    def _extract_salary(self, text):
        """Extracting Salary value from the given text

        :param text: text containg salary value
        :type text: str
        :return: Salary value
        :rtype: str
        """

        text = text.split('-')[-1]
        # using regex expresion to seprate numerical value from string
        pattern = r'[-+]?(?:\d*\.*\d+)'
        text = re.findall(pattern, text)
        
        if text:
            return text[0]
        return ''

    def _fetch_posts(self):
        """A Private Funtion crawling all job posts from collected post urls
            After crawling, post fileds are extracted and stored in a list.
            Job posts not meeting following criteria are skipped:
            • The job description includes iR-35 or iR35 or Umbrella or PAYE
            • The job description includes month or months
            • The job description includes per day or per hour
        """
        for url in self.post_urls:
            logging.info(f"Fetching post data: {url}")
            response = self._request(url)
            
            rsp_text = response.text.lower()
            if 'ir-35' not in rsp_text and 'ir35' not in rsp_text and 'umbrella' not in rsp_text and 'paye' not in rsp_text:
                # If the job description not includes iR-35 or iR35 or Umbrella or PAYE, the loop/post is skipped
                logging.debug("[Skippikng Post] The job description includes iR-35 or iR35 or Umbrella or PAYE")
                continue

            tree = self._tree(response)

            #Extract json data avalible in webpage, 
            # this json string contains salary details, Job posted date and Job reference number
            script = self._extract_value_from_xpath(tree, '//script[@type="application/ld+json" and contains(text(),"JobPosting")]/text()')
            if script: script = json.loads(script)


            #Extracting job post fields with respective xpaths
            post = {}
            post['Job Title'] = self._extract_value_from_xpath(tree, '//h1/text()')
            post['Job Description'] = self._extract_all_value_from_xpath(tree, '//main[@data-element="job-description"]/article//text()', sep=' ')
            post['Job Location'] = self._extract_value_from_xpath(tree, '//li[@data-element="job-location"]/span[not (contains(text(),"Location"))]/text()')

            if script:
                if script['baseSalary']['value']['maxValue'] == 0: 
                    #If salary value is 0 in json data, then there will be no salary detais present in webpage, so skipped
                    logging.debug("[Skippikng Post] The job doesn't have Salary details")
                    continue

                salary = str(script['baseSalary']['value']['maxValue']) + " PER " + script['baseSalary']['value']['unitText']
            else:
                salary = self._extract_value_from_xpath(tree, '//li[@data-element="job-salary"]/span[not (contains(text(),"Salary"))]/text()')
                salary = self._extract_salary(salary)

            if 'per hour' not in salary.lower() and 'per day' not in salary.lower() and 'month' not in salary.lower(): 
                #If the job description not includes per day or per hour
                #Job posts are skipped
                logging.debug("[Skippikng Post] The job doesn't have valid Salary details")
                continue
            
            post['Gross Salary'] = salary

            #Payroll status based on keywords present in html text
            if 'umbrella' in rsp_text:
                post['Payroll Status'] = 'Umbrella PAYE'
            elif 'outside' in rsp_text:
                post['Payroll Status'] = 'Outside iR35'
            else:
                post['Payroll Status'] = 'Inside iR35'

            #Location Type based on keywords present in html text
            if 'hybrid' in rsp_text:
                post['Location Type'] = 'Hybrid'
            elif 'remote' in rsp_text or 'work from home' in rsp_text or 'wfh' in rsp_text:
                post['Location Type'] = 'Remote'
            else:
                post['Location Type'] = 'Onsite'


            # Extract Assignment Length numeric value from html text
            pattern = r'(\d+) month'
            length = re.findall(pattern, rsp_text)
            if not length: 
                #If the job description not includes month or months post is skipped
                logging.debug("[Skippikng Post] The job doesn't have Assignment Length details")
                continue

            if length[0] == '1':
                # if numeric value extracted is '1'
                post['Assignment Length'] = length[0] + ' month'
            else:
                post['Assignment Length'] = length[0] + ' months'

            # Extract Security Clearance Status value based on keywords present in html text
            if 'dbs' in rsp_text:
                post['Security Clearance Status'] = 'DBS Clearance Required'
            elif 'sc clear' in rsp_text:
                post['Security Clearance Status'] = 'SC Clearance Required'
            else:
                post['Security Clearance Status'] = ''

            post['Posted Date'] = script['datePosted'].split('T')[0] if script else ''
            post['Job Reference'] = script['identifier']['value'] if script else ''

            sector = self._extract_value_from_xpath(tree, '//ul[@data-element="job-details"]//li/*[contains(text(),"Sector:")]/following-sibling::span/a/text()')

            post['Sector'] = self.sectors.get(sector, '')
            post['Recruitment Agency'] = 'Morson'
            post['Recruiter Name'] = self._extract_value_from_xpath(tree, '//ul[@data-element="job-details"]//li/*[contains(text(),"Contact:")]/following-sibling::span/text()')
            post['Recruiter Email'] = self._extract_value_from_xpath(tree, '//ul[@data-element="job-details"]//li/*[contains(text(),"Contact Email")]/following-sibling::span/text()')
            post['Logo URL'] = 'https://images.app.goo.gl/iRrSMdME2D1A1b3d7'
            post['Post URL'] = self._absolute_url(url)

            #Adding scraped post to list
            self.posts.append(post)

    def _load_sector(self):
        """A private function to load sector details for mapping from a JSON file
        """
        try:
            self.sectors = json.load(open(self.sector_filename))
            logging.info("Loaded Sectors Succesfully")
        except Exception as e:
            logging.error("Error Loading Sector File. Skipping Sector fields")
            # print(e)

    def crawl(self):
        """Public function, when called starts the crawling process
        """
        logging.info("Starting Crawler")
        #Load the sector mapping details from json file
        self._load_sector()

        logging.info("Fetching post urls from listing pages")
        #Start fetching job posts urls
        self._fetch_post_urls()
        logging.info(f"Post urls found: {len(self.post_urls)}")

        logging.info("Fetching job post details")
        #Start fetching job posts details
        self._fetch_posts()
        
    def save_to_csv(self, output_filename=""):
        """Saving extracted job post details to a CSV file

        :param output_filename: csv output filename to be saved, defaults "Morson_(today's date).csv', example "Morson_20230726.csv"
        :type text: str
        """
        if not output_filename:
            today = datetime.datetime.today().strftime("%Y%m%d")
            output_filename = f'Morson_{today}.csv'
        df = pd.DataFrame(self.posts)

        logging.info(f"Saving job posts to {output_filename}")
        df.to_csv(output_filename, index=False)

    def save_to_json(self, output_filename=""):
        """Saving extracted job post details to a JSON file

        :param output_filename: JSON output filename to be saved, defaults "Morson_(today's date).json', example "Morson_20230726.JSON"
        :type text: str
        """
        if not output_filename:
            today = datetime.datetime.today().strftime("%Y%m%d")
            output_filename = f'Morson_{today}.json'
        
        logging.info(f"Saving job posts to {output_filename}")
        with open(output_filename, 'w') as f:
            json.dump(self.posts, f, indent=4)


if __name__ == '__main__':
    #initate Crawler class
    crawler = MorsonCrawler(start_url='https://www.morson.com/jobs', limit_days=7, sector_file="./morson_sector.json")

    #Starting crawl process
    crawler.crawl()

    #Save crawled data to csv file
    crawler.save_to_csv()

    #Save Crawled data to JSON file
    crawler.save_to_json()

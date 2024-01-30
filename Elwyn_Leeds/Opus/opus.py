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
                            logging.FileHandler("./logs/opus.log"),
                            logging.StreamHandler()
                        ]
                    )

class OpusCrawler():
    """This is a Crawler class writen to crawl job posts from "www.opusrecruitmentsolutions.com"
    All HTTP Request to website are made using Requests module.
    Parsing of HTML Response from the requests made are converted to lxml etree object for parsing
    Extracting facts/fields of the lxml elements using XPATH

    :param start_url: URL to begin the crawl, optimally job posts listing webpage
    :type start_url: str
    :param limit_days: Limiting jobs for x number of days, defaults to 
    :type limit_days: int, optional
    :param sector_file: Path to opus sector mapping json file, defaults to "./opus_sector.json"
    :type sector_file: str, optional
    :param with_session: Additional configuration for request module, enabling session increase crawl ra, defaults to False
    :type with_session: bool, optional
    """
    

    def __init__(self, start_url, limit_days=7, 
                 sector_file="./opus_sector.json", with_session=False) -> None:
        """Constructor method
        Intialising the crawler class.
        All the configurations set while initiaing the class are set as class property.
        Additional properties set are: 
        BASE_URL = 'https://www.opusrecruitmentsolutions.com'
        TIMEOUT = 30 --- timeout for fetching http request
        """
        self.BASE_URL = 'https://www.opusrecruitmentsolutions.com'
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

    def _extract_all_value_from_xpath(self, tree, xpath, join=True, sep=' ', default=''):
        """Extracting all fact/value from the lxml element

        :param tree: lxml document_fromstring element
        :type tree: class:`lxml.html.HtmlElement`
        :param xpath: string of xpath to select/extract fields
        :type xpath: str
        :param join: if true, extracted fields are combined to one dtring, else list of extracted string are returned
        :type join: bool
        :param sep: separator string for combining list of extracted fields
        :type sep: str
        :param default: default value if the xpath selector has no value
        :type default: str
        :return: Extracted field/list 
        :rtype: str or list
        """
        value = tree.xpath(xpath)
        if value:
            #using string join methods, all strings/fields extracted are combined
            if join:
                return sep.join(vlu.strip() for vlu in value if vlu.strip())
            return value

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
            Pagination is also carried out here.
        """
        url = self.start_url

        while True:
            logging.info(f"Fetching post urls: {url}")
            response = self._request(url)
            tree = self._tree(response)

            #extract all post urls from webpage with xpath
            post_urls = self._extract_all_value_from_xpath(tree, '//div[@class="job-listing"]/a/@href', join=False) 
            if post_urls: self.post_urls.extend(post_urls)

            # Extract next page url with the follwoing xpath
            next_page = self._extract_value_from_xpath(tree, '//li[@class="next"]/a/@href')
            
            if not next_page:
                # if next page url is not found, exit from the loop
                break
            
            # set extracted next page url to url variable fro next loop
            url = next_page



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
            # this json string contains Job Title, Salary details, Job posted date and Job reference number
            script = self._extract_value_from_xpath(tree, '//script[@type="application/ld+json" and contains(text(),"JobPosting")]/text()')
            if script: script = json.loads(script)


            #Extracting job post fields with respective xpaths
            post = {}
            post['Job Title'] = script['title']
            desctree = fromstring(script['description'])
            post['Job Description'] = self._extract_all_value_from_xpath(desctree, './/text()', sep=' ')
            post['Job Location'] = self._extract_value_from_xpath(tree, '//p[@class="location"]/text()')

            if script:
                if 'baseSalary' not in script: 
                    #there is no salary detais present in webpage, so skipped
                    logging.debug("[Skippikng Post] The job doesn't have Salary details")
                    continue
                try:
                    salary = str(script['baseSalary']['value']['maxValue']) + " PER " + script['baseSalary']['value']['unitText']
                except:
                    # some job posts have direct salary value
                    try:
                        salary = str(script['baseSalary']['value']) + " PER " + script['baseSalary']['value']['unitText']
                    except:
                        pass

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

            post_date = dateparser.parse(script['datePosted'])
            if post_date < self.limit_days:
                # if extracted post date is less or comes before limit days, stop extracting further post urls
                continue
                
            post['Posted Date'] = script['datePosted']
            post['Job Reference'] = script['identifier'] if script else ''

            sector = ''
            # secotr not availabel in webpage
            post['Sector'] = self.sectors.get(sector, '')
            post['Recruitment Agency'] = 'Opus'
            post['Recruiter Name'] = ''
            post['Recruiter Email'] = ''

            #extarct email from job description
            email = re.findall("([a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+)", script['description'])
            if email:
                # if email found extract recruiter name from it
                email = email[0]
                # split email with .
                recruiter_name = email.split('.')
                if len(recruiter_name) == 1:
                    # if . is not present in email, taking whole email before @ as recruiter name
                    recruiter_name = email.split('@')[0]
                else:
                    recruiter_name = recruiter_name[0]
                
                post['Recruiter Name'] = recruiter_name
                post['Recruiter Email'] = email
            
            post['Logo URL'] = 'https://images.app.goo.gl/mpYma9G1K4djA5Qx7'
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

        
    def save_to_csv(self, output_filename=""):
        """Saving extracted job post details to a CSV file

        :param output_filename: csv output filename to be saved, defaults "Opus_(today's date).csv', example "Opus_20230726.csv"
        :type text: str
        """
        if not output_filename:
            today = datetime.datetime.today().strftime("%Y%m%d")
            output_filename = f'Opus_{today}.csv'
        df = pd.DataFrame(self.posts)

        logging.info(f"Saving job posts to {output_filename}")
        df.to_csv(output_filename, index=False)

    def save_to_json(self, output_filename=""):
        """Saving extracted job post details to a JSON file

        :param output_filename: JSON output filename to be saved, defaults "Opus_(today's date).json', example "Opus_20230726.JSON"
        :type text: str
        """
        if not output_filename:
            today = datetime.datetime.today().strftime("%Y%m%d")
            output_filename = f'Opus_{today}.json'
        
        logging.info(f"Saving job posts to {output_filename}")
        with open(output_filename, 'w') as f:
            json.dump(self.posts, f, indent=4)


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

if __name__ == '__main__':
    #initate Crawler class
    crawler = OpusCrawler(start_url='https://www.opusrecruitmentsolutions.com/search-jobs/', 
                          limit_days=7, sector_file="./opus_sector.json", with_session=True)

    #Starting crawl process
    crawler.crawl()

    #Save crawled data to csv file
    crawler.save_to_csv()

    #Save Crawled data to JSON file
    crawler.save_to_json()

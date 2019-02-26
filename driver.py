# TODO: go on github and find the correct selenium import statements
from selenium import webdriver
from selenium.webdriver.chrome.options import Options

class Chrome(object):

    def __init__(self, **kwargs):
        # Add options to make chrome headless and run in background
    	self.chrome_options = Options()
    	self.chrome_options.add_argument('--headless')
    	self.chrome_options.add_argument('log-level=3')
    	self.chrome_options.add_argument('--disable-extensions')
    	self.chrome_options.add_argument('test-type')
        # Close browser if it is already open
        self._end_session()
        # Open a new browser
        self.start_session()

    def _end_session(self):
        try:
            self.driver.close()
        except:
            pass

    def start_session(self):
        # self.driver = webdriver.Chrome('chromedriver.exe', options=chrome_options)
        self.driver = webdriver.Chrome('../chromedriver')
        self.driver.get('https://www.google.com/')

    def goto(self, url):
        self.driver.get(url)
        sleep(2 + random.random() / 2) # This value can be whatever we want.  We
                                       # need some kind of pause mechanism in place.

    def xpath(self, path, isList=False, container=False):
        if isList:
            return self.driver.find_elements_by_xpath(path)
        else:
            return self.driver.find_element_by_xpath(path)

    def get_attribute(self, path, attr):
        return self.driver.xpath(path).get_attribute(attr)

    def get_attribute(self, **kwargs):
        if 'xpath' in kwargs.keys():
            return self.kwargs['xpath'].get_attribute(kwargs['attribute'])
        elif 'path' in kwargs.keys():
            return self.xpath(kwargs['path']).get_attribute(kwargs['attribute'])

    def get_text(self, **kwargs):
        if container in kwargs.keys():
            return self.lwargs]
        return self.xpath(path).text

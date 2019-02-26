import os
from selenium import webdriver
from selenium.webdriver.chrome.options import Options

class Chrome(object):

    def __init__(self, testing=None):
        self.testing = testing
        # Add options to make chrome headless and run in background
        self.chrome_options = Options()
        self.chrome_options.add_argument('--headless')
        self.chrome_options.add_argument('log-level=3')
        self.chrome_options.add_argument('--disable-extensions')
        self.chrome_options.add_argument('test-type')
        # Close browser if it is already open
        self._end_session()
        # Open a new browser
        self._start_session()

    def _end_session(self):
        try:
            self.driver.close()
        except:
            pass

    def _start_session(self):
        if self.testing:
            self.driver = webdriver.Chrome(os.getcwd() + '/chromedriver')
        else:
            self.driver = webdriver.Chrome(os.getcwd() + '/chromedriver', options=self.chrome_options)
        self.driver.get('https://www.google.com/')

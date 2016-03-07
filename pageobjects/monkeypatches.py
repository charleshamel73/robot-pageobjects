from selenium.webdriver.remote.webdriver import WebDriver as RemoteWebDriver
"""
This File is just so that we are able to override certain functions within Selenium2Library at runtime
"""


def do_monkeypatches():
    def _get_current_window_info(self):
        """
        This is a replacement for the Selenium2Library function that is 
        
        This fixes Selenium2Library issue 270 
        https://github.com/rtomac/robotframework-selenium2library/issues/270
        """

        # it's more efficient to get this data in one call to self.execute_script
        # but we're observing that under some circumstances that doesn't
        # work. Getting the values individually seems to work better.
        try:
            id_ = self.execute_script("return window.id")
        except:
            id_ = 'undefined'
        name = self.execute_script("return window.name")
        title = self.execute_script("return document.title")
        url = self.execute_script("return document.URL")

#        id_ = id_ if id_ is not None else 'undefined'
        name, title, url = (att if att else 'undefined' for att in (name, title, url))
        return self.current_window_handle, id_, name, title, url
    
    RemoteWebDriver.get_current_window_info = _get_current_window_info

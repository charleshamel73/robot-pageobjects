from Selenium2Library import Selenium2Library
from Selenium2Library.keywords import _browsermanagement
from selenium.webdriver.remote.webelement import WebElement
from abstractedlogger import Logger
from context import Context
from robot.api.deco import keyword
from optionhandler import OptionHandler
from robot.libraries.BuiltIn import BuiltIn
from exceptions import UriResolutionError
from yamlhandler import YAMLHandler
from keywordmanager import KeywordManager
from robothandler import RobotHandler
from monkeypatches import do_monkeypatches
from robot import utils
from robot.utils import asserts
import inspect
import re
import time
do_monkeypatches()


class Page(Selenium2Library, Logger):
    ROBOT_LIBRARY_SCOPE = 'TEST SUITE'
    def __init__(self):
        for base in Page.__bases__:
            base.__init__(self)
        self._robot_handler = RobotHandler(self)
        self._option_handler = OptionHandler(self)
        self._yaml_handler = YAMLHandler(self)

        try:
            self.name
        except AttributeError:
            self.name = self._titleize(self.__class__.__name__)

        # Required Attributes in options ##
        self.browser = self._option_handler.get("browser", None)
        self.baseurl = self._option_handler.get("baseurl", None)

        # Setting Up Optional Selenium2Library attributes with OptionHandler ##
        selenium_speed = self._option_handler.get("selenium_speed", 0)
        selenium_implicit_wait = self._option_handler.get("selenium_implicit_wait", 5)

        self.set_selenium_timeout(selenium_implicit_wait)
        self.set_selenium_implicit_wait(selenium_implicit_wait)
        self.set_selenium_speed(selenium_speed)

        _shared_cache = Context.get_cache()
        if _shared_cache is not None:
            self._cache = _shared_cache
        Context.set_cache(self._cache)

        if Context.in_robot():
            Context.set_current_page("pageobjects.Page")
        KeywordManager().add_page_methods(self)

##############################################################################
# ASSERTION METHODS                                                          #
##############################################################################
    def current_page_should_be(self, timeout=30):
        """
        Verify that the location of the current page corresponds to the given page.
        Example:
        | | | Current page should be Optimizer Dashboard

        :param timeout: the time to wait for current page should be(defaults to 30)
        :type timeout: int
        :return: current Page
        :rtype: Page
        """
        # Looking for master locator to load
        master_locator = self.get_locator('master')
        try:
            self.wait_until_element_is_visible(master_locator, timeout)
        except Exception, e:
            raise Exception("PAGE LOAD ERROR: %s" % str(e))
        # Asserting that we are at the correct URL
        current_location = self._get_page_location()
        asserts.assert_true(self.uri.lower() in current_location.lower(),
                            "Expected page uri to contain %s but it did not: %s" % (self.uri, current_location))
        return self

##############################################################################
#  PUBLIC  PAGE METHODS                                                      #
##############################################################################
    def wait_for_ready_state(self, state="complete", timeout=30, delay=3):
        """
        Wait until the document readyState is set to the given value
        The default state is "complete"
        Example:
        | | | Wait for ready state | complete

        :param state: the ready state of the page (Defaults to "complete")
        :type state: str
        :param timeout: the time to wait for current page should be(defaults to 30)
        :type timeout: int
        :param delay: the time to sleep between each loop (defaults to 3)
        :type delay: int
        :return: current Page
        :rtype: Page
        """
        ready = False
        count = 1
        while not ready:
            if count > timeout:
                raise Exception("JAVASCRIPT ERROR: Could not get ready state via javascript")
            else:
                try:
                    # Needed a special case for the edge case of DashboardPage as Dialog Box has no DOM object ##
                    self.driver.find_element_by_id("ftbSearchName", timeout=1)
                    ready_state = True
                except:
                    try:
                        ready_state = self.execute_javascript("return document.readyState === '%s';" % state)
                    except:
                        ready_state = False
                if ready_state:
                    ready = True
                else:
                    count += delay
                    time.sleep(delay)
        return self

    def get_locator(self, key):
        """
        Returns the locator with the given key

        :param key: the key for the locator
        :type key: str
        :return: locator if its found
        :raise Exception: Fails if not found
        """
        locator = self._yaml_handler.get_locator(key)
        if locator is None:
            raise Exception("LOCATOR ERROR: Found locator with key: '%s' with no value assigned in file '%s.yaml'"%(key,self.__class__.__name__))
        return locator

    def select_window_when_visible(self, win_name, timeout=30, delay=5):
        """
        This keyword will try to select a given window based on the
        title, name, or url that you give it.  it will try to do so
        for as long as your timeout argument.  If you don't specify,
        it will use 30 sec.

        :param win_name: name of the window
        :type win_name: str
        :param timeout: the time to wait for current page should be(defaults to 30)
        :type timeout: int
        :param delay: the time to sleep between each loop (defaults to 5)
        :type delay: int
        :return: current Page
        :rtype: Page
        """

        timeout = utils.timestr_to_secs(timeout)
        maxtime = time.time() + timeout
        visible = False
        while not visible:
            try:
                self.register_keyword_to_run_on_failure("Nothing")
                self.select_window(win_name)
                visible = True
            except:
                if time.time() > maxtime:
                    self.register_keyword_to_run_on_failure("Capture Page Screenshot")
                    raise Exception('Window, %s, did not appear' % win_name)
                else:
                    time.sleep(delay)
        self.register_keyword_to_run_on_failure("Capture Page Screenshot")
        return self

##############################################################################
# PRIVATE PYTHON METHODS                                                     #
##############################################################################
    def _titleize(self, string):
        """
        Converts camel case to title case

        :param string: the string to titleize
        :type string: str
        :return: string in title case
        :rtype: str
        """
        return re.sub('([a-z0-9])([A-Z])', r'\1 \2', re.sub(r"(.)([A-Z][a-z]+)", r'\1 \2', string))

    def _get_page_location(self, timeout=30, delay=3):
        """
        Return the URL of the page, regardless of the currently selected frame

        :param timeout: the time duration to wait till failing(Defaults 30)
        :type timeout: int
        :param delay: the time to wait between each check (Defaults 3)
        :type delay: int
        :return: current url
        :rtype: str
        """
        # Note: calling self.get_location() will return the iframe URL
        # if we're in an iframe. We can't unselect the frame since
        # 'func' may depend on it not changing. This bit of javascript should
        # give us the URI of the root page
        self.wait_for_ready_state("complete")
        getlocation = False
        current_location = None
        count = 1
        while not getlocation:
            if count > timeout:
                raise Exception("JAVASCRIPT ERROR: Could not get url value via javascript")
            else:
                current_location = self.execute_javascript("return document.location.href;")
                if current_location is not None:
                    getlocation = True
                else:
                    count += delay
                    time.sleep(delay)
        return current_location

    def _has_locator(self, name):
        """
        Checks to see if the locator with the given name exist in the list of locators

        :param name: the key of the locator to check out
        :type name: str
        :return: True if exist
        :rtype: bool
        """
        try:
            self.get_locator(name)
            return True
        except Exception:
            return False

    def _element_is_visible(self, locator_type, locator):
        """
        Returns True if the given webelement at the location is visible
        Must give locator_type with check

        :param locator_type: the type of locator("XPATH","CSS",..)
        :type locator_type: str
        :param locator: the locator to check
        :type locator: str
        :return: True if it is displayed
        :rtype: bool
        """
        webelement = self.driver.find_element(locator_type, locator)
        return webelement.is_displayed()

    def _get_parent_pages(self, include_self=True, top_to_bottom=False, include_top=False):
        """
        This method gets the page hierarchy of all parent pages

        :param include_self: True if you want to include current page(Default True)
        :type include_self: bool
        :param top_to_bottom: True if you want list to start from parent classes to children(Default False)
        :type top_to_bottom: bool
        :param include_top: True if you want to include Page and S2L/Logger Base Classes in the list
        :type include_top: bool
        :return: list of classes in the order requested
        :rtype: list of classes
        """
        parents = []
        stack = []
        stack.append(self.__class__)
        # Iterates up the tree till base class Page is reached
        while len(stack) > 0:
            current = stack.pop()
            if current is not Page or include_top:
                if current != self.__class__:
                    parents.append(current)
                elif current == self.__class__ and include_self:
                    parents.append(current)
                for parent in current.__bases__:
                    if parent not in parents and parent.__name__ != "object":
                        stack.append(parent)
        # Stack Begins Bottom to Top
        if top_to_bottom:
            parents.reverse()
        return parents

    def _get_child_pages(self, include_self=True, top_to_bottom=True):
        """
        This method gets the page hierarchy of all child pages

        :param include_self: True if you want to include current page(Default True)
        :type include_self: bool
        :param top_to_bottom: True if you want list to start from parent classes to children(Default True)
        :type top_to_bottom: bool
        :return: list of classes in the order requested
        :rtype: list of classes
        """
        children = []
        stack = []
        stack.append(self.__class__)
        # Iterates down the tree till base class Page is reached
        while len(stack) > 0:
            current = stack.pop()
            if current != self.__class__ or include_self:
                children.append(current)

            for child in current.__subclasses__():
                stack.append(child)
        # Stack Begins Top to Bottom
        if not top_to_bottom:
            children.reverse()
        return children

    def __file__(self):
        """
        Returns the location of the .pyc or .py file for this class
        """
        return inspect.getfile(self.__class__)

##############################################################################
# RF HOOK KEYWORDS                                                           #
##############################################################################
    def get_keyword_names(self):
        """
        RF Hook which just sends off all available keywords
        """
        keywords = KeywordManager().get_robot_keywords_for_page(self)
        return keywords

    def run_keyword(self, name, args, kwargs):
        """
        RF Dynamic API hook implementation that maps method names to their actual functions.

        :param name: The keyword name from robot
        :type name: str
        :param args: the args from robot
        :type args: list
        :param kwargs: a dict of additional args
        :type kwargs: dict
        :return: callable function
        :rtype: callable
        """
        # Translate back from Robot Framework name to actual method
        ret = None

        func_mapping = KeywordManager().get_meth_mapping_from_robot_alias(self, name)
        meth = func_mapping.func
        try:
            if "${" in func_mapping.func_alias:
                args = self._parse_embedded_args(name, func_mapping.func_alias)
            ret = meth(self, *args, **kwargs)
        except Exception, e:
            Context.set_current_page("automationpages.Page")
            # Pass up the stack, so we see complete stack trace in Robot trace logs
            BuiltIn().fail(str(e))

        if isinstance(ret, Page):
            libnames = Context.get_libraries()
            classname = ret.__class__.__name__
            for names in libnames:
                # If we find a match for the class name, set the pointer in Context.
                if names.split(".")[-1:][0] == classname:
                    Context.set_current_page(names)

        if ret is None:
            func = meth.__name__
            if func in Selenium2Library.__dict__.values():
                ret = self
            else:
                for base in Selenium2Library.__bases__:
                    if func in base.__dict__.values():
                        ret = self
                        break

        return ret
    
    def get_keyword_documentation(self, kwname):
        """
        RF Dynamic API hook implementation that exposes keyword documentation to the libdoc tool

        :param kwname: a keyword name
        :return: a documentation string for kwname
        """
        """
        RF Dynamic API hook implementation that exposes keyword documentation to the libdoc tool

        :param kwname: a keyword name
        :return: a documentation string for kwname
        """
        if kwname == '__intro__':
            docstring = self.__doc__ if self.__doc__ else ''
            s2l_link = """\n
            All keywords listed in the Selenium2Library documentation are stored within class Page
            """
            return docstring + s2l_link
        func_mapping = KeywordManager().get_meth_mapping_from_robot_alias(self, kwname)
        kw = func_mapping.func
        docstring = kw.__doc__ if kw.__doc__ else ''
        docstring = re.sub(r'(wrapper)', r'*\1*', docstring, flags=re.I)
        return docstring

    def get_keyword_arguments(self, kwname):
        """
        RF Dynamic API hook implementation that exposes keyword argspecs to the libdoc tool

        :param kwname: a keyword name
        :return: a list of strings describing the argspec
        """
        func_mapping = KeywordManager().get_meth_mapping_from_robot_alias(self, kwname)
        kw = func_mapping.func
        if kw:
            args, varargs, keywords, defaults = inspect.getargspec(kw)
            defaults = dict(zip(args[-len(defaults):], defaults)) if defaults else {}
            arglist = []
            for arg in args:
                if arg != 'self':
                    argstring = arg
                    if arg in defaults:
                        argstring += '=%s' % defaults[arg]
                    arglist.append(argstring)
            if varargs:
                arglist.append('*args')
            if keywords:
                arglist.append('**keywords')
            if "${" in func_mapping.func_alias:
                arglist.remove('pagename')
            return arglist
        else:
            return ['*args']

    def _parse_embedded_args(self, robot_input, func):
        """
        This method parses the given input for embedded arguments("${...}") using the base function
        Currently replaces any instance of ${pagename} with the name of the given page(page().name)

        :param robot_input: the method given by robot
        :type robot_input: str
        :param func: the name of the function alias
        :type func: str
        :return: list of arguments
        :rtype: list of values
        """
        args = []
        if "${" not in func:
            return args
        input_split = robot_input.split(" ")
        func_split = func.split(" ")
        input_index = 0
        func_index = 0
        for func_part in func_split:
            if "${" in func_part:
                temp_args = ""
                term_word = ""
                if func_index+1 < len(func_split):
                    term_word = func_split[func_index+1]
                while input_index < len(input_split) and input_split[input_index] != term_word:
                    temp_args = "%s %s" % (temp_args, input_split[input_index])
                    input_index += 1
                if temp_args == "":
                    raise Exception("ERROR: No args found for argument '%s' in method '%s'" % (func_part, func))
                args.append(temp_args.strip())
            else:
                input_index += 1
            func_index += 1
        return args

    def _generic_make_browser(self, webdriver_type, desired_cap_type, remote_url, desired_caps):
        """
        Override Selenium2Library's _generic_make_browser to allow for extra params
        to driver constructor.
        """
        kwargs = {}
        if not remote_url:
            browser = webdriver_type(**kwargs)
        else:
            browser = self._create_remote_web_driver(desired_cap_type, remote_url, desired_caps)
        return browser

    def _make_browser(self, browser_name, desired_capabilities=None, profile_dir=None, remote=None):
        """
        Overrides make browser in Selenium2Library
        """
        creation_func = self._get_browser_creation_function(browser_name)

        if not creation_func:
            raise ValueError(browser_name + " is not a supported browser.")

        browser = creation_func(remote, desired_capabilities, profile_dir)
        browser.set_speed(self._speed_in_secs)
        browser.set_script_timeout(self._timeout_in_secs)
        browser.implicitly_wait(self._implicit_wait_in_secs)
        return browser

    @keyword(name='Open ${pagename}')
    def open(self, pagename):
        """
        Wrapper for Selenium2Library's open_browser() that calls resolve_url for url logic and self.browser.
        It also deletes cookies after opening the browser.

        :param pagename: the name of the page to open
        :type pagename: str
        :return: the Page object for that page
        :rtype: Page
        :raises Exception: IF url of page is not resolvable
        """
        self.log("OPENING BROWSER TO %s" % pagename, is_console=False)
        resolved_url = ""
        pages = Page()._get_child_pages(include_self=False)
        new_page = None
        for page in pages:
            if hasattr(page, "name"):
                page_name = page.name
                if page_name == pagename:
                    new_page = page()
                    resolved_url = new_page._resolve_url()
                    break
                else:
                    continue
        if resolved_url == "":
            raise Exception("RESOLVED URL NOT FOUND")

        self.open_browser(resolved_url, self.browser)
        self.maximize_browser_window()
        self.log("PO_BROWSER: %s" % (str(self.get_current_browser())), is_console=False)
        new_page.current_page_should_be()
        return new_page

    @keyword(name='Go To ${pagename}')
    def go_to_page(self, pagename):
        """
        Wrapper for Selenium2Library's open_browser() that calls resolve_url for url logic and self.browser.
        It also deletes cookies after opening the browser.

        :param pagename: the name of the page to open
        :type pagename: str
        :return: the Page object for that page
        :rtype: Page
        :raises Exception: IF url of page is not resolvable
        """
        self.log("GOING TO %s" % pagename, is_console=False)
        resolved_url = ""
        pages = Page()._get_child_pages(include_self=False)
        new_page = None
        for page in pages:
            if hasattr(page, "name"):
                page_name = page.name
                if page_name == pagename:
                    new_page = page()
                    resolved_url = new_page._resolve_url()
                    break
                else:
                    continue
        if resolved_url == "":
            raise Exception("RESOLVED URL NOT FOUND")
        try:
            self.go_to(resolved_url)
        except:
            raise Exception("ERROR: No Browser Found. Please use 'Open ${pagename} instead!")
        self.maximize_browser_window()
        self.log("PO_BROWSER: %s" % (str(self.get_current_browser())), is_console=False)
        new_page.current_page_should_be()
        return new_page
    
    def _resolve_url(self):

        """
        Figures out the URL that a page object should open at.

        Called by open().
        """
        pageobj_name = self.__class__.__name__

        # determine type of uri attribute
        if not hasattr(self, 'uri'):
            raise UriResolutionError("Page object \"%s\" must have a \"uri\" attribute set." % pageobj_name)

        # We always need a baseurl set. This enforces parameterization of the
        # domain under test.

        if self.baseurl is None:
            raise UriResolutionError("To open page object, \"%s\" you must set a baseurl." % pageobj_name)
            
        return self.baseurl + self.uri
    
    @property
    def driver(self):
        """
        Wrap the _current_browser() S2L method
        """
        try:
            return self._current_browser()
        except RuntimeError:
            return None

    def get_current_browser(self):
        """
        Legacy wrapper for self.driver
        """
        return self.driver

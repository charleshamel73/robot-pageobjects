from _metasingleton import MetaSingleton


class KeywordManager(object):
    __metaclass__ = MetaSingleton
    """
    This singleton class handles the mapping of robot functions
    To add mapping do
        KeywordManager().add_page_methods(self)
    To map from python to robot use:
        KeywordManager().get_meth_from_robot_alias(page,name)
    To get a list of all robot keywords for page:
        KeywordManager().get_robot_keywords(self)
    """
    def __init__(self):
        if not self._initialized:
            # PLACE CRITICAL CODE HERE IN ORDER TO AVOID INIT BEING CALLED TWICE
            self._initialized = True
            self._robot_maps_by_page = {}
            self._robot_maps_by_name = {}
            self._func_maps_by_page = {}

    def add_page_methods(self, page_inst):
        """
        This method adds the robot functions for that object and updates the current map of python funcs
        This method restricts the keywords based on the following criteria
        Requirement
           Can't start with "_"
           Can't be used in RF Hook
           Can't be a part of Logger Class
           S2L Keywords belong only to Page Class
           Can't be Static

        :param page_inst: The page instance with the methods to add
        :type page_inst: Page Object
        """
        pages = page_inst._get_parent_pages(top_to_bottom=True, include_top=True)
        robot_page_name = page_inst.name
        # THIS IS A SINGLETON SO ONCE ROBOT KEYWORDS EXIST FOR THAT PAGE IT DOES NOT NEED TO BE REPEATED ##
        if robot_page_name not in self._robot_maps_by_page:
            current_page_robot_map = {}
            current_page_func_map = {}
            for page in pages:
                # IGNORE ANY METHOD IN LOGGER ##
                if page.__name__ == 'Logger':
                    continue
                # ALL S2L METHODS SHOULD ONLY EXIST IN PAGE AND NOTHING ELSE ##
                elif page_inst.__class__.__name__ != 'Page' and self.in_s2l(page):
                    continue
                for method in page.__dict__.values():
                    # VALIDATING THAT METHOD IS A FUNCTION OBJECT ##
                    if hasattr(method, "func_name"):
                        func_name = method.func_name
                        # IGNORE ANY METHOD THAT IS PRIVATE TO ROBOT HOOK ##
                        if func_name.startswith("_") or func_name in ["get_keyword_names", "run_keyword","get_keyword_arguments","get_keyword_documentation"]:
                            continue
                        # FUNC NAME AND ALIAS DEFAULT TO NAME ##
                        func_alias = func_name
                        robot_name = func_name
                        # IF ROBOT ALIAS EXIST THEN OVERWRITE ${pagename} with page name ##
                        if hasattr(method, "robot_name"):
                            func_alias = method.robot_name
                            robot_name = func_alias.replace("${pagename}", robot_page_name)
                        # Adding Entries into Func Map under func alias ##
                        current_page_func_map[func_alias] = FuncMap(func_alias, func_name, page, method)
                        # Adding Entries into Robot Map under robot function name##
                        current_page_robot_map[robot_name] = RobotMap(robot_name, page_inst, func_alias)
                # Adding Entries into Func Map by page and updating list ##
                # Must be entered by page as function mapping changes per inheritance per page ##
            self._func_maps_by_page[robot_page_name] = current_page_func_map
            # Adding Entries into Robot Map for the current page and updating list of robot keywords ##
            self._robot_maps_by_page[robot_page_name] = current_page_robot_map
            self._robot_maps_by_name.update(current_page_robot_map)

    def get_robot_keywords_for_page(self, page):
        """
        Passes back the current list of robot keywords for the given page

        :param page: the page instance which you want methods of
        :type page: Page
        :return: a list of methods in string form
        :rtype: list of strings
        """
        return self._robot_maps_by_page[page.name].keys()

    def get_meth_mapping_from_robot_alias(self, page, robot_name):
        """
        Given a page instance and a robot_method name
        returns back a Func_Map which has the following attr
            func_alias: name
            def_name: defined func name
            func_page: class that holds the function

        :param page: the current page instance
        :type page: Page
        :param robot_name: the name of the page ex. page_inst.name
        :type robot_name: str
        :return: A Func Map for the given Robot Method
        :rtype: _Func_Map
        """
        try:
            robot_map = self._robot_maps_by_name[robot_name]
        except:
            raise Exception("Keyword, %s, not found in pages" % robot_name)
        func_map_for_page = self._func_maps_by_page[page.name]
        return func_map_for_page[robot_map.func_alias]

    def in_s2l(self, clazz):
        """
        This method checks if the given class object is part of selenium2library

        :param clazz: class object to check
        :type clazz: object
        :return: True if the object is a part of Selenium2Library
        :rtype: bool
        """
        if "Selenium2Library" in clazz.__module__:
            return True
        return False


class FuncMap(object):
    """
    This object holds the attribute of the function:
    func_alias: (primary key) the keyword_alias for the method(DEFAULTS TO FUNC_NAME IF @[keyword..] not there)
    def_name: the absolute name of the function
    func_page: the page that the func resides in
    func: the func object for that function
    """
    func_alias = None
    def_name = None
    func_page = None
    func = None

    def __init__(self, alias, name, page, meth):
        self.func_alias = alias
        self.def_name = name
        self.func_page = page
        self.func = meth


class RobotMap(object):
    """
    RobotMap defines the attribute of the robot keywords from ROBOT to python:
    robot_name: (primary key)the unique name of the robot function
    robot_page: the page that the unique name is attributed to
    func_alias: (foreign key)the alias of the function which maps to func_alias in FuncMap
    """
    robot_name = None
    robot_page = None
    func_alias = None
    
    def __init__(self, name, page, func_alias):
        self.robot_name = name
        self.robot_page = page
        self.func_alias = func_alias

from _metaflyweight import MetaFlyWeight
#import YamlVariables
import yaml
import os
import inspect


class YAMLHandler(object):
    """
    This class is a Flyweight for the options
    Example:
        YAMLHandler(LoginPage)
    To get all locators:
        YAMLHandler(LoginPage).get_locators()
    To get options use:
        YAMLHandler(LoginPage).get_locator("ice cream")
    """
    __metaclass__ = MetaFlyWeight
    _page_instance = None
    _locators = None

    def __init__(self, page_inst):
        if not self._initialized:
            self._page_instance = page_inst
            self._populate_yaml()
            self._initialized = True
        
    def _populate_yaml(self):
        """ 
        Populates the _locators value with all the yaml files of self to parents
        Lower Level Classes Take Priority
        """
        self._locators = {}
        list_of_classes = self._page_instance._get_parent_pages(top_to_bottom=True)
        for clazz in list_of_classes:
            yaml_path = self._convert_classpath_to_yaml(clazz)
            if os.path.isfile(yaml_path):
                with open(yaml_path, "r") as f:
                    values = yaml.load(f)
                if(values is None):
                    self.log("YAMLHANDLER WARNING: Empty yaml file found at location '%s'. Please delete file if not needed. "%yaml_path,"WARN")
                    values ={}
                self._locators.update(values)

    def get_locator(self, key):
        """ 
        Gets the Locator with the given key

        :param key: The key of the locator
        :type key: str
        :return: value of the locator at the location
        :returns: dict of locators or value
        :raise Exception: IF KEY IS NOT FOUND
        """
        name = self._normalize(key)
        path = name.split(".")
        try:
            locatorlist = self._locators
            for part in path:
                locatorlist = locatorlist[part]
            return locatorlist
        except:
            raise Exception("LOCATOR ERROR: no locator found with name %s" % name)
        
    def get_locators(self):
        """ 
        Gets the list of all locators

        :return: list of all locators
        :rtype: dict of locators
        """
        return self._locators
    
    def _normalize(self, name):
        """
        Normalizes key by:
            Replaces Locators spaces with _
            makes them lowercase

        :param name: the string you want normalized
        :type name: str
        :return: normalized version of the string
        :rtype: str
        """
        norm = name.replace(' ', '_')
        norm = norm.lower()
        return norm
    
    def _convert_classpath_to_yaml(self, clazz):
        """
        Converts the class filepath to a yaml path at the current place

        :param clazz: the class object to whom the file is being looked for
        :type clazz: object
        :return: the path of the .robot file associated with that class
        :rtype: str
        """
        path = ""
        try:
            clazzfile = inspect.getfile(clazz)
        except:
            clazzfile = ""
        if ".pyc" in clazzfile:
            path = clazzfile.replace(".pyc", ".yaml")
        else:
            path = clazzfile.replace(".py", ".yaml")
        return path

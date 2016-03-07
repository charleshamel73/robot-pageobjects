from robot.libraries.BuiltIn import BuiltIn
from robot.running.context import EXECUTION_CONTEXTS
from _metasingleton import MetaSingleton


class Context(object):
    __metaclass__ = MetaSingleton
    """
    Encapsulates the logic for whether we're in Robot or not.
    It's a singleton.
    """
    _instance = None
    _s2l_instance = None
    _new_called = 0
    _keywords_exposed = False
    _cache = None
    _current_page = None

    @staticmethod
    def in_robot():
        """
        This returns True if Robot framework is running

        :return: bool True if robot is running
        :rtype: bool
        """
        try:
            BuiltIn().get_variables()
            return True
        except:
            return False

    @staticmethod
    def set_current_page(name):
        """
        Sets Current Search Order to choose the given page as first

        :param name: The name of the page to set as current context
        :type name: str
        """
        BuiltIn().set_library_search_order(name)

    @classmethod
    def set_cache(cls, cache):
        """
        This sets the cache for S2L

        :param cache: the cache to save
        """
        cls._cache = cache
        
    @classmethod
    def get_cache(cls):
        """
        This method returns the cache
        :return: shared cache
        """
        return cls._cache

    @staticmethod
    def get_libraries():
        """
        This returns a list of libraries that are imported in Robot

        :return: a list of all libs installed
        :rtype: list of strings
        """
        """ Gets the list of libraries that are imported in robot"""
        return [lib.name for lib in EXECUTION_CONTEXTS.current.namespace.libraries]

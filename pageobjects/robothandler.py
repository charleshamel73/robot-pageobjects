from _metaflyweight import MetaFlyWeight
from context import Context
from robot.libraries.BuiltIn import BuiltIn
from abstractedlogger import Logger
import os
import inspect


class RobotHandler(object):
    """
    This class is a Flyweight for the robot file
    It imports the associated .robot file if it exist
    Example:
        RobotHandler(LoginPage)
    """
    __metaclass__ = MetaFlyWeight
    _page_instance = None
    
    def __init__(self, page_inst):
        if not self._initialized:
            self._page_instance = page_inst
            if Context.in_robot():
                self._load_robot_resources()
            else:
                Logger().log("Robot Framework is currently not available", "INFO")
            self._initialized = True
        
    def _load_robot_resources(self):
        """
        This method runs through the list of parent classes including self
        Imports the Resource directly into robot if a .robot file with the same class name exist
        WILL NOT RUN IF NOT IN ROBOT
        """

        self._locators = {}
        list_of_classes = self._page_instance._get_parent_pages(top_to_bottom=True)
        for clazz in list_of_classes:
            robot_path = self._convert_classpath_to_robot(clazz)
            if os.path.isfile(robot_path):
                test_path = robot_path.replace("\\", "\\\\")
                BuiltIn().import_resource(test_path)
                
    def _convert_classpath_to_robot(self, clazz):
        """
        Converts the class filepath to a robot path at the current place

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
            path = clazzfile.replace(".pyc", ".robot")
        else:
            path = clazzfile.replace(".py", ".robot")
        return path

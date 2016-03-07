from _metaflyweight import MetaFlyWeight
from context import Context
from exceptions import VarFileImportErrorError
from robot.libraries.BuiltIn import BuiltIn
import os
import re
import imp


class OptionHandler(object):
    """
    This class is a Flyweight for the options
    Example:
        OptionHandler(LoginPage)
    To get options use:
        OptionHandler(LoginPage).get("ice cream",None)
    """
#    from automationpages import Page 
    __metaclass__ = MetaFlyWeight
    _page_instance = None
    _opts = {}
    
    def __init__(self, page_inst):
        if not self._initialized:
            self._opts = {}
            self._page_instance = page_inst
            self._populate_opts()
        
    def _populate_opts(self):
        """
        Pulls environment from PO_ environment file
        """
        self._opts.update(self._get_opts_from_var_file())
        self._opts.update(self._get_opts_from_env_vars())
        if Context.in_robot():
            self._opts.update(self._get_opts_from_robot())
        self._update_opts_from_inherited_classes()

    def _get_opts_from_robot(self):
        """
        Pulls environment from PO_ environment file
        """
        ret = {}
        robot_vars = BuiltIn().get_variables()
        for var, val in robot_vars.iteritems():
            ret[self._normalize(var)] = val
        return ret

    def _get_opts_from_var_file(self):
        """
        Pulls environment from PO_ environment file
        """
        ret = {}
        var_file_path = os.environ.get("PO_VAR_FILE", None)
        if var_file_path:
            abs_var_file_path = os.path.abspath(var_file_path)
            try:
                vars_mod = imp.load_source("vars", abs_var_file_path)

            except (ImportError, IOError), e:
                raise VarFileImportErrorError(
                    "Couldn't import variable file: %s. Ensure it exists and is importable." % var_file_path)

            var_file_attrs = vars_mod.__dict__
            for vars_mod_attr_name in var_file_attrs:
                if not vars_mod_attr_name.startswith("_"):
                    vars_file_var_value = var_file_attrs[vars_mod_attr_name]
                    ret[self._normalize(vars_mod_attr_name)] = vars_file_var_value
        return ret

    def _get_opts_from_env_vars(self):
        """
        Pulls environment from PO_ environment vars in the local machine
        """
        ret = {}
        for env_varname in os.environ:
            if env_varname.startswith("PO_") and env_varname.isupper():
                varname = env_varname[3:]
                ret[self._normalize(varname)] = os.environ.get(env_varname)
        return ret
    
    def _update_opts_from_inherited_classes(self):
        """
        Using the given Page object class, we create a cumulative options value based on its parent pages
        """
        list_of_classes = self._page_instance._get_parent_pages(top_to_bottom=True)
        self.temp_options = {}
        for clazz in list_of_classes:
            if hasattr(clazz, "options"):
                self.temp_options.update(clazz.options)
        self._opts.update(self.temp_options)

    def _normalize(self, opts):
        """
        Convert an option keyname to lower-cased robot format, or convert
        all the keys in a dictionary to robot format.
        """
        if isinstance(opts, str) or isinstance(opts,unicode):
            name = opts.lower()
            rmatch = re.search("\$\{(.+)\}", name)
            return rmatch.group(1) if rmatch else name
        else:
            # We're dealing with a dict
            return {self._normalize(key): val for (key, val) in opts.iteritems()}

    def get(self, name, default=None):
        """
        Gets an option value given an option name

        :param name: The name of the option to get
        :type name: str
        :param default: the value to return if none is found
        :type default: any
        :return: the value of the attribute or default if not found
        """
        ret = default
        try:
            if Context.in_robot():
                ret = self._opts[self._normalize(name)]
            else:
                ret = self._opts[self._normalize(name.replace(" ", "_"))]
        except KeyError:
            pass
        return ret

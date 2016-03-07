""" Add __metaclass__ = MetaFlyWeight to Class to work"""


class MetaFlyWeight(type):
    def __init__(cls, *args, **kargs):
        """
        This enables the decorated class to create a single instance and cache it
        Stores each cached instance by module name
        cls = MetaFlyWeight
        """
        type.__init__(cls, *args, **kargs)
        cls.__instances = {}
        # Overwriting the new method of the MetaFlyWeight
        cls.__new__ = cls._get_instance
        
    def _get_instance(cls, *args, **kargs):
        """
        This function overwrites the __new__ function of the cls
        The non-meta class __init__ will be called twice if a check is not added
        def __init__(self,page_inst):
            if(self._initialized == False):
                ....<Critial Initialization Steps>...
                self._initialized = True

        :return:  the instance of the cached object by key
        """
        """

        Args:
            *args: any argument for constructing class
            **kargs: map of arguments for class

        Returns:
            instance: the instance of the cached object by argument


        """
        key = (cls, args[1].__class__.__module__)
        instances = cls._MetaFlyWeight__instances
        if key in instances:
            return instances.get(key)
        else:
            new_instance = super(cls, cls).__new__(*args, **kargs)
            new_instance._initialized = False
            cls._MetaFlyWeight__instances[key] = new_instance
            return new_instance

""" Add __metaclass__ = MetaSingleton to Class to work"""


class MetaSingleton(type):
    def __init__(cls, *args, **kargs):
        """
        This enables the decorated class to create a single instance
        cls = MetaFlyWeight
        """
        type.__init__(cls, *args, **kargs)
        cls.__instance = None
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
        # This key is based on Class this is built on
        if cls.__instance is None:
            instance = super(cls, cls).__new__(*args, **kargs)
            instance._initialized = False
            cls.__instance = instance
        return cls.__instance

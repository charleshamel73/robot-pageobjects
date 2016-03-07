class MissingLocatorError(Exception):
    """
    Raised when there is a problem with locators.
    """


class UriResolutionError(Exception):
    """
    Raised when there is a problem with resolving a uri using a page.
    """


class VarFileImportErrorError(Exception):
    """
    Raised when a variable file can't be imported
    """
    pass


class MissingBrowserOptionError(Exception):
    """
    Raised when there's a missing browser option 
    """
    pass


class MissingBaseURLOptionError(Exception):
    """
    Raised when there's a missing baseurl option 
    """
    pass


class PageLoadError(Exception):
    """
    Raised when a page fails to load
    """
    pass

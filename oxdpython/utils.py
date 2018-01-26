import json

class Resource(object):
    """A utility class to represent resources in `ResourceSet`

    Args:
        path (str, unicode): the path of the resource
    """
    def __init__(self, path):
        self.path = path
        self.conditions = []
        self.scope_expression = {}

    def dump(self):
        """Returns a dictionary representation of the resource and conditions

        Returns:
            a dict representation of the resource
        """
        return dict(path=self.path, conditions=self.conditions)

    def set_scope(self, http_method, scope):
        """Set a scope condition for the resource for a http_method

        Args:
            http_method (str): HTTP method like GET, POST, PUT, DELETE
            scope (str, list): the scope of access control as str if single, or
                as a list of strings if multiple scopes are to be set
        """

        for con in self.conditions:
            if http_method in con['httpMethods']:
                if isinstance(scope, list):
                    con['scopes'] = scope
                elif isinstance(scope, str) or isinstance(scope, unicode):
                    con['scopes'].append(scope)
                return
        # If not present, then create a new condition
        if isinstance(scope, list):
            self.conditions.append({'httpMethods': [http_method],
                                    'scopes': scope})
        elif isinstance(scope, str) or isinstance(scope, unicode):
            self.conditions.append({'httpMethods': [http_method],
                                    'scopes': [scope]})

    def set_expression(self, http_method, expression):
        """Set a scope expression scope_expression is Gluu invented extension
        which allows to put JsonLogic expression instead of single list of
        scopes. Please read more about scope_expression at
        https://gluu.org/docs/ce/3.1.2/admin-guide/uma.md

        Args:
            http_method (str): a HTTP method like GET, POST, PUT, DELETE
            expression (dict): the scope expression in the format::

                {
                  "rule": {
                    "and": [
                      {
                        "or": [{"var": 0}, {"var": 1}]
                      },
                      {
                        "var": 2
                      }
                    ]
                  },
                  "data": [
                    "http://photoz.example.com/dev/actions/all",
                    "http://photoz.example.com/dev/actions/add",
                    "http://photoz.example.com/dev/actions/internalClient"
                  ]
                }

        """
        self.conditions.append({'httpMethods': [http_method],
                                'scope_expression': expression})

    def __str__(self):
        return json.dumps(self.dump())

    def __repr__(self):
        return "<Resource %s>" % self.path


class ResourceSet(object):
    """A utility class for mapping resources and conditions for UMA resource
    protection
    """
    def __init__(self):
        self.resources = {}

    def add(self, path):
        """Adds a new resource with the given path to the resource set.

        Args:
            path (str, unicode): path of the resource to be protected

        Raises:
            TypeError when the path is not a string or a unicode string
        """
        if not isinstance(path, str) and not isinstance(path, unicode):
            raise TypeError('The value passed for parameter path is not a str'
                            ' or unicode')

        resource = Resource(path)
        self.resources[path] = resource
        return resource

    def dump(self):
        """Dumps the resource set into the Python object suitable for the oxd
        server's JSON expectation.

        Returns:
            A list of dicts defined in the resource set in the format::

                [{
                    "path": "path1",
                    "conditions": [
                        {
                            "httpMethod": ["method1", "method2"],
                            "scopes": ["scope1", "scope2"]
                        },
                        {
                            "httpMethod": ["method3", "method4"],
                            "scopes": ["scope3", "scope4"]
                        }
                    ]
                },{
                    "path": "path2",
                    "conditions": []
                }]
        """
        return [v.dump() for k,v in self.resources.iteritems()]

    def remove(self, path):
        """Removes the given resource from the resource set.
        """
        self.resources.pop(path, None)

    def __len__(self):
        return len(self.resources)

    def __str__(self):
        return json.dumps(self.dump())

    def __repr__(self):
        r = ",".join(self.resources.keys())
        return "<ResourceSet [%s]>" % r


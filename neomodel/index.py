from lucenequerybuilder import Q
from .exception import PropertyNotIndexed
from .properties import AliasProperty
from py2neo import neo4j


class NodeIndexManager(object):
    def __init__(self, node_class, index_name):
        self.node_class = node_class
        self.name = index_name

    def _check_params(self, params):
        """checked args are indexed and convert aliases"""
        for key in params.keys():
            prop = self.node_class.get_property(key)
            if not prop.is_indexed:
                raise PropertyNotIndexed(key)
            if isinstance(prop, AliasProperty):
                real_key = prop.aliased_to()
                if real_key in params:
                    msg = "Can't alias {0} to {1} in {2}, key {0} exists."
                    raise Exception(msg.format(key, real_key, repr(params)))
                params[real_key] = params[key]
                del params[key]

    def _execute(self, query):
        return self.__index__.query(query)

    def search(self, query=None, **kwargs):
        """ Load multiple nodes via index """
        if not query:
            self._check_params(kwargs)
            query = reduce(lambda x, y: x & y, [Q(k, v) for k, v in kwargs.iteritems()])

        return [self.node_class.inflate(n) for n in self._execute(str(query))]

    def get(self, query=None, **kwargs):
        """ Load single node via index """
        nodes = self.search(query=query, **kwargs)
        if len(nodes) == 1:
            return nodes[0]
        elif len(nodes) > 1:
            raise Exception("Multiple nodes returned from query, expected one")
        else:
            raise self.node_class.DoesNotExist("Can't find node in index matching query")

    @property
    def __index__(self):
        from .core import connection
        return connection().get_or_create_index(neo4j.Node, self.name)
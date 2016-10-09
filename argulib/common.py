
class ArgumentationException(Exception):
    pass

class IllegalArgument(ArgumentationException):
    pass

class IllegalMove(ArgumentationException):
    pass

class NotYourMove(ArgumentationException):
    pass

class DiscussionFinished(ArgumentationException):
    pass

class MethodNotApplicable(ArgumentationException):
    pass

class NoMoreMoves(ArgumentationException):
    pass

class Confused(ArgumentationException):
    pass

class Disagree(ArgumentationException):
    pass

def enum(*sequential, **named):
    """ This functions declares a new type 'enum' that acts as an enum. """
    enums = dict(zip(sequential, range(len(sequential))), **named)
    reverse = dict((value, key) for key, value in enums.items())
    enums['reverse_mapping'] = reverse
    return type('Enum', (), enums)


Move = enum('QUESTION', 'CLAIM', 'WHY', 'BECAUSE', 'CONCEDE',
                'DISAGREE', 'RETRACT')

PlayerType = enum('OPPONENT', 'PROPONENT')


def role_str(p):
    return PlayerType.reverse_mapping[p]


def move_str(m):
    return Move.reverse_mapping[m]

# helpers
def oi_to_args(issues):
    """ Return a set containing all arguments in the list of open issues."""
    res = set()
    for i in issues:
        res &= set(i.arguments)
    return res


# ########################### Graph Data Structure ############################# #


class Graph:
    """ This class represents a graph (in the mathematical sense).
    A graph is a set of nodes and edges connecting the nodes. The nodes
    in the graph can be of any type, as long as they can be used keys in a dict.

    For more info about the graph structure see
    http://www.python.org/doc/essays/graphs.html
    
    Unlike normal graphs, this graph has a root node and an end node to support
    workflows better, as they usually have Start and End.

    """

    def __init__(self, items=None):
        self._items = dict()
        if items is not None:
            for k, v in items.items():
                self._items[k] = set(v)
        self.root = None
        self.top  = None

    def add_node(self, node, replace=False):
        """ Add a new node into the graph.
        If replace is True, replace the node if it exists (ie. delete 
        corresponding edges). Return true if added else return False.
        
        """
        if node not in self._items or replace:
            self._items[node] = set()
            return True
        return False

    def del_node(self, node):
        """ Remove the node from the graph, if it exists. """
        if node in self._items: del self._items[node]

    def add_edge(self, source, dest, create=True):
        """ Add a new edge to the graph.
        If create is true, create nodes if they are not in the graph.
        Return true if edge was added else return False.
        
        """
        if source not in self._items or dest not in self._items:
            if not create:
                return False
            else:
                self.add_node(source)
                self.add_node(dest)
        self._items[source].add(dest)
        return True

    def del_edge(self, source, dest):
        """ Remove the edge between source and dest, if it exists. """
        if source in self._items:
            self._items[source].remove(dest)

    def __str__(self):
        """ Return the summary of the graph. """
        num_edges = 0
        for n, t in self._items.items():
            num_edges += len(t)
        result = ('TaskGraph: #nodes: %d\t#edges %d' %
                    (len(self._items), num_edges))
        return result

    def __repr__(self):
        """ Return the string representation of the graph. """
        result = self.__str__() + '\n'
        for n, t in self._items.items():
            result += ('\t%s: %s\n' % (str(n), str(t)))
        return result

    @property
    def nodes(self):
        """ Returns nodes in the graph in arbitrary order. """
        return list(self._items.keys())

    @property
    def edges(self):
        """ Returns a list of pairs that represents the edges. """
        result = list()
        for n, t in self._items.items():
            for destination in t:
                result.append((n, destination))
        return result

    def __contains__(self, item):
        """ Return true if a node (item) is in the graph. """
        return item in self._items

    def __getitem__(self, k):
        """ Return the list of nodes connected to the node k or raise exception
        if the node is not in the graph.

        """
        return self._items[k]

    def items(self):
        return [x for x in self._items.items()]

    def depth_first_nodes(self, start, visited=None):
        """ Return nodes from start using depth first algorithm. Note that 
        if there is no edge to a particular node, it will not be visited.
        
        """
        yield start
        if visited is None: visited = set()
        visited.add(start)
        for t in self[start]:
            if t in visited:
                continue
            yield from self.depth_first_nodes(t, visited)

    def depth_first_nodes_with_level(self, start, visited=None, lvl=0):
        """ Return nodes from start using depth first algorithm. Note that 
        if there is no edge to a particular node, it will not be visited.
        
        """
        yield (start, lvl)
        if visited is None: visited = set()
        visited.add(start)
        for t in self[start]:
            if t in visited:
                continue
            yield from self.depth_first_nodes_with_level(t, visited, lvl+1)

    def breadth_first_nodes(self, start):
        """ Return nodes from start using breadth first algorithm. Note that
        if there is no edge to a particular node, it will not be visited.
        
        """
        visited = set()
        queue = [start]
        while len(queue) > 0:
            t = queue.pop()  # take the last element
            if t not in visited:
                visited.add(t)
                yield t
                if len(self[t]) > 0:
                    queue = list(self[t]) + queue  # prepend the new nodes

    def breadth_first_nodes_with_level(self, start):
        """ Return nodes from start using breadth first algorithm. Note that
        if there is no edge to a particular node, it will not be visited.
        
        """
        visited = set()
        lvl = 0
        queue = [ (start, lvl) ]
        while len(queue) > 0:
            t, current = queue.pop()  # take the last element
            if t not in visited:
                visited.add(t)
                yield (t, current)
                if len(self[t]) > 0:
                    queue = [(x, current+1) for x in self[t]] + queue  # prepend the new nodes

    def find_path(self, start, end, path=[]):
        """ Find path between start and end. If there is no such path, return 
        None. If start is end return [start].
        
        """
        path = path + [start]
        if start == end:
            return path
        if start not in self:
            return None
        for node in self[start]:
            if node not in path:
                newpath = self.find_path(node, end, path)
                if newpath:
                    return newpath
        return None

    def find_all_paths(self, start, end, path=[]):
        """ Find all paths between start and end in a list.
            If there are no paths, return an empty list.
        
        """
        path = path + [start]
        if start == end:
            return [path]
        if start not in self:
            return []
        paths = []
        for node in self[start]:
            if node not in path:
                newpaths = self.find_all_paths(node, end, path)
                for newpath in newpaths:
                    paths.append(newpath)
        return paths

    def find_shortest_path(self, start, end, path=[]):
        """ Find the shortest path between start and end.
            If there is no such path, return None.
            If start is end return [start].

        """
        path = path + [start]
        if start == end:
            return path
        if not start in self:
            return None
        shortest = None
        for node in self[start]:
            if node not in path:
                newpath = self.find_shortest_path(node, end, path)
                if newpath:
                    if not shortest or len(newpath) < len(shortest):
                        shortest = newpath
        return shortest


################################################################################


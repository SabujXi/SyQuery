class Query:
    def __init__(self):
        self.__filter_root_node = None
        self.__actions = None

    @property
    def is_empty(self):
        return self.__filter_root_node is None and self.__actions is None

    @property
    def filter_root(self):
        return self.__filter_root_node

    @property
    def actions(self):
        return self.__actions

    def set_filter(self, filter_root):
        assert self.__filter_root_node is None
        self.__filter_root_node = filter_root

    def set_actions(self, action):
        assert self.__actions is None
        self.__actions = action

    def __str__(self):
        if self.is_empty:
            return "Query<>"
        return f"Query< {self.filter_root} \n | {self.actions} >"

    def __repr__(self):
        return self.__str__()

    def __bool__(self):
        return not self.is_empty


class FilterNode:
    def __init__(self, key, op, data):
        self.__op = op
        self.__key = key
        self.__data = data

    @property
    def key(self):
        return self.__key

    @property
    def data(self):
        return self.__data

    @property
    def op(self):
        return self.__op

    def __str__(self):
        return f"""{self.__class__.__name__} [{str(self.key)} {str(self.op)} {str(self.data)}]"""

    def __repr__(self):
        return self.__str__()


class ActionNode:
    def __init__(self, action_key, action_params):
        self.__action_key = action_key
        self.__action_params = action_params

    @property
    def action_key(self):
        return self.__action_key

    @property
    def action_params(self):
        return self.__action_params

    def __str__(self):
        return f"{self.action_key} {self.action_params}"

    def __repr__(self):
        return self.__str__()


class JoinerNode:
    def __init__(self):
        self.__left = None
        self.__right = None
        self.__joiner = 'NONE'
        self.__leaf = None

    @property
    def is_valid(self):
        return (self.__left is None and self.__right is None) and self.__leaf is not None or \
               (self.__left is not None or self.__right is not None) and self.__leaf is None

    @property
    def is_leaf(self):
        return self.__leaf is not None

    @property
    def leaf(self) -> FilterNode:
        return self.__leaf

    def set_leaf(self, node: FilterNode):
        assert self.__left is None and self.__right is None
        self.__leaf = node

    @property
    def left(self) -> 'JoinerNode':
        return self.__left

    def set_left(self, node: 'JoinerNode'):
        assert not self.is_leaf, "Leaf node cannot have left or right"
        assert self.__left is None, "Cannot reset node"
        self.__left = node

    @property
    def right(self) -> 'JoinerNode':
        return self.__right

    def set_right(self, joiner, node: 'JoinerNode'):
        assert not self.is_leaf, "Leaf node cannot have left or right"
        assert self.__left is not None, "Left must be set before right can be..."
        assert self.__right is None, "Cannot reset right."
        assert isinstance(node, JoinerNode), f"Found {node} of type {type(node)}"
        assert joiner in ('and', 'or')
        self.__joiner = joiner
        self.__right = node

    @property
    def joiner(self):
        return self.__joiner

    @property
    def has_right(self):
        return self.__right is not None

    @property
    def has_left(self):
        return self.__left is not None

    def walk(self, evaluator_call, joiner_call):
        """
        evaluator is a callable that work on a single FilterNode
        evaluator: (filter_node) -> value

        joiner will take left value the joiner key and the right value and will return a new value.
        joiner: (left_value, joiner, right_value) -> value
        :return: a value calculated by the evaluator.
        """
        assert self.is_valid, "Cannot walk on invalid tree"

        if self.is_leaf:
            leaf = self.leaf
            value = evaluator_call(leaf)
        else:
            value = left_value = self.left.walk(evaluator_call, joiner_call)
            if self.has_right:
                right_value = self.right.walk(evaluator_call, joiner_call)
                value = joiner_call(left_value, self.joiner, right_value)
        return value

    def str_tree(self) -> str:

        def evaluator_call(filter_node):
            return str(filter_node)

        def joiner_call(left_value, joiner, right_value):
            return f"{{ {left_value} {joiner} {right_value} }}"

        return self.walk(evaluator_call, joiner_call)

    def __str__(self):
        return self.str_tree()

    def __repr__(self):
        return self.__str__()

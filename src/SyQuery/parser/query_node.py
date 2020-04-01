import abc
import enum


class AbcNode(metaclass=abc.ABCMeta):
    def __init__(self):
        self.__next = None

    def add_next(self, node: 'AbcNode'):
        assert self.__next is None, "Cannot add more than once"
        assert isinstance(node, self.__class__), f"Programmer error: node must of type {self.__class__.__name__}"
        self.__next = node

    def has_next(self) -> bool:
        return self.__next is not None

    @property
    def next(self) -> 'AbcNode':
        return self.__next

    def has_leaf(self):
        return self.has_next()

    def get_leaf(self):
        leaf = None
        if self.__next is not None:
            next = self.__next
            while next.has_next():
                next = next.next
        return leaf

    def __repr__(self):
        return self.__str__()


class JoinedWith(enum.Enum):
    AND = 'AND'
    OR = 'OR'
    NONE = 'NONE'


class FilterQueryNode(AbcNode):
    def __init__(self, op, left, right, joined_with: JoinedWith = JoinedWith.NONE):
        super().__init__()
        self.__op = op
        self.__left = left
        self.__right = right
        self.__joined_with = joined_with

    @property
    def left(self):
        return self.__left

    @property
    def right(self):
        return self.__right

    @property
    def op(self):
        return self.__op

    @property
    def joined_with(self):
        return self.__joined_with

    def __str__(self):
        return f"""
        {self.__class__.__name__}( {str(self.left)} {str(self.op)} {str(self.right)} )
        """


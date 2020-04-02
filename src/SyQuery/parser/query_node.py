import enum
import abc


class JoinedWith(enum.Enum):
    AND = 'AND'
    OR = 'OR'
    NONE = 'NONE'

    @classmethod
    def from_text(self, text):
        if text == 'and':
            return self.AND
        elif text == 'or':
            return self.OR
        else:
            return self.NONE


class AbcNode(metaclass=abc.ABCMeta):
    def __init__(self):
        self.__next = None
        self.__joined_with = JoinedWith.NONE

    def set_join(self, joined_with: JoinedWith):
        assert self.__joined_with is JoinedWith.NONE
        self.__joined_with = joined_with

    def add_next(self, node: 'AbcNode', joined_with: JoinedWith):
        assert self.__next is None, "Cannot add more than once"
        assert isinstance(node, self.__class__), f"Programmer error: node must of type {self.__class__.__name__}"
        node.set_join(joined_with)
        self.__next = node

    def has_next(self) -> bool:
        return self.__next is not None

    @property
    def next(self) -> 'AbcNode':
        return self.__next

    @property
    def joined_with(self):
        return self.__joined_with

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


class FilterQueryNode(AbcNode):
    def __init__(self, key, op, data, joined_with: JoinedWith = JoinedWith.NONE):
        super().__init__()
        self.__op = op
        self.__key = key
        self.__data = data
        self.__joined_with = joined_with

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
        return f"""{self.joined_with.value} {self.__class__.__name__} [{str(self.key)} {str(self.op)} {str(self.data)} {str(self.next) if self.has_next() else '-'}]"""

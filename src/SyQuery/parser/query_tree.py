from .query_node import FilterNode, JoinedWith
import typing


class QueryTree:
    def __init__(self):
        self.__root_node = None

    def append(self, node: FilterNode):
        if self.__root_node is None:
            self.__root_node = node
        # get the last node
        else:
            assert node.joined_with is not JoinedWith.NONE
            if self.__root_node.has_leaf():
                leaf = self.__root_node.get_leaf()
            else:
                leaf = self.__root_node
            leaf.add_next(node)

    def get_root(self) -> FilterNode:
        return self.__root_node

    def get_nodes(self):
        nodes: typing.List[FilterNode] = []
        if self.__root_node is not None:
            node: FilterNode = self.__root_node
            nodes.append(node)
            while node.has_next():
                node = node.next
                nodes.append(node)
        return nodes

    def is_empty(self):
        return self.__root_node is None

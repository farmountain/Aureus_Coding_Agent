class TreeNode:
    """Represents a node in the binary search tree."""
    
    def __init__(self, value: int):
        self.value: int = value
        self.left: 'TreeNode' = None
        self.right: 'TreeNode' = None


class BinarySearchTree:
    """Binary Search Tree implementation with insert, search, delete, and in-order traversal methods."""

    def __init__(self):
        self.root: 'TreeNode' = None

    def insert(self, value: int) -> None:
        """Insert a value into the binary search tree."""
        if self.root is None:
            self.root = TreeNode(value)
        else:
            self._insert_recursive(self.root, value)

    def _insert_recursive(self, node: TreeNode, value: int) -> None:
        """Helper method to insert a value recursively into the tree."""
        if value < node.value:
            if node.left is None:
                node.left = TreeNode(value)
            else:
                self._insert_recursive(node.left, value)
        elif value > node.value:
            if node.right is None:
                node.right = TreeNode(value)
            else:
                self._insert_recursive(node.right, value)

    def search(self, value: int) -> bool:
        """Search for a value in the binary search tree."""
        return self._search_recursive(self.root, value)

    def _search_recursive(self, node: TreeNode, value: int) -> bool:
        """Helper method to search for a value recursively."""
        if node is None:
            return False
        if value == node.value:
            return True
        elif value < node.value:
            return self._search_recursive(node.left, value)
        else:
            return self._search_recursive(node.right, value)

    def delete(self, value: int) -> None:
        """Delete a value from the binary search tree."""
        self.root = self._delete_recursive(self.root, value)

    def _delete_recursive(self, node: TreeNode, value: int) -> TreeNode:
        """Helper method to delete a value recursively."""
        if node is None:
            return None
        if value < node.value:
            node.left = self._delete_recursive(node.left, value)
        elif value > node.value:
            node.right = self._delete_recursive(node.right, value)
        else:
            # Node with only one child or no child
            if node.left is None:
                return node.right
            elif node.right is None:
                return node.left
            # Node with two children: Get the inorder successor (smallest
            # in the right subtree)
            min_larger_node = self._min_value_node(node.right)
            node.value = min_larger_node.value
            node.right = self._delete_recursive(node.right, min_larger_node.value)
        return node

    def _min_value_node(self, node: TreeNode) -> TreeNode:
        """Helper method to find the node with the minimum value in a subtree."""
        current = node
        while current.left is not None:
            current = current.left
        return current

    def in_order_traversal(self) -> list:
        """Return the in-order traversal of the tree as a list."""
        result: list = []
        self._in_order_recursive(self.root, result)
        return result

    def _in_order_recursive(self, node: TreeNode, result: list) -> None:
        """Helper method for in-order traversal."""
        if node is not None:
            self._in_order_recursive(node.left, result)
            result.append(node.value)
            self._in_order_recursive(node.right, result)
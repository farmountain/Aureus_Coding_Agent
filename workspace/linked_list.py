class Node:
    """Represents a node in the linked list."""
    
    def __init__(self, value: int):
        self.value: int = value
        self.next: 'Node' = None


class LinkedList:
    """Singly linked list implementation with insert, delete, and search methods."""
    
    def __init__(self):
        self.head: Node = None

    def insert(self, value: int) -> None:
        """Insert a new node with the specified value at the end of the linked list."""
        new_node = Node(value)
        if not self.head:
            self.head = new_node
            return
        last_node = self.head
        while last_node.next:
            last_node = last_node.next
        last_node.next = new_node

    def delete(self, value: int) -> bool:
        """Delete the first occurrence of the node with the specified value from the linked list.

        Returns True if the node was deleted, False if not found.
        """
        current_node = self.head
        previous_node = None
        
        while current_node and current_node.value != value:
            previous_node = current_node
            current_node = current_node.next
        
        if not current_node:  # Value not found
            return False
        
        if previous_node is None:  # The node to delete is the head
            self.head = current_node.next
        else:
            previous_node.next = current_node.next
        
        return True

    def search(self, value: int) -> bool:
        """Search for a node with the specified value in the linked list.

        Returns True if found, False otherwise.
        """
        current_node = self.head
        while current_node:
            if current_node.value == value:
                return True
            current_node = current_node.next
        return False

    def __str__(self) -> str:
        """Return a string representation of the linked list."""
        values = []
        current_node = self.head
        while current_node:
            values.append(str(current_node.value))
            current_node = current_node.next
        return " -> ".join(values)
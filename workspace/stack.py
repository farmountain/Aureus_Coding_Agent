class Stack:
    """
    A simple stack implementation using a list.

    Attributes:
        items (list): A list to hold the stack items.
    """

    def __init__(self) -> None:
        """Initialize an empty stack."""
        self.items = []

    def push(self, item: any) -> None:
        """Push an item onto the stack.

        Args:
            item (any): The item to be pushed onto the stack.
        """
        self.items.append(item)

    def pop(self) -> any:
        """Pop an item off the stack.

        Returns:
            any: The popped item.

        Raises:
            IndexError: If the stack is empty.
        """
        if self.is_empty():
            raise IndexError("pop from empty stack")
        return self.items.pop()

    def peek(self) -> any:
        """Return the top item of the stack without removing it.

        Returns:
            any: The top item of the stack.

        Raises:
            IndexError: If the stack is empty.
        """
        if self.is_empty():
            raise IndexError("peek from empty stack")
        return self.items[-1]

    def is_empty(self) -> bool:
        """Check if the stack is empty.

        Returns:
            bool: True if the stack is empty, False otherwise.
        """
        return len(self.items) == 0

    def size(self) -> int:
        """Return the number of items in the stack.

        Returns:
            int: The size of the stack.
        """
        return len(self.items)
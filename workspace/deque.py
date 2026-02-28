from collections import deque
from typing import Any

class Deque:
    """
    A class that represents a double-ended queue (deque).
    
    Methods
    -------
    add_front(item: Any) -> None
        Adds an item to the front of the deque.
    
    add_rear(item: Any) -> None
        Adds an item to the rear of the deque.
    
    remove_front() -> Any
        Removes and returns the item from the front of the deque.
    
    remove_rear() -> Any
        Removes and returns the item from the rear of the deque.
    
    is_empty() -> bool
        Checks if the deque is empty.
    
    size() -> int
        Returns the number of items in the deque.
    """

    def __init__(self) -> None:
        """Initializes an empty deque."""
        self._deque = deque()

    def add_front(self, item: Any) -> None:
        """Adds an item to the front of the deque."""
        self._deque.appendleft(item)

    def add_rear(self, item: Any) -> None:
        """Adds an item to the rear of the deque."""
        self._deque.append(item)

    def remove_front(self) -> Any:
        """Removes and returns the item from the front of the deque."""
        if self.is_empty():
            raise IndexError("remove_front from an empty deque")
        return self._deque.popleft()

    def remove_rear(self) -> Any:
        """Removes and returns the item from the rear of the deque."""
        if self.is_empty():
            raise IndexError("remove_rear from an empty deque")
        return self._deque.pop()

    def is_empty(self) -> bool:
        """Checks if the deque is empty."""
        return len(self._deque) == 0

    def size(self) -> int:
        """Returns the number of items in the deque."""
        return len(self._deque)
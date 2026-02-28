from typing import Any, Optional

class Queue:
    """
    A class that represents a simple queue data structure.

    Methods
    -------
    enqueue(item: Any) -> None
        Adds an item to the end of the queue.
    
    dequeue() -> Optional[Any]
        Removes and returns the item from the front of the queue.
    
    is_empty() -> bool
        Checks if the queue is empty.
    """
    
    def __init__(self) -> None:
        """Initializes an empty queue."""
        self.items: list[Any] = []

    def enqueue(self, item: Any) -> None:
        """Adds an item to the end of the queue."""
        self.items.append(item)

    def dequeue(self) -> Optional[Any]:
        """
        Removes and returns the item from the front of the queue.
        
        Returns
        -------
        Optional[Any]
            The item removed from the front of the queue, or None if the queue is empty.
        """
        if self.is_empty():
            return None
        return self.items.pop(0)

    def is_empty(self) -> bool:
        """Checks if the queue is empty."""
        return len(self.items) == 0
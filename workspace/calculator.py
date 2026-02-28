class Calculator:
    """
    A simple calculator class that provides methods for basic arithmetic operations.

    Methods
    -------
    add(a: float, b: float) -> float
        Returns the sum of two numbers.
    
    subtract(a: float, b: float) -> float
        Returns the difference between two numbers.
    """

    def add(self, a: float, b: float) -> float:
        """
        Adds two numbers together.

        Parameters
        ----------
        a : float
            The first number.
        b : float
            The second number.

        Returns
        -------
        float
            The sum of a and b.
        """
        return a + b

    def subtract(self, a: float, b: float) -> float:
        """
        Subtracts the second number from the first.

        Parameters
        ----------
        a : float
            The number from which to subtract.
        b : float
            The number to subtract.

        Returns
        -------
        float
            The difference of a and b.
        """
        return a - b
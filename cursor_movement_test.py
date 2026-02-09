class MathOperations:
    def check_prime(self, n):
        """Check if a number is prime"""
        if n < 2:
            return False
        for i in range(2, int(n ** 0.5) + 1):
            if n % i == 0:
                return False
        return True
    
    def find_factorial(self, n):
        """Find factorial of a number"""
        if n < 0:
            return "Factorial not defined for negative numbers"
        if n == 0 or n == 1:
            return 1
        result = 1
        for i in range(2, n + 1):
            result *= i
        return result
"""
Instructions:

Your task is to create a program that implements the Sieve of Eratosthenes
algorithm to find all prime numbers less than or equal to a given number

A prime number is a number larger than 1 that is only divisible by 1 and itself.

Example:
2, 3, 5, 7, 11 and 13 are prime numbers
6 is not a prime number as it not only divisible by 1 and itself, but also 2 nad 3

To use the Sieve of Eratosthenes:
First, write out all the numbers from 2 up to and including your number. Then follow these steps:
1. Find the next unmarked number (skipping over marked numbers). This is a prime number
2. Mark all the multiples of that prime number as not prime

Repeat the steps until you've gone through every number. At the end, all the unmarked numbers are prime

Example:
Let's say you're finding the primes less than or equal to 10
- Write out 2, 3, 4, 5, 6, 7, 8, 9, 10, leaving them all unmarked
    2 3 4 5 6 7 8 9 10
- 2 is unmarked and is therefore a prime. Mark 4, 6, 8, and 10 as "not prime"
- 3 is unmarked and mark 6 and 9 as not prime
- 4 is marked as "not prime", so we skip over it
- 5 is unmarked and is therefore a prime. Mark 10 as not prime
... 


"""

def primes(limit):
    numbers = set(range(2, limit + 1))
    for i in range(2, limit + 1):
        if i in numbers:
            numbers.difference_update(range(i * 2, limit + 1, i))

    return sorted(numbers)
            

print(primes(10))
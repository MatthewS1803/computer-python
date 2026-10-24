"""
Instructions

Your task is to write the code that calculates the energy points that get awarded to players when they complete a level.

The point awarded depend on two things:
- The level (a number) that the player completed
- The base value of each magical item collected by the player during that level

The energy points are awarded according to the following rules:
1. For each magical item, take the base value and find all the multiples of that value taht are less than the level number
2. Combine the set of numbers
3. Remove any duplicates
4. Calculate the sum of all the numbers that are left


"""

def sum_of_multiples(limit, multiples):
    unique_multiples = set()
    for number in multiples:
        if number < limit and number != 0:
            for multiple in range(number, limit, number):
                unique_multiples.add(multiple)

    return sum(unique_multiples)

print(sum_of_multiples(1, [3, 5]))
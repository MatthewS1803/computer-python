def triplets_with_sum(number):
    triplets = []
    for a in range(1, number):
        b = (number**2 - 2 * number * a) // (2 * number - 2 * a)
        c = number - (a + b)
        if a**2 + b**2 == c**2 and a < b < c:
            triplets.append([a, b, c])

    return triplets

print(triplets_with_sum(12))
print(2 * 3 * 4)
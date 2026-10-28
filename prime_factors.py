def factors(value):
    result = []
    divisor = 2
    while value > 1:
        if value % divisor == 0:
            result.append(divisor)
            value /= divisor
        else:
            divisor += 1

    return result
                
print(factors(9))
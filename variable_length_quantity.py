def encode_number(number):
    if number == 0:
        return [0]
    digits = []
    while number > 0:
        digits.append(number  % 128)
        number //= 128
    digits.reverse()

    result = []
    for digit in digits[:-1]:
        result.append(digit + 128)
    result.append(digits[-1])

    return result


def encode(numbers):
    result = []
    for number in numbers:
        result.extend(encode_number(number))
    return result

def decode(bytes_):
    value = 0
    result = []
    in_number = False
    for byte in bytes_:
        value = value * 128 + (byte & 0x7F)
        if byte < 128:
            result.append(value)
            value = 0
            in_number = False
        else:
            in_number = True

    if in_number:
        raise ValueError('incomplete sequence')
    return result

print(encode([0]))
print(decode([0x81, 0x00]))
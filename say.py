place_value = ('', 'thousand', 'million', 'billion')
zero_to_nineteen = (
    'zero', 'one', 'two', 'three',
    'four', 'five', 'six', 'seven',
    'eight', 'nine', 'ten', 'eleven',
    'twelve', 'thirteen', 'fourteen', 'fifteen',
    'sixteen', 'seventeen', 'eighteen', 'nineteen'

)

tens = ('', '', 'twenty', 'thirty', 'forty', 
        'fifty', 'sixty', 'seventy', 'eighty', 'ninety')

def say_under_100(n):
    if n < 20:
        return zero_to_nineteen[n]
    elif n % 10 == 0:
        quotient = n // 10
        return tens[quotient]
    else:
        quotient = n // 10
        remainder = n % 10
        return tens[quotient] + '-' + zero_to_nineteen[remainder]

def say_under_1000(n):
    if n < 100:
        return say_under_100(n)
    elif n % 100 == 0:
        quotient = n // 100
        return zero_to_nineteen[quotient] + ' hundred'
    else:
        quotient = n // 100
        return f"{zero_to_nineteen[quotient]} hundred {say_under_100(n % 100)}"
    

def say(number):
    if number < 0 or number > 999_999_999_999:
        raise ValueError('input out of range')

    if number == 0:
        return zero_to_nineteen[0]
    
    result = []
    counter = 0
    while number > 0:
        group = number % 1000
        if group != 0:
            phrase = say_under_1000(group)
            if counter > 0:
                phrase += ' ' + place_value[counter]
            result.append(phrase)
        number //= 1000
        counter += 1
    return ' '.join(reversed(result))


print(say(1_234_567))

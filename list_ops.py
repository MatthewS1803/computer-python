from functools import reduce

# Add all items in the second list to the end of the first list
def append(list1, list2):
    list1.extend(list2)
    return list1

# Combine all items in all lists into one flattened list
def concat(lists):
    result = []
    for item in lists:
        if isinstance(item, list):
            for n in item:
                result.append(n)
        else:
            result.append(item)

    return result

# Given a predicate and a list, return the list of all items for which predicate(item) is True
def filter(function, list):
    result = []
    for item in list:
        if function(item):
            result.append(item)

    return result

# Given a list, return the total number of items within it
def length(list):
    length = len(list)
    return length

# Given a function and a list, return the list of the results of applying function(item) on all items
def map(function, list):
    result = []
    for item in list:
        new_item = function(item)
        result.append(new_item)

    return result

# Given a function, a list, and initial accumulator, fold (reduce) 
# each item into the accumulator from the left
def foldl(function, list, initial):
    result = reduce(function, list, initial)
    return int(result)



# Given a function, a list, and an initial accumulator, fold (reduce)
# each item into the accumulator from the right
def foldr(function, list, initial):
    reversed_list = list[::-1]

    result = reduce(function, reversed_list, initial)
    return result

# Given a list, return a list with all the original items, but in reversed order

def reverse(list):
    return list[::-1]






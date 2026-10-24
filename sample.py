word = 'happiness'


if word[-4:] == 'ness':
    word = word[:-4]

if word[-1] == 'i':
    word = word[:-1] + 'y'

print(word)

"""
Instruction:
Count how many times each word occurs in a subtitle of a drama
The subtitles from these dramas use only ASCII characters

Words can be separated by any form of punctuation (e.g. ':', '!' or '?') or whitespace (e.g. '\t', '\n' or '')
The only punctuation that does not separate words is the apostrophe in contractions

Numbers are considered words. If the subtitle says 'It costs 100 dollars' then 100 will be its own word

Words are case insensitive. 
For example:
You come back, you hear me? DO YOU HEAR ME?
The word 'you' occurs three times

The ordering of the word counts in the results doesn't matter

"""
import re

def count_words(sentence):
    word_count = {}
    cleaned_sentence = re.sub(r"[^a-z0-9\s']", " ", sentence.lower())
    words = cleaned_sentence.split()

    
    for word in words:
        word = word.strip("'")
        if word not in word_count:
            if word == '':
                continue
            else:
                word_count[word] = 1
        else:
            word_count[word] += 1

    return word_count

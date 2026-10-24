import re, nltk

pos_map = {
    "noun" : ["NN", "NNS", "NNP", "NNPS"],
    "verb" : ["VB", "VBD", "VBG", "VBN", "VBP", "VBZ"],
    "adjective" : ["JJ", "JJR", "JJS"],
}

with open("file.txt") as file:
    template = file.read()

print("===== Mad Libs Generator =====")
print(template)


placeholder = re.findall(r"\[[A-Z]+\]", template)

for word in placeholder:
    clean_word = word.strip("[]").lower()
    if re.match(r"^[aeiou]", clean_word):
        article = "an"
    else:
        article = "a"

    user_input = input(f"Please enter {article} {clean_word}: ")

    while True:
        user_input = re.sub(r"\s+", " ", user_input)
        if re.search(r"\d", user_input):
            print("Please enter a valid word (no numbers).")
            user_input = input(f"Please enter {article} {clean_word}: ").strip()
            continue

        # Check if the user input matches the expected part of speech
        tagged_input = nltk.pos_tag([user_input])
        tag = tagged_input[0][1]

        if tag not in pos_map[clean_word]:
            print(f"Please enter a valid {clean_word}.")
            user_input = input(f"Please enter {article} {clean_word}: ").strip()
            continue

        break

    template = re.sub(re.escape(word), user_input, template, count=1).strip()

print("\n===== Your Mad Libs Story =====")
print(template)
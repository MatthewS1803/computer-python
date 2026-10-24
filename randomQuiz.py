"""
Random Quiz Files:
- Creates 35 different quizzes
- Creates 50 multiple-choice questions for each quiz, in random order
- Provides the correct answer and three random wrong answers for each question, in random order
- Writes the quizzes to 35 text files
- Writes teh answer keys to 35 text files
"""

import random

# The quiz data. Keys are states and values are their capital
capitals = {'Alabama': 'Montgomery', 'Alaska': 'Juneau', 'Arizona':
'Phoenix', 'Arkansas': 'Little Rock', 'California': 'Sacramento', 'Colorado':
'Denver', 'Connecticut': 'Hartford', 'Delaware': 'Dover', 'Florida':
'Tallahassee', 'Georgia': 'Atlanta', 'Hawaii': 'Honolulu', 'Idaho': 'Boise',
'Illinois': 'Springfield', 'Indiana': 'Indianapolis', 'Iowa': 'Des Moines',
'Kansas': 'Topeka', 'Kentucky': 'Frankfort', 'Louisiana': 'Baton Rouge',
'Maine': 'Augusta', 'Maryland': 'Annapolis', 'Massachusetts': 'Boston',
'Michigan': 'Lansing', 'Minnesota': 'Saint Paul', 'Mississippi': 'Jackson',
'Missouri': 'Jefferson City', 'Montana': 'Helena', 'Nebraska': 'Lincoln',
'Nevada': 'Carson City', 'New Hampshire': 'Concord', 'New Jersey': 'Trenton',
'New Mexico': 'Santa Fe', 'New York': 'Albany', 'North Carolina': 'Raleigh',
'North Dakota': 'Bismarck', 'Ohio': 'Columbus', 'Oklahoma': 'Oklahoma City',
'Oregon': 'Salem', 'Pennsylvania': 'Harrisburg', 'Rhode Island': 'Providence',
'South Carolina': 'Columbia', 'South Dakota': 'Pierre', 'Tennessee':
'Nashville', 'Texas': 'Austin', 'Utah': 'Salt Lake City', 'Vermont':
'Montpelier', 'Virginia': 'Richmond', 'Washington': 'Olympia', 'West Virginia':'Charleston', 
'Wisconsin': 'Madison', 'Wyoming': 'Cheyenne'}

# Generate 35 quiz files
for quiz_num in range(35):
    # TODO: Create the quiz and answer key files
    quiz_file = open(f'capitalsquiz{quiz_num + 1}.txt', 'w', encoding="UTF-8")
    answer_file = open(f'capitalsquiz_answers{quiz_num + 1}.txt', 'w', encoding="UTF-8" )

    # TODO: Write out the header for the quiz
    quiz_file.write('Name:\n\nData:\n\nPeriod:\n\n')
    quiz_file.write((' ' * 20) + f'State Capitals Quiz (Form{quiz_num + 1})')
    quiz_file.write('\n\n')

    # TODO: Shuffle the order of the states
    states = list(capitals.keys())
    random.shuffle(states)

    # TODO: Loop through all 50 states, making a question for each
    for num in range(50):

        # Get right and wrong answers
        correct_answer = capitals[states[num]]
        wrong_answers = list(capitals.values())
        del wrong_answers[wrong_answers.index(correct_answer)]
        wrong_answers = random.sample(wrong_answers, 3)
        answers_options = wrong_answers + [correct_answer]
        random.shuffle(answers_options)

        # TODO: Write the equation and answer options to the quiz file
        quiz_file.write(f'{num + 1}. Capital of {states[num]}:\n')
        for i in range(4):
            quiz_file.write(f"    {'ABCD'[i]}. {answers_options[i]}\n") 
        quiz_file.write('\n')

        # TODO: Write the answer key
        answer_file.write(f"{num + 1}.{'ABCD'[answers_options.index(correct_answer)]}")
    quiz_file.close()
    answer_file.close()
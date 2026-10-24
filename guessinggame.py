import random

while True:
    random_choice = random.randint(1,100)
    count = 0
    print("Welcome to the Number Guessing Game!")
    while True:
        user_input = input("Please enter a number bewteen 1 and 100: ")
        try:
            valid_number = int(user_input)

            if valid_number < 1 or valid_number > 100:
                print("Input is out of range.")
            elif valid_number > random_choice:
                print("Your guess is too high! Try again")
                count += 1
            elif valid_number < random_choice:
                print("Your guess is too low! Try again")
                count += 1
            else:
                count += 1
                print("You got it right!"
                      f" It took you {count} attempts!")
                break
        except ValueError:
            print("That is not a vaild number. Try again")

    while True:
        play_again = input("Do you want to play again? (yes/no): ").lower()
        if play_again == "yes" or play_again == "no":
            break
        print("Please try again")

    if play_again == "no":
        break
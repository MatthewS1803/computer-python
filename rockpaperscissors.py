import random

def second_choice(game_mode, difficulty=None, player_choice=None):
    if game_mode == "double":
        while True:
            player_two_choice = input("Please choose rock, paper, or scissors: ").lower()
            # Checks if user input is correct or not 
            if player_two_choice not in ("rock", "paper", "scissors"):
                print("Invalid input. Please try again: ")
            else:
                display_move(player_two_choice)
                return player_two_choice
    else:
        roll = random.randint(1, 100)

        # Gamemode: Easy 75% chance to win, 15% chance to lose, 10% chance to tie
        if difficulty == "easy":
            if roll <= 75:
                computer_move = beats[player_choice]
            elif roll > 75 and roll <= 90:
                computer_move = loses_to[player_choice]
            else:
                computer_move = player_choice

        # Gamemode: Medium 50% chance to win, 20% chance to lose, 30% chance to tie
        elif difficulty == "medium":
            if roll <= 50:
                computer_move = beats[player_choice]
            elif roll > 50 and roll <= 70:
                computer_move = loses_to[player_choice]
            else:
                computer_move = player_choice

        # Gamemode: Hard 15% chance to win, 60% chance to lose, 25% to tie    
        elif difficulty == "hard":
            if roll <= 15:
                computer_move = beats[player_choice]
            elif roll > 15 and roll <= 75:
                computer_move = loses_to[player_choice]
            else:
                computer_move = player_choice

        # Gamemode: Impossible 80% chance to lose,  20% chance to tie
        else:
            if roll <= 80:
                computer_move = loses_to[player_choice]
            else:
                computer_move = player_choice

        display_move(computer_move)
        return computer_move


def winning_move(player_choice, opponent_move):
    if player_choice == opponent_move:
        print("It's a tie!")
        return "tie"
    elif beats[player_choice] == opponent_move:
        print("You win this round!")
        return "player"
    else:
        print("Computer wins this round!")
        return "opponent"


def display_move(move):
    move_art = {
        'rock' : """
    _______
---'   ____)
      (_____)
      (_____)
      (____)
---.__(___)
""",
        'scissors' : """
    _______
---'   ____)____
          ______)
       __________)
      (____)
---.__(___)

""",
        'paper' : """
     _______
---'    ____)____
           ______)
          _______)
         _______)
---.__________)
"""
    }

    print(move_art[move])



beats = {
    'rock' : 'scissors',   # Rock beats scissors
    'paper' : 'rock',      # Paper beats rock
    'scissors' : 'paper'   # Scissors beats paper
}

loses_to = {
    'rock' : 'paper',      # Rock loses to paper
    'paper' : 'scissors',  # Paper loses to scissors
    'scissors' : 'rock'    # Scissors loses to rock 
}

print("Welcome to Rock Paper Scissors!")


# Checks if user picked correct gamemode
while True:
    while True:
        game_mode = input("Please select single player or two player (single/double): ").lower()
        if game_mode not in ("single", "double"):
            print("Invalid game mode. Please try again: ")
        else:
            break

    difficulty = None
    if game_mode == "single":
        while True:
            difficulty = input("Please select difficulty (easy, medium, hard, impossible): ")
            if difficulty not in ('easy', 'medium', 'hard', 'impossible'):
                print("Invalid difficulty setting. Please try again: ")
            else:
                break

    # Best of 3 Match
    player_wins = 0
    opponent_wins = 0
    
    for round_num in range(3):
        print(f"\n---Round {round_num + 1} ---")    
        while True:
            player_choice = input("Please choose rock, paper, or scissors: ").lower()
            # Checks if user input is correct or not 
            if player_choice not in ('rock', 'paper', 'scissors'):
                print("Invalid input. Please try again: ")
            else:
                display_move(player_choice)
                break

        if game_mode == "double":
            opponent_move = second_choice(game_mode)
        else:
            opponent_move = second_choice(game_mode, difficulty, player_choice)

        result = winning_move(player_choice, opponent_move)

        if result == "player":
            player_wins += 1
        elif result == "opponent":
            opponent_wins += 1

        print(f"Score\nYou: {player_wins}, Opponent: {opponent_wins}")

        if player_wins == 2 or opponent_wins == 2:
            break

    if player_wins > opponent_wins:
        print("\nYou won the match!")
    elif opponent_wins > player_wins:
        print("\nOpponent won the match!")
    else:
        print("\nThe match is tied!")


    # Ask: same difficulty / change/ quit
    while True:
        next_action = input(
            "\nPlay again with the same setting, change settings, or quit? (same/change/quit):"
        ).lower()
        if next_action in ("same", "change", "quit"):
            break
        print("Please try again")

    if next_action == "quit":
        break
    

    
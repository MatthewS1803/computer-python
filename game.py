def display_board(board):
    for i in range(len(board)): 
        row = f"{board[i][0]} | {board[i][1]} | {board[i][2]}"
        print(row)
        if i != len(board) - 1:
            print("-" * len(row))

def get_move(board):
    while True:
        row = int(input("Please enter your row (1, 2, 3): ")) - 1
        col = int(input("Please enter your column (1, 2, 3): ")) - 1
        if row not in (0, 1, 2) or col not in (0, 1, 2):
            print("Please enter a number between 1 and 3.")
            continue
        if board[row][col] == "---":
            return row, col
        else:
            print("This spot is already taken. Please choose another one.")

def check_winner(board):
    winning_combination = [
        [(0, 0), (0, 1), (0, 2)],
        [(1, 0), (1, 1), (1, 2)],
        [(2, 0), (2, 1), (2, 2)],
        [(0, 0), (1, 0), (2, 0)],
        [(0, 1), (1, 1), (2, 1)],
        [(0, 2), (1, 2), (2, 2)],
        [(0, 2), (1, 1), (2,0)],
        [(0, 0), (1, 1), (2, 2)]
    ]

    for winning_combo in winning_combination:
        a, b, c = winning_combo[0], winning_combo[1], winning_combo[2]
        row1, col1 = a
        row2, col2 = b
        row3, col3 = c

        values = {board[row1][col1], board[row2][col2], board[row3][col3]}

        if len(values) == 1 and "---" not in values:
            return board[row1][col1]

    return False

def is_board_full(board):
    for row in board:
        if "---" in row:
            return False
    return True

def play_cli_game():
    while True:
        board = [
        ["---", "---", "---"],
        ["---", "---", "---"],
        ["---", "---", "---"],
        ]

        current_player = "X"
        player_labels = {"X": "Player 1", "O": "Player 2"}

        for i in range(9):
            print(f"It's {player_labels[current_player]}'s turn")
            display_board(board)

            player_row, player_col = get_move(board)
            board[player_row][player_col] = current_player

            winner = check_winner(board)
            tie = is_board_full(board)

            if not winner == False:
                display_board(board)
                print(f"{player_labels[current_player]} is the winner!") 
                break
            if tie:
                display_board(board)
                print("It's a tie!")
                break

            if current_player == "X":
                current_player = "O"
            else:
                current_player = "X"

        while True:
            play_again = input("Do you want to play again? (yes/no): ").lower()
            if play_again == "yes" or play_again == "no":
                break
            print("Please try again")

        if play_again == "no":
            break

if __name__ == "__main__":
    play_cli_game()
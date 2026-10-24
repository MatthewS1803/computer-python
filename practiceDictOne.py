def isValidChessBoard(board):
    counts = {}
    white_total = 0
    black_total = 0
    for square, piece in board.items():
        if len(square) != 2:
            return False
        elif square[0] not in 'abcdefgh' or square[1] not in '12345678':
            return False
        if len(piece) != 2:
            return False
        elif piece[0] not in 'wb' or piece[1] not in 'RNBQKP':
            return False
        counts.setdefault(piece, 0)
        counts[piece] += 1
        if piece[0] == 'w':
            white_total += 1
        else:
            black_total += 1

    if white_total > 16 or black_total > 16:
        return False
    if counts.get('wK', 0) != 1 or counts.get('bK', 0) != 1:
        return False
    elif counts.get('wP', 0) > 8 or counts.get('bP', 0) > 8:
        return False
    

    return True



STARTING_PIECES = {'a8': 'bR', 'b8': 'bN', 'c8': 'bB', 'd8': 'bQ',
'e8': 'bK', 'f8': 'bB', 'g8': 'bN', 'h8': 'bR', 'a7': 'bP', 'b7': 'bP',
'c7': 'bP', 'd7': 'bP', 'e7': 'bP', 'f7': 'bP', 'g7': 'bP', 'h7': 'bP',
'a1': 'wR', 'b1': 'wN', 'c1': 'wB', 'd1': 'wQ', 'e1': 'wK', 'f1': 'wB',
'g1': 'wN', 'h1': 'wR', 'a2': 'wP', 'b2': 'wP', 'c2': 'wP', 'd2': 'wP',
'e2': 'wP', 'f2': 'wP', 'g2': 'wP', 'h2': 'wP'}

print(isValidChessBoard(STARTING_PIECES))
print(isValidChessBoard({'a1': 'wK', 'z9': 'bK'}))
print(isValidChessBoard({'a1': 'wK', 'b1' : 'wX'}))
print(isValidChessBoard({'a1': 'wQ', 'e8': 'bK'}))
print(isValidChessBoard({'a8': 'bR', 'b8': 'bN', 'c8': 'bB', 'd8': 'bQ',
'e8': 'bK', 'f8': 'bB', 'g8': 'bN', 'h8': 'bR', 'a7': 'bP', 'b7': 'bP',
'c7': 'bP', 'd7': 'bP', 'e7': 'bP', 'f7': 'bP', 'g7': 'bP', 'h7': 'bP',
'a1': 'wR', 'b1': 'wN', 'c1': 'wB', 'd1': 'wQ', 'e1': 'wK', 'f1': 'wB',
'g1': 'wN', 'h1': 'wR', 'a2': 'wP', 'b2': 'wP', 'c2': 'wP', 'd2': 'wP',
'e2': 'wP', 'f2': 'wP', 'g2': 'wP', 'h2': 'wP', 'e1' : 'wP'}))
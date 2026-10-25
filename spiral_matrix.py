"""
Instruction:

Your task is to return a square matrix of a given size

The matrix should be filled with natural numbers, starting from 1 in the top-left corner,
increasing in an inward, clockwise spiral order, like these examples:

Examples:
Spiral matrix of size 3
1 2 3
8 9 4
7 6 5

Spiral matrix of size 4
1 2 3 4
12 13 14 5
11 16 15 6
10 9 8 7
"""

directions = (
    (0, 1),  # right
    (1, 0),   # down 
    (0, -1), # left
    (-1, 0) # up
)

def spiral_matrix(size):
    grid = []
    for _ in range(size):
        grid.append([0] * size)   
    
    row, col = 0, 0
    direction = 0
    
    for number in range(1, size * size + 1):
        grid[row][col] = number
        row_change, col_change = directions[direction]
        next_row = row + row_change
        next_col = col + col_change
        if not (0 <= next_row < size) or not (0 <= next_col < size) or grid[next_row][next_col] != 0:
            direction = (direction + 1) % 4
            row_change, col_change = directions[direction]
            next_row = row + row_change
            next_col = col + col_change
        row, col = next_row, next_col

    return grid
        
print(spiral_matrix(3))
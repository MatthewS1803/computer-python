class Alien:
    total_aliens_created = 0

    def __init__(self, x_coordinate, y_coordinate):
        self.x_coordinate = x_coordinate
        self.y_coordinate = y_coordinate
        self.health = 3
        Alien.total_aliens_created += 1

    def hit(self):
        if not(self.health <= 0):
            self.health -= 1

    def is_alive(self):
        if self.health <= 0:
            return False
        return True

def new_aliens_collection(positions):
    alien_positions = []
    for position in positions:
        alien_positions.append(Alien(position[0], position[1]))
    return alien_positions

result = new_aliens_collection([(4, 7), (-1, 0)])
print(result[0].x_coordinate, result[0].y_coordinate)   # 4 7
print(result[1].x_coordinate, result[1].y_coordinate)   # -1 0



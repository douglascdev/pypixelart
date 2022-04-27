class Point:
    def __init__(self, x: int = 0, y: int = 0):
        self.x = x
        self.y = y

    @property
    def coordinates(self):
        return self.x, self.y

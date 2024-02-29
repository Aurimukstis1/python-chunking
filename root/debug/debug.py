def water_movement(self, pos):
    x, y = pos
    center_height = self.height(x, y)
    center_ground = self.ground[x][y]
    center_water = self.water[x][y]

    # A list of XYZ that water will flow to
    adjacent_cells = self.adjacent_less_than((x, y), center_height)

    # End this function call if there are no viable adjacent cells
    if len(adjacent_cells) == 0:
        return [None]

    shuffle(adjacent_cells)

    adjacent = adjacent_cells[0]

    # Difference in height between the center cell and the adjacent
    delta = center_height - adjacent[2]

    xfer_coefficient = 0.8
    cohesion_constant = 0.01

    if center_ground > adjacent[2]:
        max_water_xfer = center_water
        if delta > max_water_xfer:  # Scenario 3

            if max_water_xfer < cohesion_constant:
                xfer = max_water_xfer
                self.water[x][y] = 0
                self.water[adjacent[0]][adjacent[1]] += xfer
                # TODO remove x,y from water_cells
            else:
                xfer = max_water_xfer*xfer_coefficient
                self.water[x][y] -= xfer
                self.water[adjacent[0]][adjacent[1]] += xfer

            return [pos, (adjacent[0], adjacent[1])]

    # Otherwise, water should be balanced between the 2 cells
    average_height = (center_height+adjacent[2])/2

    # This is the amount of water that will be necessary to give the two cells the same height
    water_xfer_to_balance = average_height - adjacent[2]

    # Water transfer for situations 1 & 2
    self.water[x][y] -= water_xfer_to_balance
    self.water[adjacent[0]][adjacent[1]] += water_xfer_to_balance

    # TODO add adjacent to water_cells

    # Return XY's of effected cells
    return [pos, (adjacent[0], adjacent[1])]


def adjacent_less_than(self, center, height):
    x, y = center
    adjacent_cells = []
    for i in range(-1, 2):
        for j in range(-1, 2):
            if i == 0 and j == 0:  # Skip the center cell
                continue
            if x + i < 0 or x + i >= self.size[0]: # Skip cells outside the board
                continue
            if y + j < 0 or y + j >= self.size[1]: # Skip cells outside the baord
                continue
            if self.ground[x + i][y + j] < height:
                adjacent_cells.append((x + i, y + j, self.ground[x + i][y + j]))
    return adjacent_cells
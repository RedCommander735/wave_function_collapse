import random
import sys
import json
import time
import pygame

# COMPLETE REWORK
#
# TODO 
# - Render image after each iteration
#
#

class Tile:
    def __init__(self, coords: tuple[int, int], possible_states: list, grid_size: int):

        self.tile_state: str = ""
        self.file: pygame.Surface = None
        self.coords: tuple[int, int] = coords
        self.collapsed: bool = False
        self.valid_neighbours: dict = []
        self.possible_states: list = possible_states
        self.grid_size: int = grid_size
        self.north: tuple[int, int] = (max(self.coords[0] - 1, 0), self.coords[1])
        self.east: tuple[int, int]  = (self.coords[0], min(self.coords[1] + 1, grid_size - 1))
        self.south: tuple[int, int] = (min(self.coords[0] + 1, grid_size - 1), self.coords[1])
        self.west: tuple[int, int]  = (self.coords[0], max(self.coords[1] - 1, 0))
        self.tile_north: Tile = None
        self.tile_east: Tile = None
        self.tile_south: Tile = None
        self.tile_west: Tile = None
        self.tiles: list = []

    def neighbouring_tiles(self, _grid):
        self.tile_north = _grid[self.north[1]][self.north[0]]
        self.tile_east = _grid[self.east[1]][self.east[0]]
        self.tile_south = _grid[self.south[1]][self.south[0]]
        self.tile_west = _grid[self.west[1]][self.west[0]]
        self.tiles = [self.tile_north, self.tile_east, self.tile_south, self.tile_west]

    def get_states_count(self) -> int:
        return len(self.possible_states)
        

    def update(self, _grid):
        if not self.collapsed:
            return

        directions: list[str] = ["north", "east", "south", "west"]

        # Update the state list of all surrounding tiles
        for tile, direction in zip(self.tiles, directions):
            if not tile.collapsed:
                #tile.possible_states = list(set(self.valid_neighbours[direction]).intersection(tile.possible_states))
                tile.possible_states = list(set(self.valid_neighbours[direction]) & set(tile.possible_states))

def main():
    file = "default"
    #simple = False
    # if len(sys.argv) > 2:
    #     file = sys.argv[1]
    #     if sys.argv[2] == "-simple":
    #         simple = True
    # elif len(sys.argv) > 1:
    #     file = sys.argv[1]
    if len(sys.argv) > 1:
        file: str = sys.argv[1]

    # Get all data and seed from file
    with open(f'json/{file}.json', 'r+', encoding="Utf-8") as openedfile:
        data: dict = json.load(openedfile)
        seed: str = data["meta"]["seed"]

        # If there is no seed specified use current time as seed; NEEDS REWORK
        if len(seed) == 0:
            seed = str(time.time())
            data["meta"]["seed"]: str = seed
            openedfile.truncate()
            json.dump(data, openedfile, indent = 4)

    random.seed(seed)

    # Raise exception if not every specified type has its own image file specified
    if len(data["types"]) != len(data["image_files"]):
        raise Exception("Types and file names don't have equal count")

    # Load the actual image files into storage instead of reference names
    for index, _file in enumerate(data["image_files"]):
        data["image_files"][index]: pygame.Surface = pygame.image.load(f"src/{_file}")

    # Grid size
    size: int = data["meta"]["size"]

    states: list[str] = data["types"]

    generate_image(size, data, states)


def generate_image(size: int, data: dict, possible_states: list[str]):
    # Define and generate initial grid
    grid: list = []
    for y_pos in range(size):
        row = []
        for x_pos in range(size):
            _tile = Tile((x_pos, y_pos), possible_states, size)
            row.append(_tile)
        grid.append(row)

    # Update all tiles so the have their neighbouring tiles cached
    for y_pos in range(size):
        for x_pos in range(size):
            grid[y_pos][x_pos].neighbouring_tiles(grid)

    # Define a random starting position for the algorithm
    x_pos = random.randint(0, size - 1)
    y_pos = random.randint(0, size - 1)

    # Initialize first tile
    tile_state: str = random.choice(possible_states)

    initial_tile: Tile = grid[y_pos][x_pos]

    initial_tile.collapsed: bool = True
    initial_tile.tile_state: str = tile_state
    initial_tile.valid_neighbours: dict = data["options"][tile_state]
    initial_tile.possible_states: list[str] = [tile_state]
    initial_tile.file: pygame.Surface = data["image_files"][data["types"].index(tile_state)]

    tile_size: int = data["meta"]["tile_size"]

    
    

    # Main loop

    pygame.init()
    
    # Generate clean canvas to later add tiles
    gameDisplay = pygame.display.set_mode((size*tile_size, size*tile_size))
    finished = False

    running = True

    total_start = time.perf_counter()
    while running:

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

        gameDisplay.fill((0,0,0))

        for y_pos in range(size):
            for x_pos in range(size):
                if grid[y_pos][x_pos].collapsed:
                    gameDisplay.blit(grid[y_pos][x_pos].file, (x_pos*tile_size, y_pos*tile_size))

        pygame.display.update()

        if not finished:
            # Iterate over the whole grid, update all tiles and check if finished
            min_states = len(possible_states)
            min_tiles = []

            start = time.perf_counter()

            finished = True
            for y_pos in range(size):
                for x_pos in range(size):
                    grid[y_pos][x_pos].update(grid)
                    if not grid[y_pos][x_pos].collapsed:
                        finished = False

            for y_pos in range(size):
                for x_pos in range(size):
                    __tile: Tile = grid[y_pos][x_pos]
                    states: int = __tile.get_states_count()
                    if states < min_states and states != 1:
                        min_states = states
                        min_tiles = []
                        min_tiles.append(__tile)
                    elif states == min_states:
                        min_tiles.append(__tile)

            lowest_entropy_tile: Tile = random.choice(min_tiles)

            _tile_state: str = random.choice(lowest_entropy_tile.possible_states)

            lowest_entropy_tile.collapsed: bool = True
            lowest_entropy_tile.tile_state: str = _tile_state
            lowest_entropy_tile.valid_neighbours: dict = data["options"][_tile_state]
            lowest_entropy_tile.possible_states: list[str] = [_tile_state]
            lowest_entropy_tile.file: pygame.Surface = data["image_files"][data["types"].index(_tile_state)]

            duration = time.perf_counter() - total_start

        # Display time of iteration
        dur = f'{duration:.2f}s'
        if duration > 60:
            duration = duration / 60
            dur = f'{int(duration)}min {((duration - int(duration)) * 60):.2f}s  '
        time_string = f'{(time.perf_counter() - start):.2f}'
        print(f'Iterationsdauer: {time_string}s, Dauer: {dur} ', end="\r")

if __name__ == '__main__':
    main()

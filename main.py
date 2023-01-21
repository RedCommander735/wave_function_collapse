import random
import sys
import json
import time
from PIL import Image

# COMPLETE REWORK
#
# TODO 
# - load the list of all possible states into every tile on creation
# - Implement check for lowest entropy to collapse
#

class Tile:
    def __init__(self, coords: tuple, possible_states: list,valid_neighbours: dict, grid_size: int, ttype: str = "", collapsed = False):

        self.ttype = ttype
        self.file = None
        self.coords = coords
        self.collapsed = collapsed
        self.valid_neighbours: dict = valid_neighbours
        self.possible_states: list = possible_states
        self.grid_size: int = grid_size
        self.north = (max(self.coords[0] - 1, 0),               self.coords[1])
        self.east  = (self.coords[0],                           min(self.coords[1] + 1, grid_size - 1))
        self.south = (min(self.coords[0] + 1, grid_size - 1),   self.coords[1])
        self.west  = (self.coords[0],                           max(self.coords[1] - 1, 0))
        self.tile_north = None
        self.tile_east = None
        self.tile_south = None
        self.tile_west = None
        self.tiles = []

    def neighbouring_tiles(self, _grid):
        self.tile_north = _grid[self.north[1]][self.north[0]]
        self.tile_east = _grid[self.east[1]][self.east[0]]
        self.tile_south = _grid[self.south[1]][self.south[0]]
        self.tile_west = _grid[self.west[1]][self.west[0]]
        self.tiles = [self.tile_north, self.tile_east, self.tile_south, self.tile_west]
        

    def update(self, _grid):
        if not self.collapsed:
            return

        
        if not self.tile_north.collapsed:
            self.tile_north.neighbours = set(self.valid_neighbours["options"][self.ttype]).intersection(self.tile_north.neighbours)
            self.tile_north.file = self.valid_neighbours["image_files"][self.valid_neighbours["types"].index(ttype)]


        # update corresponding to north
        
        if not self.tile_east.collapsed:
            self.tile_east.collapsed = True
            ttype = self.randomize_tile("east", self.tile_east)
            self.tile_east.ttype = ttype
            self.tile_east.neighbours = self.valid_neighbours["options"][ttype]
            self.tile_east.file = self.valid_neighbours["image_files"][self.valid_neighbours["types"].index(ttype)]

        
        if not self.tile_south.collapsed:
            self.tile_south.collapsed = True
            ttype = self.randomize_tile("south", self.tile_south)
            self.tile_south.ttype = ttype
            self.tile_south.neighbours = self.valid_neighbours["options"][ttype]
            self.tile_south.file = self.valid_neighbours["image_files"][self.valid_neighbours["types"].index(ttype)]

        
        if not self.tile_west.collapsed:
            self.tile_west.collapsed = True
            ttype = self.randomize_tile("west", self.tile_west)
            self.tile_west.ttype = ttype
            self.tile_west.neighbours = self.valid_neighbours["options"][ttype]
            self.tile_west.file = self.valid_neighbours["image_files"][self.valid_neighbours["types"].index(ttype)]



def main():
    file = "default"
    #simple = False
    if len(sys.argv) > 2:
        file = sys.argv[1]
        if sys.argv[2] == "-simple":
            simple = True
    elif len(sys.argv) > 1:
        file = sys.argv[1]

    # Get all data and seed from file
    with open(f'json/{file}.json', 'r+', encoding="Utf-8") as openedfile:
        data = json.load(openedfile)
        seed = data["meta"]["seed"]

        # If there is no seed specified use current tile as seed; NEEDS REWORK
        if len(seed) == 0:
            seed = str(time.time())
            data["meta"]["seed"] = seed
            openedfile.truncate()
            json.dump(data, openedfile, indent = 4)

    random.seed(seed)

    # Raise exception if not every specified type has its own image file specified
    if len(data["types"]) != len(data["image_files"]):
        raise Exception("Types and file names don't have equal count")

    # Load the actual image files into storage instead of reference names
    for index, _file in enumerate(data["image_files"]):
        data["image_files"][index] = Image.open(f"src/{_file}")

    # Grid size
    size = data["meta"]["size"]
    generate_image(size, data, file)


def generate_image(size, valid_neighbours, _file):
    # Define and generate initial grid
    grid = []
    for y_pos in range(size):
        row = []
        for x_pos in range(size):
            tile = Tile((x_pos, y_pos), valid_neighbours, size)
            row.append(tile)
        grid.append(row)

    # Update all tiles so the have their neighbouring tiles cached
    for y_pos in range(size):
        for x_pos in range(size):
            grid[y_pos][x_pos].neighbouring_tiles(grid)

    # Define a random starting position for the algorithm
    x_pos = random.randint(0, size - 1)
    y_pos = random.randint(0, size - 1)

    # Initialize first tile; EVERYTHIN BELOW NEEDS REWORK
    options = valid_neighbours["types"]
    index = random.randint(0, len(options) - 1)
    
    ttype = options[index]

    grid[y_pos][x_pos].collapsed = True
    grid[y_pos][x_pos].ttype = ttype
    grid[y_pos][x_pos].neighbours = valid_neighbours["options"][ttype]
    grid[y_pos][x_pos].file = valid_neighbours["image_files"][valid_neighbours["types"].index(ttype)]

    tile_size = valid_neighbours["meta"]["tile_size"]

    
    # Generate clean canvas to later add tiles
    output = Image.new("RGB", (size*tile_size, size*tile_size))

    # Main loop
    total_start = time.perf_counter()
    while True:
        # Iterate over the whole grid, update all tiles and check if finished; SHOULD WORK FINE
        start = time.perf_counter()
        finished = True
        for y_pos in range(size):
            for x_pos in range(size):
                grid[y_pos][x_pos].update(grid)
                if not grid[y_pos][x_pos].collapsed:
                    finished = False
        duration = time.perf_counter() - total_start

        # Display time of iteration
        dur = f'{duration:.2f}s'
        if duration > 60:
            duration = duration / 60
            dur = f'{int(duration)}min {((duration - int(duration)) * 60):.2f}s  '
        time_string = f'{(time.perf_counter() - start):.2f}'
        print(f'Iterationsdauer: {time_string}s, Dauer: {dur} ', end="\r")

        if finished:
            print("\n----- Finished -----")
            break

    # Convert grid to Image; SHOULD WORK
    for y_pos in range(size):
        for x_pos in range(size):
            output.paste(grid[y_pos][x_pos].file, (x_pos*tile_size, y_pos*tile_size))
            output.save(f"img/{_file}.png")

if __name__ == '__main__':
    main()

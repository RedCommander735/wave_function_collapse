import time
import multiprocessing
import math
import json
import sys
from PIL import Image, ImageFilter

class Crystal:
    def __init__(self, coords: tuple, orientation = 0, grown = False, rate = (1, 1, 1, 1)):
        self.coords = coords
        self.grown = grown
        self.rate = rate
        self.orientation = orientation
        self.spawntick = 0
        self.north = 0
        self.east  = 0
        self.south = 0
        self.west = 0
        self.crystal_north = None
        self.crystal_east = None
        self.crystal_south = None
        self.crystal_west = None

    def update(self, _grid, grid_size, tick):
        if not self.grown:
            return
        if self.spawntick == tick:
            return

        self.north = (max(self.coords[0] - 1, 0),               self.coords[1])
        self.east  = (self.coords[0],                           min(self.coords[1] + 1, grid_size - 1))
        self.south = (min(self.coords[0] + 1, grid_size - 1),   self.coords[1])
        self.west  = (self.coords[0],                           max(self.coords[1] - 1, 0))


        self.crystal_north = _grid[self.north[1]][self.north[0]]
        if not self.crystal_north.grown and tick % self.rate[0] == 0:
            self.crystal_north.grown = True
            self.crystal_north.rate = self.rate
            self.crystal_north.orientation = self.orientation
            self.crystal_north.spawntick = tick

        self.crystal_east = _grid[self.east[1]][self.east[0]]
        if not self.crystal_east.grown and tick % self.rate[1] == 0:
            self.crystal_east.grown = True
            self.crystal_east.rate = self.rate
            self.crystal_east.orientation = self.orientation
            self.crystal_east.spawntick = tick

        self.crystal_south = _grid[self.south[1]][self.south[0]]
        if not self.crystal_south.grown and tick % self.rate[2] == 0:
            self.crystal_south.grown = True
            self.crystal_south.rate = self.rate
            self.crystal_south.orientation = self.orientation
            self.crystal_south.spawntick = tick

        self.crystal_west = _grid[self.west[1]][self.west[0]]
        if not self.crystal_west.grown and tick % self.rate[3] == 0:
            self.crystal_west.grown = True
            self.crystal_west.rate = self.rate
            self.crystal_west.orientation = self.orientation
            self.crystal_west.spawntick = tick

    def pixelvalue(self, colorrange, layercount):
        refraction = (math.cos(self.orientation) + 1) * 255
        if refraction < 255 * colorrange[0]:
            refraction = 255 * colorrange[0]
        elif refraction > 255 * colorrange[1]:
            refraction = 255 * colorrange[1]
        refraction = int(refraction)

        return (refraction, refraction, refraction, int(255 / layercount))

def main():
    pointlist = []
    file = "default"
    if len(sys.argv) > 1:
        file = sys.argv[1]

    with open(f'json/{file}.json', 'r', encoding="Utf-8") as openedfile:
        jsonval = str(openedfile.read())
    data = json.loads(jsonval)
    size = int(data["meta"]["size"])
    colorrange =   [float(data["meta"]["color_range"]["min"]),\
                     float(data["meta"]["color_range"]["max"])]
    for layerindex in range(len(data["layers"])):
        layerdata = []
        for pointindex in range(len(data["layers"][str(layerindex)]["points"])):
            point_data = (
                (
                    int(data["layers"][str(layerindex)]["points"]\
                        [str(pointindex)]["position"]["x"]),
                    int(data["layers"][str(layerindex)]["points"]\
                        [str(pointindex)]["position"]["y"])
                ),
                (
                    int(data["layers"][str(layerindex)]["points"]\
                        [str(pointindex)]["rate"]["north"]),
                    int(data["layers"][str(layerindex)]["points"]\
                        [str(pointindex)]["rate"]["east"]),
                    int(data["layers"][str(layerindex)]["points"]\
                        [str(pointindex)]["rate"]["south"]),
                    int(data["layers"][str(layerindex)]["points"]\
                        [str(pointindex)]["rate"]["west"])
                ),
                float(data["layers"][str(layerindex)]["points"]\
                    [str(pointindex)]["orientation"])
            )
            layerdata.append(point_data)
        pointlist.append(layerdata)
 
    layercount = len(data["layers"])
    layers = []
    iteration = 0
    queue = multiprocessing.SimpleQueue()

    for _ in range(layercount):
        multiprocessing.Process(target=generateimage, args=([], size, 0, queue,
                            iteration, pointlist, colorrange, layercount)).start()
        iteration += 1

    stat = {}
    for i in range(layercount):
        layers.append(queue.get()[0])

        stat["layers"][i] = {"ticks": queue.get()[1], "time": queue.get()[2]}

        with open(f'stats/{file}.json', 'r', encoding="Utf-8") as stats:
            json.dump(stat, stats, indent=2)



    for i in range(1, len(layers)):
        layers[0].alpha_composite(layers[i])

    layers[0].alpha_composite(layers[0])

    layers[0] = layers[0].convert('RGB')

    layers[0] = layers[0].resize((512, 512), Image.Resampling.NEAREST).filter(ImageFilter.DETAIL)

    layers[0].save(f"img/{file}.png")

def generateimage(grid, size, tick, queue, iteration, point_data, colorrange, layercount):
    for y_pos in range(size):
        row = []
        for x_pos in range(size):
            crystal = Crystal((x_pos, y_pos))
            row.append(crystal)
        grid.append(row)

    spawn = tuple(point_data[iteration])
    for point in spawn:
        x_pos = point[0][0]
        y_pos = point[0][1]
        grid[y_pos][x_pos].rate = point[1]
        grid[y_pos][x_pos].grown = True
        grid[y_pos][x_pos].orientation = point[2]
        grid[y_pos][x_pos].spawntick = 0


    output = Image.new("RGBA", (size, size))

    # main loop
    total_start = time.perf_counter()
    while True:
        start = time.perf_counter()
        finished = True
        tick += 1
        for y_pos in range(size):
            for x_pos in range(size):
                grid[y_pos][x_pos].update(grid, size, tick)
                if not grid[y_pos][x_pos].grown:
                    finished = False
        duration = time.perf_counter() - total_start

        dur = f'{duration:.2f}s'
        sec_duration = duration
        if duration > 60:
            duration = duration / 60
            dur = f'{int(duration)}min {((duration - int(duration)) * 60):.2f}s  '
        time_string = f'{(time.perf_counter() - start):.2f}'
        print(f'Tick: {tick}, Iterationsdauer: {time_string}s, Dauer: {dur} ', end="\r")

        if finished:
            print("\n----- Finished -----")
            break
    for y_pos in range(size):
        for x_pos in range(size):
            output.putpixel((x_pos, y_pos), grid[y_pos][x_pos].pixelvalue(colorrange, layercount))
    queue.put((output, tick, sec_duration))

if __name__ == '__main__':
    main()

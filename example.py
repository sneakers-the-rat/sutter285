from sutterMP285 import Sutter
from time import time, sleep
from itertools import cycle
from threading import Timer

# a set of well positions, x, y, and z in microns
well_positions = [
    (3625,  4108,  9000),
    (3676,  13204, 9000),
    (3443,  21940, 9000),
    (12739, 4108,  9000),
    (12738, 13204, 9000),
    (12622, 22285, 9000)
]

# make a cycling object to repeat positions
well_cycle = cycle(well_positions)

# delay between position switches in seconds
delay = 10*60

# file to save positions
log_path = logpath = "D:\Users\example\Documents\log.csv"

# instantiate object
sutter = Sutter(port="COM5", timeout=10, logfile=log_path)

# sleep to give it time to set up
sleep(10)

# get firsr position and set
pos = well_cycle.next()
sutter.set_position(pos)

# cycle through positions indefinitely
while True:
    pos = well_cycle.next()
    Timer(delay, sutter.set_position, args=(pos,)).start()
    #sutter.set_position(pos)
    sleep(delay)



import asyncio
import curses
import random
import time
from itertools import cycle

from curses_tools import draw_frame, read_controls, get_frame_size

TIC_TIMEOUT = 0.1


async def blink(canvas, row, column, symbol='*', bias=True):
    if bias:
        for _ in range(random.randint(1, 100)):
            await asyncio.sleep(0)

    while True:
        canvas.addstr(row, column, symbol, curses.A_DIM)
        for _ in range(20):
            await asyncio.sleep(0)

        canvas.addstr(row, column, symbol)
        for _ in range(3):
            await asyncio.sleep(0)

        canvas.addstr(row, column, symbol, curses.A_BOLD)
        for _ in range(5):
            await asyncio.sleep(0)

        canvas.addstr(row, column, symbol)
        for _ in range(3):
            await asyncio.sleep(0)


def generate_stars(canvas_size, count):
    stars = []
    for _ in range(count):
        symbol = random.choice('+*.:')
        coordinates = [
            random.randint(2, canvas_size[0] - 2),
            random.randint(2, canvas_size[1] - 2)
        ]
        stars.append({'symbol': symbol, 'coordinates': coordinates})

    return stars


async def make_fire(canvas, start_row, start_column, rows_speed=-0.3, columns_speed=0):
    """Display animation of gun shot, direction and speed can be specified."""

    row, column = start_row, start_column

    canvas.addstr(round(row), round(column), '*')
    await asyncio.sleep(0)

    canvas.addstr(round(row), round(column), 'O')
    await asyncio.sleep(0)
    canvas.addstr(round(row), round(column), ' ')

    row += rows_speed
    column += columns_speed

    symbol = '-' if columns_speed else '|'

    rows, columns = canvas.getmaxyx()
    max_row, max_column = rows - 1, columns - 1

    curses.beep()

    while 1 < row < max_row and 1 < column < max_column:
        canvas.addstr(round(row), round(column), symbol)
        await asyncio.sleep(0)
        canvas.addstr(round(row), round(column), ' ')
        row += rows_speed
        column += columns_speed


async def animate_spaceship(canvas, spaceship_frames, coordinates, canvas_size, speed=1):
    min_row = 1
    min_column = 1
    max_row = canvas_size[0] - 1
    max_column = canvas_size[1] - 1

    row, column = coordinates

    for spaceship_frame in cycle(spaceship_frames):
        rows_direction, columns_direction, space_pressed = read_controls(canvas)
        row += rows_direction * speed
        column += columns_direction * speed

        spaceship_frame_size = get_frame_size(spaceship_frame)
        if row < min_row:
            row = min_row
        elif row > max_row - spaceship_frame_size[0]:
            row = max_row - spaceship_frame_size[0]
        elif column < min_column:
            column = min_column
        elif column > max_column - spaceship_frame_size[1]:
            column = max_column - spaceship_frame_size[1]

        for _ in range(2):
            draw_frame(canvas, row, column, spaceship_frame)
            await asyncio.sleep(0)
        draw_frame(canvas, row, column, spaceship_frame, negative=True)


def draw(canvas):
    curses.curs_set(False)
    canvas.border()
    canvas.nodelay(True)
    canvas_size = curses.window.getmaxyx(canvas)
    canvas_center_coordinates = (int(canvas_size[0] / 2), int(canvas_size[1] / 2))

    stars = generate_stars(canvas_size, 1000)
    blinking_stars = [blink(canvas, star['coordinates'][0], star['coordinates'][1], symbol=star['symbol']) for star in stars]

    shot = make_fire(canvas, canvas_center_coordinates[0] - 1, canvas_center_coordinates[1] + 2)

    with open('animation_frames/spaceship_frame_1.txt', 'r') as spaceship_frame_1_file:
        spaceship_frame_1 = spaceship_frame_1_file.read()

    with open('animation_frames/spaceship_frame_2.txt', 'r') as spaceship_frame_2_file:
        spaceship_frame_2 = spaceship_frame_2_file.read()

    spaceship_frames = (spaceship_frame_1, spaceship_frame_2)
    spaceship = animate_spaceship(canvas, spaceship_frames, canvas_center_coordinates, canvas_size, 10)

    coroutines = [*blinking_stars, shot, spaceship]

    while True:
        for coroutine in coroutines.copy():
            try:
                coroutine.send(None)
            except StopIteration:
                coroutines.remove(coroutine)
        canvas.refresh()
        time.sleep(TIC_TIMEOUT)
        if len(coroutines) == 0:
            break


if __name__ == '__main__':
    curses.update_lines_cols()
    curses.wrapper(draw)

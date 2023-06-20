import asyncio
import curses
import os
import random
import time
from itertools import cycle

from curses_tools import draw_frame, read_controls, get_frame_size
from physics import update_speed
from space_garbage import fly_garbage

TIC_TIMEOUT = 0.1
BORDER_WIDTH = 1
GARBAGE_RESPAWN_TIME = 20


coroutines = []


async def blink(canvas, row, column, symbol='*', offset_tics=0):
    await sleep(offset_tics)

    while True:
        canvas.addstr(row, column, symbol, curses.A_DIM)
        await sleep(20)

        canvas.addstr(row, column, symbol)
        await sleep(3)

        canvas.addstr(row, column, symbol, curses.A_BOLD)
        await sleep(5)

        canvas.addstr(row, column, symbol)
        await sleep(3)


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


async def animate_spaceship(canvas, spaceship_frames, start_row, start_column, canvas_height, canvas_width):
    row, column = start_row, start_column
    row_speed = column_speed = 0

    min_row = BORDER_WIDTH
    min_column = BORDER_WIDTH
    max_row = canvas_height - BORDER_WIDTH
    max_column = canvas_width - BORDER_WIDTH

    for spaceship_frame in cycle(spaceship_frames):
        rows_direction, columns_direction, space_pressed = read_controls(canvas)
        row_speed, column_speed = update_speed(row_speed, column_speed, rows_direction, columns_direction)
        row += row_speed
        column += column_speed

        frame_rows, frame_columns = get_frame_size(spaceship_frame)
        biased_max_row = max_row - frame_rows
        biased_max_column = max_column - frame_columns
        row = min(max(min_row, row), biased_max_row)
        column = min(max(min_column, column), biased_max_column)

        if space_pressed:
            biased_shot_row = row - 1
            biased_shot_column = column + 2
            shot = make_fire(canvas, biased_shot_row, biased_shot_column)
            coroutines.append(shot)

        draw_frame(canvas, row, column, spaceship_frame)
        await asyncio.sleep(0)
        draw_frame(canvas, row, column, spaceship_frame, negative=True)


async def fill_orbit_with_garbage(canvas, canvas_width, garbage_frames):
    min_column = BORDER_WIDTH
    max_column = canvas_width - BORDER_WIDTH

    while True:
        garbage_frame = random.choice(garbage_frames)

        _, frame_columns = get_frame_size(garbage_frame)
        biased_max_column = max_column - frame_columns
        garbage_item_column = random.randint(min_column, biased_max_column)

        garbage_item = fly_garbage(canvas, column=garbage_item_column, garbage_frame=garbage_frame)
        coroutines.append(garbage_item)
        await sleep(GARBAGE_RESPAWN_TIME)


async def sleep(tics=1):
    for _ in range(tics):
        await asyncio.sleep(0)


def draw(canvas):
    curses.curs_set(False)
    canvas.nodelay(True)
    canvas_height, canvas_width = curses.window.getmaxyx(canvas)
    canvas_center_row_coordinate, canvas_center_column_coordinate = int(canvas_height / 2), int(canvas_width / 2)

    stars_count = 1000

    stars = []
    for _ in range(stars_count):
        symbol = random.choice('+*.:')
        row_coordinate = random.randint(BORDER_WIDTH, canvas_height - BORDER_WIDTH - 1)
        column_coordinate = random.randint(BORDER_WIDTH, canvas_width - BORDER_WIDTH - 1)
        offset_tics = random.randint(1, 100)
        blinking_star = blink(
            canvas,
            row_coordinate,
            column_coordinate,
            symbol=symbol,
            offset_tics=offset_tics
        )
        stars.append(blinking_star)

    with open('animation_frames/spaceship_frame_1.txt', 'r') as spaceship_frame_1_file:
        spaceship_frame_1 = spaceship_frame_1_file.read()

    with open('animation_frames/spaceship_frame_2.txt', 'r') as spaceship_frame_2_file:
        spaceship_frame_2 = spaceship_frame_2_file.read()

    spaceship_frames = (spaceship_frame_1, spaceship_frame_1, spaceship_frame_2, spaceship_frame_2)
    spaceship = animate_spaceship(
        canvas,
        spaceship_frames,
        canvas_center_row_coordinate,
        canvas_center_column_coordinate,
        canvas_height,
        canvas_width,
    )

    garbage_file_names = os.listdir('animation_frames/garbage')

    garbage_frames = []
    for garbage_file_name in garbage_file_names:
        with open(f'animation_frames/garbage/{garbage_file_name}', "r") as garbage_file:
            garbage_frame = garbage_file.read()
            garbage_frames.append(garbage_frame)

    garbage = fill_orbit_with_garbage(canvas, canvas_width, garbage_frames)

    coroutines.extend([*stars, spaceship, garbage])

    while True:
        for coroutine in coroutines.copy():
            try:
                coroutine.send(None)
            except StopIteration:
                coroutines.remove(coroutine)
        canvas.border()
        canvas.refresh()
        time.sleep(TIC_TIMEOUT)
        if len(coroutines) == 0:
            break


if __name__ == '__main__':
    curses.update_lines_cols()
    curses.wrapper(draw)

import asyncio
import curses
import random
import time
from itertools import cycle

from curses_tools import draw_frame, read_controls, get_frame_size

TIC_TIMEOUT = 0.1


async def blink(canvas, row, column, symbol='*', offset_tics=0):
    for _ in range(offset_tics):
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


async def animate_spaceship(canvas, spaceship_frames, start_row, start_column, canvas_height, canvas_width, speed=1):
    row, column = start_row, start_column
    min_row = 1
    min_column = 1
    max_row = canvas_height - 1
    max_column = canvas_width - 1

    for spaceship_frame in cycle(spaceship_frames):
        rows_direction, columns_direction, space_pressed = read_controls(canvas)
        row += rows_direction * speed
        column += columns_direction * speed

        frame_rows, frame_columns = get_frame_size(spaceship_frame)
        if row < min_row:
            row = min_row
        elif row > max_row - frame_rows:
            row = max_row - frame_rows
        elif column < min_column:
            column = min_column
        elif column > max_column - frame_columns:
            column = max_column - frame_columns

        for _ in range(2):
            draw_frame(canvas, row, column, spaceship_frame)
            await asyncio.sleep(0)
        draw_frame(canvas, row, column, spaceship_frame, negative=True)


def draw(canvas):
    curses.curs_set(False)
    canvas.border()
    canvas.nodelay(True)
    canvas_height, canvas_width = curses.window.getmaxyx(canvas)
    canvas_center_row_coordinate, canvas_center_column_coordinate = int(canvas_height / 2), int(canvas_width / 2)

    stars_count = 1000

    stars = []
    for _ in range(stars_count):
        symbol = random.choice('+*.:')
        row_coordinate = random.randint(2, canvas_height - 2)
        column_coordinate = random.randint(2, canvas_width - 2)
        offset_tics = random.randint(1, 100)
        blinking_star = blink(
            canvas,
            row_coordinate,
            column_coordinate,
            symbol=symbol,
            offset_tics=offset_tics
        )
        stars.append(blinking_star)

    shot = make_fire(canvas, canvas_center_row_coordinate - 1, canvas_center_column_coordinate + 2)

    with open('animation_frames/spaceship_frame_1.txt', 'r') as spaceship_frame_1_file:
        spaceship_frame_1 = spaceship_frame_1_file.read()

    with open('animation_frames/spaceship_frame_2.txt', 'r') as spaceship_frame_2_file:
        spaceship_frame_2 = spaceship_frame_2_file.read()

    spaceship_frames = (spaceship_frame_1, spaceship_frame_2)
    spaceship = animate_spaceship(
        canvas,
        spaceship_frames,
        canvas_center_row_coordinate,
        canvas_center_column_coordinate,
        canvas_height,
        canvas_width,
        10
    )

    coroutines = [*stars, shot, spaceship]

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

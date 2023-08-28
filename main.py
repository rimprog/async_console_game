import asyncio
import curses
import os
import random
import time
from itertools import cycle

from curses_tools import draw_frame, read_controls, get_frame_size
from game_scenario import PHRASES, PLASMA_GUN_YEAR, TRASH_YEAR, max_phrase_length, get_garbage_delay_tics
from physics import update_speed
from space_garbage import fly_garbage, obstacles, obstacles_in_last_collisions

TIC_TIMEOUT = 0.1
TICS_IN_ONE_GAME_YEAR = 15
BORDER_WIDTH = 1

year = 1957

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
        for obstacle in obstacles.values():
            if obstacle.has_collision(row, column):
                obstacles_in_last_collisions[obstacle.uid] = obstacle
                return
        canvas.addstr(round(row), round(column), symbol)
        await asyncio.sleep(0)
        canvas.addstr(round(row), round(column), ' ')
        row += rows_speed
        column += columns_speed


async def animate_spaceship(canvas, spaceship_frames, start_row, start_column, canvas_height, canvas_width,
                            game_over_frame):
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

        if space_pressed and year >= PLASMA_GUN_YEAR:
            biased_shot_row = row - 1
            biased_shot_column = column + 2
            shot = make_fire(canvas, biased_shot_row, biased_shot_column)
            coroutines.append(shot)

        draw_frame(canvas, row, column, spaceship_frame)
        await asyncio.sleep(0)
        draw_frame(canvas, row, column, spaceship_frame, negative=True)

        for obstacle in obstacles.values():
            if obstacle.has_collision(row, column):
                await show_game_over(canvas, game_over_frame, start_row, start_column)


async def fill_orbit_with_garbage(canvas, canvas_width, garbage_frames):
    min_column = BORDER_WIDTH
    max_column = canvas_width - BORDER_WIDTH

    uid = 0
    while True:
        uid += 1
        garbage_frame = random.choice(garbage_frames)

        frame_row_count, frame_column_count = get_frame_size(garbage_frame)
        biased_max_column = max_column - frame_column_count
        garbage_item_column = random.randint(min_column, biased_max_column)

        garbage_delay_tics = get_garbage_delay_tics(year)

        if garbage_delay_tics:
            garbage_item = fly_garbage(canvas, garbage_item_column, garbage_frame, frame_row_count, frame_column_count,
                                       uid)
            coroutines.append(garbage_item)
            await sleep(garbage_delay_tics)
        else:
            tics_to_trash_year = (TRASH_YEAR - year) * TICS_IN_ONE_GAME_YEAR
            await sleep(tics_to_trash_year)


async def count_years(canvas):
    global year
    phrase = PHRASES.get(year)
    year_row_position = 1
    phrase_row_position = 2

    while True:
        for tics in range(TICS_IN_ONE_GAME_YEAR):
            canvas.addstr(year_row_position, BORDER_WIDTH, str(year))

            new_phrase = PHRASES[year] if PHRASES.get(year) else phrase
            phrase = new_phrase
            canvas.addstr(phrase_row_position, BORDER_WIDTH, phrase)

            canvas.refresh()
            await asyncio.sleep(0)

            phrase_cleaner_template = ' ' * len(phrase)
            canvas.addstr(phrase_row_position, BORDER_WIDTH, phrase_cleaner_template)

        year += 1


async def show_game_over(canvas, game_over_frame, start_row, start_column):
    frame_rows, frame_columns = get_frame_size(game_over_frame)
    biased_start_row = start_row - frame_rows / 2
    biased_start_column = start_column - frame_columns / 2

    while True:
        draw_frame(canvas, biased_start_row, biased_start_column, game_over_frame)
        await asyncio.sleep(0)


async def sleep(tics=1):
    for _ in range(tics):
        await asyncio.sleep(0)


def draw(canvas):
    curses.curs_set(False)
    canvas.nodelay(True)
    canvas_height, canvas_width = curses.window.getmaxyx(canvas)
    canvas_center_row_coordinate, canvas_center_column_coordinate = int(canvas_height / 2), int(canvas_width / 2)

    info_elements = 2
    info_window_start_row = canvas_height - info_elements - BORDER_WIDTH * 2
    info_window_start_column = canvas_width - max_phrase_length - BORDER_WIDTH * 2
    info_window = canvas.derwin(info_window_start_row, info_window_start_column)

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

    with open('animation_frames/game_over.txt', 'r') as game_over_frame_file:
        game_over_frame = game_over_frame_file.read()

    spaceship_frames = (spaceship_frame_1, spaceship_frame_1, spaceship_frame_2, spaceship_frame_2)
    spaceship = animate_spaceship(
        canvas,
        spaceship_frames,
        canvas_center_row_coordinate,
        canvas_center_column_coordinate,
        canvas_height,
        canvas_width,
        game_over_frame
    )

    garbage_file_names = os.listdir('animation_frames/garbage')

    garbage_frames = []
    for garbage_file_name in garbage_file_names:
        with open(f'animation_frames/garbage/{garbage_file_name}', "r") as garbage_file:
            garbage_frame = garbage_file.read()
            garbage_frames.append(garbage_frame)

    garbage = fill_orbit_with_garbage(canvas, canvas_width, garbage_frames)

    years = count_years(info_window)

    coroutines.extend([*stars, spaceship, garbage, years])

    while True:
        for coroutine in coroutines.copy():
            try:
                coroutine.send(None)
            except StopIteration:
                coroutines.remove(coroutine)
        info_window.border()
        canvas.border()
        canvas.refresh()
        time.sleep(TIC_TIMEOUT)
        if len(coroutines) == 0:
            break


if __name__ == '__main__':
    curses.update_lines_cols()
    curses.wrapper(draw)

import asyncio

from curses_tools import draw_frame
from explosion import explode
from obstacles import Obstacle

obstacles = {}
obstacles_in_last_collisions = {}


async def fly_garbage(canvas, column, garbage_frame, frame_row_count, frame_column_count, uid, speed=0.5):
    """Animate garbage, flying from top to bottom. Column position will stay same, as specified on start."""
    rows_number, columns_number = canvas.getmaxyx()

    column = max(column, 0)
    column = min(column, columns_number - 1)

    row = 0

    obstacle = Obstacle(row, column, rows_size=frame_row_count, columns_size=frame_column_count, uid=uid)
    obstacles[obstacle.uid] = obstacle

    while row < rows_number:
        obstacle.row = row
        draw_frame(canvas, row, column, garbage_frame)

        await asyncio.sleep(0)

        draw_frame(canvas, row, column, garbage_frame, negative=True)
        if obstacle.uid in obstacles_in_last_collisions.keys():
            obstacles.pop(obstacle.uid)
            obstacles_in_last_collisions.pop(obstacle.uid)

            explosion_row_center = row + frame_row_count
            explosion_column_center = column + frame_column_count / 3

            await explode(canvas, explosion_row_center, explosion_column_center)

            return

        row += speed

    obstacles.pop(obstacle.uid)

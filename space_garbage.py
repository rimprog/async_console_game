import asyncio

from curses_tools import draw_frame
from obstacles import Obstacle


obstacles = {}


async def fly_garbage(canvas, column, garbage_frame, frame_row_count, frame_column_count, uid, speed=0.5):
    """Animate garbage, flying from top to bottom. Column position will stay same, as specified on start."""
    rows_number, columns_number = canvas.getmaxyx()

    column = max(column, 0)
    column = min(column, columns_number - 1)

    row = 0

    obstacle = Obstacle(row, column, rows_size=frame_row_count, columns_size=frame_column_count, uid=uid)
    obstacles[obstacle.uid] = obstacle

    while row < rows_number:
        obstacle = obstacles[uid]
        obstacle.row = row
        draw_frame(canvas, row, column, garbage_frame)

        await asyncio.sleep(0)

        draw_frame(canvas, row, column, garbage_frame, negative=True)
        row += speed

    obstacles.pop(obstacle.uid)

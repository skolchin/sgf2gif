# Sgf2Gif script
# Go game progress animation
# (c) kol, 2023

import numpy as np
import click
from sgfmill import sgf, sgf_moves, boards
from PIL import Image, ImageDraw, ImageFont
from imageio import get_writer
from itertools import zip_longest
from collections import namedtuple

PROPS = {
    'DT' :'date played',
    'PB': 'black',
    'PW': 'white',
    'KM': 'komi',
    'HA': 'handicap',
    'RE': 'winner',
}
BOARD_COLOR = (210, 145, 80)
BLACK_COLOR = (0, 0, 0)
WHITE_COLOR = (255, 255, 255)

def move_str(bw,p):
    return f'{bw.upper()}[{chr(p[1]+ord("A")+1)}{p[0]+1}]'

def sample_str(plays, prange, limit=3):
    total_moves = len(list(plays))
    play_idx = list(range(prange[0], min(total_moves, prange[0]+limit)))
    play_idx.extend([i for i in range(max(0, prange[1]-limit), prange[1]) if i not in play_idx])

    play_seq = []
    for a, b in zip_longest(play_idx, play_idx[1:]):
        play_seq.append(move_str(plays[a][0], plays[a][1]))
        if b and a < b - limit:
            play_seq.append('...')

    return ', '.join(play_seq)

def draw_board(moves, board_size=19, image_size=512, with_numbers=False):

    # Params
    edge_size = int(image_size / 18)
    grid_space = (image_size - 2*edge_size) / float(board_size-1)
    r = max(int(grid_space / 2) - 1, 4)
    txt_space = int(grid_space / 3)
    label_fnt_sz = max(int(grid_space / 2) + 1, 2)
    move_fnt_sz = label_fnt_sz
    if moves[-1].num >= 100:
        move_fnt_sz = max(move_fnt_sz-3, 1)

    # Make an empty board image
    img = Image.new('RGB', (image_size, image_size), BOARD_COLOR)
    draw = ImageDraw.Draw(img)

    # Draw the grid and labels
    label_fnt = ImageFont.truetype('arial', size=label_fnt_sz)
    move_fnt = ImageFont.truetype('arial', size=move_fnt_sz)
    for i in range(board_size):
        x1 = edge_size + (i * grid_space)
        y1 = edge_size
        x2 = x1
        y2 = image_size - edge_size
        draw.line(((x1,y1), (x2,y2)), fill=BLACK_COLOR)
        draw.text((x1, txt_space), chr(i+ord('A')), anchor='mt', font=label_fnt, fill=BLACK_COLOR)
        draw.text((x1, image_size-txt_space), chr(i + ord('A')), anchor='mb', font=label_fnt, fill=BLACK_COLOR)

    for i in range(board_size):
        x1 = edge_size
        y1 = edge_size + (i * grid_space)
        x2 = image_size - edge_size
        y2 = y1
        draw.line(((x1,y1), (x2,y2)), fill=BLACK_COLOR)
        draw.text((txt_space, y1), str(board_size-i), anchor='lm', font=label_fnt, fill=BLACK_COLOR)
        draw.text((image_size-txt_space, y1), str(board_size-i), anchor='rm', font=label_fnt, fill=BLACK_COLOR)

    # Put the stones
    for m in moves:
        x = edge_size + int(m.pos[1] * grid_space)
        y = edge_size + int((board_size-m.pos[0]-1) * grid_space)
        if m.clr == 'b':
            draw.ellipse(((x-r,y-r), (x+r,y+r)), outline=BLACK_COLOR, fill=BLACK_COLOR)
        else:
            draw.ellipse(((x-r,y-r), (x+r,y+r)), outline=BLACK_COLOR, fill=WHITE_COLOR, width=1)
        if with_numbers:
            draw.text((x+1,y), str(m.num), anchor='mm', font=move_fnt, fill=BLACK_COLOR \
                if m.clr == 'w' else WHITE_COLOR)

    # Mark the last move
    if not with_numbers:
        m = moves[-1]
        x = edge_size + int(m.pos[1] * grid_space)
        y = edge_size + int((board_size-m.pos[0]-1) * grid_space)
        if m.clr == 'b':
            draw.ellipse(((x-r/2,y-r/2), (x+r/2+1,y+r/2+1)), outline=WHITE_COLOR)
        else:
            draw.ellipse(((x-r/2,y-r/2), (x+r/2+1,y+r/2+1)), outline=BLACK_COLOR, width=2)

    return img

Move = namedtuple('Move', ['num', 'clr', 'pos'])

def ordered_moves(board, plays, start=1):
    positions = {m:c for c, m in board.list_occupied_points()}
    return [Move(n+start, c, m) for n, (c, m) in enumerate(plays) if m in positions]

@click.command()
@click.argument('sgf-file', type=click.File('rb'))
@click.argument('gif-file', type=click.Path(dir_okay=False, writable=True))
@click.option('-s', '--size', type=click.IntRange(128, 2048), default=512, show_default=True,
    help='Image size')
@click.option('-r', '--range', 'prange', type=int, nargs=2,
    help='Starting and ending positions range')
@click.option('-d', '--duration', type=float, default=3, show_default=True,
    help='Pause between the moves')
@click.option('--final', is_flag=True,
    help='Make a picture with final game position instead of GIF file (range limit respected)')
@click.option('-n', '--numbers', is_flag=True,
    help='Show move numbers')
def main(sgf_file, gif_file, size, prange, duration, final, numbers):
    """ Replays a saved SGF file (kifu) to animated GIF.

    Usage: sgf2gif [OPTIONS] SGF_FILE GIF_FILE
    """

    # Grab the file and print out some props    
    print(f'SGF file: {sgf_file.name}')
    game = sgf.Sgf_game.from_bytes(sgf_file.read())
    props = {k:game.root.get(k) if game.root.has_property(k) else None for k in PROPS}
    print('Game properties:')
    for p, v in props.items():
        print(f'\t{PROPS[p]}: {v if v is not None else "unknown"}')

    board, plays = sgf_moves.get_setup_and_moves(game)
    total_moves = len(list(plays))
    print(f'\ttotal moves: {total_moves}')

    # Limit positions if requested and display some game moves
    if not prange:
        prange = [0, total_moves-1]
        print(f'Starting and ending moves: {sample_str(plays, prange)}')
    else:
        prange = [x-1 for x in prange]
        if prange[0] < 0 or prange[0] >= total_moves:
            print(f'ERROR: invalid starting position: {prange[0]}')
            return

        if prange[1] < 0 or prange[1] <= prange[0]:
            print(f'ERROR: invalid ending position: {prange[1]}')
            return

        if prange[1] >= total_moves:
            print(f'Ending position {prange[1]+1} is greater than total number of moves, ignoring')
            prange[1] = total_moves-1

        print(f'Limiting moves to range ({prange[0]+1}:{prange[1]+1}): {sample_str(plays, prange)}')
        plays = plays[prange[0]:prange[1]+1]

    # Replay the game on a new board
    new_board = boards.Board(game.get_size())
    if final:
        # Scroll up to the end, save final position
        for c, m in plays:
            new_board.play(m[0], m[1], c)
        img = draw_board(ordered_moves(new_board, plays, prange[0]+1),
            image_size=size, board_size=game.get_size(), with_numbers=numbers)
        img.save(gif_file)
        print(f'Final position saved to {gif_file}')
    else:
        # Generate GIF frame at every move
        with get_writer(uri=gif_file, format='GIF', duration=duration) as writer:
            for c, m in plays:
                new_board.play(m[0], m[1], c)
                img = draw_board(ordered_moves(new_board, plays, prange[0]+1),
                    image_size=size, board_size=game.get_size(), with_numbers=numbers)
                writer.append_data(np.array(img))
        print(f'File {gif_file} created')

if __name__ == '__main__':
    try:
        main()
    except Exception as ex:
        print('ERROR %s', ex)

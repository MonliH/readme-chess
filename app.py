from fastapi import FastAPI, Response
from fastapi.responses import RedirectResponse, FileResponse
import chess
import chess.svg
import re

app = FastAPI()

base_board = chess.Board()
board = chess.Board()
active_square = None
piece_legal_moves = None
last_move = None

split_pgn = re.compile(r"\s*(\d+\.)\s*")

no_cache_headers = {"Cache-Control": "no-cache,no-store,must-revalidate","expires": "0","pragma": "no-cache"}
redir_url = "http://localhost:8000" # hardcode for now

@app.get("/click-grid")
async def click(r: int, c: int):
    global active_square, piece_legal_moves, last_move
    r = 7-r
    square = chess.square(c, r)
    piece_at = board.piece_at(square) 
    if active_square is None:
        if piece_at is not None and piece_at.color == board.turn:
            new_square = square
        else:
            new_square = None
    else:
        move = chess.Move(active_square, square)
        new_square = None
        if move in board.legal_moves:
            board.push(move)
            last_move = move
        elif piece_at is not None and piece_at.color == board.turn:
            new_square = square

    if new_square is not None:
        active_square = new_square
        piece_legal_moves = [move.to_square for move in board.legal_moves if move.from_square == active_square]
    else:
        active_square = None
        piece_legal_moves = None

    return RedirectResponse(redir_url)

def get_svg(r: int, c: int):
    sq = chess.square(c, 7-r)
    piece = board.piece_at(sq)
    color = "rgb(119,149,86)" if (r+c)%2 else "rgb(235,236,208)"
    if active_square is not None and sq == active_square:
        color = "rgb(247,246,133)"
    if last_move is not None and sq in (last_move.from_square, last_move.to_square):
        color = "rgb(189,203,62)" if (r+c)%2 else "rgb(247,246,133)"

    bg = f"""<rect width="45" height="45" style="fill: {color}"/"""

    if piece is not None:
        piece_svg = chess.svg.piece(piece)
        piece_svg.replace("""viewBox="0 0 45 45"">""", """viewBox="0 0 45 45" width="40" height="40">""")
    else:
        piece_svg = """<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" version="1.2" baseProfile="tiny" viewBox="0 0 45 45" width="40" height="40"></svg>"""

    piece_svg = piece_svg.split(">")
    piece_svg.insert(1, bg)

    if piece_legal_moves is not None and sq in piece_legal_moves:
        piece_svg.insert(2, """<circle r="7" cx="50%" cy="50%" style="fill: rgba(0,0,0,0.1)"/""")

    return ">".join(piece_svg)

@app.get("/render-grid/{r}/{c}")
async def render(r: int, c: int):
    svg = get_svg(r, c)
    return Response(content=svg, media_type="image/svg+xml", headers=no_cache_headers)

@app.get("/render-moves")
async def render():
    # display played moves
    moves = list(filter(bool, split_pgn.split(base_board.variation_san(board.move_stack))))
    # chunk moves into pairs
    moves = [" ".join(moves[i:i+2]) for i in range(0, len(moves), 2)][-65:]
    n_moves = len(moves)
    height = n_moves*22+48

    moves = "\n".join((f"""<text x="6" y="{i*22 + 18+40}" style="font:18px sans-serif;">{move}</text>""" for i, move in enumerate(moves)))
    svg = f"""<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" version="1.2" baseProfile="tiny" height="{height}">\
<rect width="200" height="{height}" style="fill: rgba(255,255,255);" rx="5" ry="5" />\
<text x="6" y="32" style="font:bold 24px sans-serif;">Moves so far:</text>\
{moves}\
</svg>"""
    return Response(content=svg, media_type="image/svg+xml", headers=no_cache_headers)

@app.get("/reset-board")
async def reset():
    global board, active_square, piece_legal_moves, last_move
    board.reset()
    active_square = None
    piece_legal_moves = None
    last_move = None
    return RedirectResponse(redir_url)

@app.get("/render-reset")
async def render_reset():
    svg = """<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" version="1.2" baseProfile="tiny" width="200" height="40">\
<rect width="200" height="40" style="fill: rgb(255, 33, 33);" ry="5" rx="5"/>\
<text x="50%" y="50%" text-anchor="middle" dominant-baseline="middle" style="font:bold 15px sans-serif;fill:white;">Reset</text>\
</svg>"""
    return Response(content=svg, media_type="image/svg+xml", headers=no_cache_headers)

@app.get("/")
async def root():
    # return index.html
    return FileResponse("index.html")

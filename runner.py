import sys
sys.path.append("/Users/sophiawisdom/python-chess")
import chess
from chess import engine # will fail normally without removing references to chess.Color
import random
from flask import Flask, send_from_directory, send_file
from flask_sockets import Sockets
import time
import gevent
import json

app = Flask(__name__)
sockets = Sockets(app)

MOVE_GAP = 5 # in seconds

class RemembererBoard(chess.Board):
    def __init__(self, *args, **kwargs):
        self.states = []
        super().__init__(*args, **kwargs)

    def push_uci(self, uci):
        resp = super().push_uci(uci)
        self.states.append(self.get_pieces())
        return resp

    def get_pieces(self):
        pieces = []
        for i in range(64):
            symbol = self.piece_at(i)
            if symbol:
                position = "abcdefgh"[i%8] + str((i//8) + 1)
                pieces.append(f"{symbol}@{position}")
        return pieces

def do_move(board, move, ws):
    ws.send(bytes(move, 'utf-8'))
    print("Do some websocket stuff")
    board.push_uci(str(move))

def generate_board(num_random=10):
    board = RemembererBoard()
    for i in range(num_random):
        board.push_uci(str(random.choice(list(board.legal_moves))))
        if board.is_game_over(claim_draw=True): return generate_board(num_random)
    return board

def play_game(ws):
    board = generate_board(10)
    ws.send(json.dumps({"player": "random", "type": "player"}))
    engine = chess.engine.SimpleEngine.popen_uci("/usr/bin/stockfish")
    for state in board.states:
        analysis = engine.analyse(board, chess.engine.Limit(time=MOVE_GAP/3))
        ws.send(json.dumps({
            "pieces": state,
            "score": analysis.score.white().score(),
            "type": "update"
        }))

    ws.send(json.dumps({"player": "nonrandom", "type": "player"}))

    while not board.is_game_over(claim_draw=True):
        result = engine.play(board, chess.engine.Limit(time=MOVE_GAP))
        analysis = engine.analyse(board, chess.engine.Limit(time=MOVE_GAP))
        print("score is:", analysis.score, "fen is", board.fen())
        board.push(result.move)
        ws.send(json.dumps({
            "pieces": board.get_pieces(),
            "score": analysis.score.white().score(),
            "type": "update"
        }))
    
    if board.is_checkmate():
        ws.send(json.dumps({"winner": not board.turn(), "type": "winner"}))
    else:
        ws.send(json.dumps({"winner": None, "type": "winner"}))
    engine.quit()

@sockets.route("/chess_game")
def start_game(ws):
    while 1:
        play_game(ws)
        gevent.sleep(5)
    ws.close()

@app.route("/")
def send_index_html():
    return send_file("build/index.html")

@app.route("/<file>")
def send_stuff(file):
    return send_from_directory("build", file)

@app.route("/static/js/<file>")
def send_js(file):
    return send_from_directory("build/static/js", file)

@app.route("/static/css/<file>")
def send_css(file):
    return send_from_directory("build/static/css", file)

if __name__ == "__main__":
    from gevent import pywsgi
    from geventwebsocket.handler import WebSocketHandler
    server = pywsgi.WSGIServer(('', 7000), app, handler_class=WebSocketHandler)
    server.serve_forever()

from typing import Dict

import numpy as np
import tkinter as tk
import copy
#from FeatureExtractor import *
from myLearningAgents import *
import pickle as pickle    # cPickle is for Python 2.x only; in Python 3, simply "import pickle" and the accelerated version will be used automatically if available
import math
from numpy.core.multiarray import ndarray


class Game:
    def __init__(self, master, player1, player2, Q_learn=None, Q={}, alpha=0.3, gamma=0.9, board_size=3, streak_size=3):
        frame = tk.Frame()
        frame.grid()
        self.master = master
        master.title("Tic Tac Toe")

        self.player1 = QPlayer(discount=gamma,learningRate=alpha) ###player
        self.player2 = RandomPlayer() ###player2
        self.current_player = player1
        self.other_player = player2
        self.empty_text = ""
        self.board_size = board_size
        self.streak_size = streak_size
        self.board = Board(board_size=board_size, streak_size=streak_size)

        self.buttons = [[None for _ in range(board_size)] for _ in range(board_size)]
        for i in range(3):
            for j in range(3):
                self.buttons[i][j] = tk.Button(frame, height=board_size, width=board_size, text=self.empty_text, command=lambda i=i, j=j: self.callback(self.buttons[i][j]))
                self.buttons[i][j].grid(row=i, column=j)

        self.reset_button = tk.Button(text="Reset", command=self.reset)
        self.reset_button.grid(row=board_size)

        self.Q_learn = Q_learn
        if self.Q_learn:
            self.Q = Q
            self.alpha = alpha          # Learning rate
            self.gamma = gamma          # Discount rate
            self.share_Q_with_players()

    @property
    def Q_learn(self):
        if self._Q_learn is not None:
            return self._Q_learn
        if isinstance(self.player1, QPlayer) or isinstance(self.player2, QPlayer):
            return True

    @Q_learn.setter
    def Q_learn(self, _Q_learn):
        self._Q_learn = _Q_learn

    def share_Q_with_players(self):             # The action value table Q is shared with the QPlayers to help them make their move decisions
        if isinstance(self.player1, QPlayer):
            self.player1.Q = self.Q
        if isinstance(self.player2, QPlayer):
            self.player2.Q = self.Q

    def callback(self, button):
        if self.board.over():
            pass                # Do nothing if the game is already over
        else:
            if isinstance(self.current_player, HumanPlayer) and isinstance(self.other_player, HumanPlayer):
                if self.empty(button):
                    move = self.get_move(button)
                    self.handle_move(move)
            elif isinstance(self.current_player, HumanPlayer) and isinstance(self.other_player, ComputerPlayer):
                computer_player = self.other_player
                if self.empty(button):
                    human_move = self.get_move(button)
                    self.handle_move(human_move)
                    if not self.board.over():               # Trigger the computer's next move
                        computer_move = computer_player.get_move(self.board)
                        self.handle_move(computer_move)

    def empty(self, button):
        return button["text"] == self.empty_text

    def get_move(self, button):
        info = button.grid_info()
        move = (int(info["row"]), int(info["column"]))                # Get move coordinates from the button's metadata
        return move

    def handle_move(self, move):
        #if self.Q_learn:
        #    self.learn_Q(move)
        i, j = move         # Get row and column number of the corresponding button
        #self.buttons[i][j].configure(text=self.current_player.mark)     # Change the label on the button to the current player's mark
        self.board.place_mark(move, self.current_player.mark)           # Update the board
        if self.board.over():
            self.declare_outcome()
        ### Osher : no need to switch players in our scenario, each turn includes both players
        ###else:
        ###    self.switch_players()

    def declare_outcome(self):
        if self.board.winner() is None:
            print("Cat's game.")
        else:
            print(("The game is over. The player with mark {mark} won!".format(mark=self.current_player.mark)))

    def reset(self):
        print("Resetting...")
        for i in range(self.board_size):
            for j in range(self.board_size):
                self.buttons[i][j].configure(text=self.empty_text)
        self.board = Board(grid=np.ones((self.board_size,self.board_size))*np.nan)
        self.current_player = self.player1
        self.other_player = self.player2
        # np.random.seed(seed=0)      # Set the random seed to zero to see the Q-learning 'in action' or for debugging purposes
        self.play()

    def switch_players(self):
        if self.current_player == self.player1:
            self.current_player = self.player2
            self.other_player = self.player1
        else:
            self.current_player = self.player1
            self.other_player = self.player2

    def play(self):
        while not self.board.over():
            self.play_turn()
        '''
        if isinstance(self.player1, HumanPlayer) and isinstance(self.player2, HumanPlayer):
            pass        # For human vs. human, play relies on the callback from button presses
        elif isinstance(self.player1, HumanPlayer) and isinstance(self.player2, ComputerPlayer):
            pass
        elif isinstance(self.player1, ComputerPlayer) and isinstance(self.player2, HumanPlayer):
            first_computer_move = self.player1.get_move(self.board)      # If player 1 is a computer, it needs to be triggered to make the first move.
            self.handle_move(first_computer_move)
        elif isinstance(self.player1, ComputerPlayer) and isinstance(self.player2, ComputerPlayer):
            while not self.board.over():        # Make the two computer players play against each other without button presses
                self.play_turn()
        '''
    def getReward(self, nextState)->float:
        ### Osher: check
        if self.board.winner == "X":
            return 1000.0
        elif self.board.winner == "O":
            return -1000.0
        else:
            return 0.0

    def play_turn(self):
        ''' X moves, Y moves and then update (learn)'''
        state = copy.deepcopy(self.board)
        X_move = self.player1.get_move(self.board)
        self.handle_move(X_move)
        reward = self.getRewards(self.board)
        O_move = self.player2.get_move(self.board)
        self.handle_move(O_move)
        next_state = self.board
        self.player1.qLearningAgent.update(state, X_move, next_state, reward)

    '''
    def learn_Q(self, move):                        # If Q-learning is toggled on, "learn_Q" should be called after receiving a move from an instance of Player and before implementing the move (using Board's "place_mark" method)
        state_key = QPlayer.make_and_maybe_add_key(self.board, self.current_player.mark, self.Q)
        next_board = self.board.get_next_board(move, self.current_player.mark)
        reward = next_board.give_reward()
        next_state_key = QPlayer.make_and_maybe_add_key(next_board, self.other_player.mark, self.Q)
        if next_board.over():
            expected = reward
        else:
            next_Qs = self.Q[next_state_key]             # The Q values represent the expected future reward for player X for each available move in the next state (after the move has been made)
            if self.current_player.mark == "X":
                expected = reward + (self.gamma * min(next_Qs.values()))        # If the current player is X, the next player is O, and the move with the minimum Q value should be chosen according to our "sign convention"
            elif self.current_player.mark == "O":
                expected = reward + (self.gamma * max(next_Qs.values()))        # If the current player is O, the next player is X, and the move with the maximum Q vlue should be chosen
        change = self.alpha * (expected - self.Q[state_key][move])
        self.Q[state_key][move] += change
    '''

class Board:
    def __init__(self, board_size=3, streak_size=3):
        assert board_size>=streak_size
        self.board_size = board_size
        self.grid = np.ones((board_size, board_size)) * np.nan
        self.streak_size = streak_size

    def winner(self):
        rows, cols, diag, cross_diag = self.get_rows_cols_streaks()
        lanes = np.concatenate((rows, cols, diag, cross_diag))      # A "lane" is defined as a row, column, diagonal, or cross-diagonal
        any_lane = lambda x: any([np.array_equal(lane, x) for lane in lanes])   # Returns true if any lane is equal to the input argument "x"
        if any_lane(np.ones(self.streak_size)):
            return "X"
        elif any_lane(np.zeros(self.streak_size)):
            return "O"

    def get_rows_cols_streaks(self):
        # TODO: we might need to convert values to 1,0 and np.nan
        board_mat = np.array(copy.deepcopy(self.grid))
        board_rows = []
        board_cols = []
        for i in range(self.board_size):
            for j in range(self.board_size):
                if (j+self.streak_size<self.board_size+1):
                    row = []
                    for k in range(self.streak_size):
                        row.append(board_mat[i,j+k])
                    board_rows.append(row)
                    #print(j+self.streak_size)
                    #board_rows.append(board_mat[i, j:(j+self.streak_size])
                    #board_rows.append(row)
                if (i+self.streak_size < self.board_size+1):
                    col = []
                    for k in range(self.streak_size):
                        col.append(board_mat[i + k, j])
                    board_cols.append(col)

        # diagonals
        board_diag = []
        board_cross_diag = []
        for i in range(self.board_size):
            for j in range(self.board_size):
                if (i + self.streak_size < self.board_size + 1) and (j + self.streak_size < self.board_size + 1):
                    diag = []
                    for k in range(self.streak_size):
                        diag.append(board_mat[i+k][j+k])
                    board_diag.append(diag)
                if (i+self.streak_size < self.board_size+1) and (self.board_size-j-self.streak_size >= 0):
                    cross_diag = []
                    for k in range(self.streak_size):
                        cross_diag.append(board_mat[i+k][self.board_size-1-j-k])
                    board_cross_diag.append(cross_diag)

        return board_rows,board_cols,board_diag,board_cross_diag

    def over(self):             # The game is over if there is a winner or if no squares remain empty (cat's game)
        return (not np.any(np.isnan(self.grid))) or (self.winner() is not None)

    def place_mark(self, move, mark):       # Place a mark on the board
        num = Board.mark2num(mark)
        self.grid[tuple(move)] = num

    @staticmethod
    def mark2num(mark):         # Convert's a player's mark to a number to be inserted in the Numpy array representing the board. The mark must be either "X" or "O".
        d = {"X": 1, "O": 0, np.nan: np.nan}
        return d[mark]


    def available_moves(self):
        return [(i,j) for i in range(self.board_size) for j in range(self.board_size) if np.isnan(self.grid[i][j])]


    @staticmethod
    def available_moves_static(board):
        # Returns a list of INDICES (i,j)
        return [(i, j) for i in range(board.board_size) for j in range(board.board_size) if np.isnan(board.grid[i][j])]

    def get_next_board(self, move, mark):
        next_board = copy.deepcopy(self)
        next_board.place_mark(move, mark)
        return next_board

    def make_key(self, mark):          # For Q-learning, returns a 10-character string representing the state of the board and the player whose turn it is
        ###Osher: this should be replaced with features!
        fill_value = 3
        filled_grid = copy.deepcopy(self.grid)
        np.place(filled_grid, np.isnan(filled_grid), fill_value)
        return "".join(map(str, (list(map(int, filled_grid.flatten()))))) + mark

    def give_reward(self):                          # Assign a reward for the player with mark X in the current board position.
        if self.over():
            if self.winner() is not None:
                if self.winner() == "X":
                    return 1.0                      # Player X won -> positive reward
                elif self.winner() == "O":
                    return -1.0                     # Player O won -> negative reward
            else:
                return 0.5                          # A smaller positive reward for cat's game
        else:
            return 0.0                              # No reward if the game is not yet finished


class Player(object):
    def __init__(self, mark):
        self.mark = mark

    @property
    def opponent_mark(self):
        if self.mark == 'X':
            return 'O'
        elif self.mark == 'O':
            return 'X'
        else:
            print("The player's mark must be either 'X' or 'O'.")

class HumanPlayer(Player):
    pass

class ComputerPlayer(Player):
    pass

class RandomPlayer(ComputerPlayer):
    @staticmethod
    def get_move(board):
        moves = board.available_moves()
        if moves:   # If "moves" is not an empty list (as it would be if cat's game were reached)
            return moves[np.random.choice(len(moves))]    # Apply random selection to the index, as otherwise it will be seen as a 2D array

class THandPlayer(ComputerPlayer):
    def __init__(self, mark):
        super(THandPlayer, self).__init__(mark=mark)

    def get_move(self, board):
        moves = board.available_moves()
        if moves:
            for move in moves:
                if THandPlayer.next_move_winner(board, move, self.mark):
                    return move
                elif THandPlayer.next_move_winner(board, move, self.opponent_mark):
                    return move
            else:
                return RandomPlayer.get_move(board)

    @staticmethod
    def next_move_winner(board, move, mark):
        return board.get_next_board(move, mark).winner() == mark


class QPlayer(ComputerPlayer):
    def __init__(self, mark='X', Q={}, epsilon=0.0, discount=0.9, learningRate=0.8):
        super(QPlayer, self).__init__(mark=mark)
        self.Q = Q
        self.epsilon = 0.0 ###epsilon - change later from hardcoding the value
        ### Osher: Board.available_moves() might not be a pointer to a function
        actionFn = lambda state: Board.available_moves_static(state) ###lambda board: board.available_moves()
        self.agentOpts = {'actionFn': actionFn, 'epsilon': epsilon, \
                                      'gamma': discount, 'alpha': learningRate}
        qLearningAgent = ApproximateQAgent(exctractor=FeatureExtractor(),**self.opts)

    def get_move(self, board):
        action = self.qLearningAgent(board)
        return action


        '''
        if np.random.uniform() < self.epsilon:              # With probability epsilon, choose a move at random ("epsilon-greedy" exploration)
            return RandomPlayer.get_move(board)
        else:




            
            state_key = QPlayer.make_and_maybe_add_key(board, self.mark, self.Q)
            Qs = self.Q[state_key]

            if self.mark == "X":
                return QPlayer.stochastic_argminmax(Qs, max)
            elif self.mark == "O":
                return QPlayer.stochastic_argminmax(Qs, min)

    @staticmethod
    def make_and_maybe_add_key(board, mark, Q):     # Make a dictionary key for the current state (board + player turn) and if Q does not yet have it, add it to Q
        default_Qvalue = 1.0       # Encourages exploration
        state_key = board.make_key(mark)
        if Q.get(state_key) is None:
            moves = board.available_moves()
            Q[state_key] = {move: default_Qvalue for move in moves}    # The available moves in each state are initially given a default value of zero
        return state_key

    @staticmethod
    def stochastic_argminmax(Qs, min_or_max):       # Determines either the argmin or argmax of the array Qs such that if there are 'ties', one is chosen at random
        min_or_maxQ = min_or_max(list(Qs.values()))
        if list(Qs.values()).count(min_or_maxQ) > 1:      # If there is more than one move corresponding to the maximum Q-value, choose one at random
            best_options = [move for move in list(Qs.keys()) if Qs[move] == min_or_maxQ]
            move = best_options[np.random.choice(len(best_options))]
        else:
            move = min_or_max(Qs, key=Qs.get)
        return move
    '''

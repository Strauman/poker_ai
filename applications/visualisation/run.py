import time

from plot import PokerPlot
from pluribus.games.short_deck.player import ShortDeckPokerPlayer
from pluribus.games.short_deck.state import ShortDeckPokerState
from pluribus.poker.pot import Pot


def get_state() -> ShortDeckPokerState:
    """Gets a state to visualise"""
    n_players = 6
    pot = Pot()
    players = [
        ShortDeckPokerPlayer(player_i=player_i, initial_chips=10000, pot=pot)
        for player_i in range(n_players)
    ]
    return ShortDeckPokerState(players=players, load_pickle_files=False)


pp: PokerPlot = PokerPlot()
state: ShortDeckPokerState = get_state()
time.sleep(5)
print("updating state")
pp.update_state(state)

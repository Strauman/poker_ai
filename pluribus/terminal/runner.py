import random
import time
from typing import Dict

import click
import joblib
import numpy as np
from blessed import Terminal

from pluribus.games.short_deck.state import new_game, ShortDeckPokerState
from pluribus.terminal.ascii_objects.card_collection import AsciiCardCollection
from pluribus.terminal.ascii_objects.player import AsciiPlayer
from pluribus.terminal.ascii_objects.logger import AsciiLogger
from pluribus.terminal.render import print_footer, print_header, print_log, print_table
from pluribus.terminal.results import UserResults
from pluribus.utils.algos import rotate_list


@click.command()
@click.option('--pickle_dir', required=True, type=str)
@click.option('--agent', required=False, default="offline", type=str)
@click.option('--strategy_path', required=False, default="", type=str)
@click.option('--debug_quick_start/--no_debug_quick_start', default=False)
def run_terminal_app(
    pickle_dir: str,
    agent: str = "offline",
    strategy_path: str = "",
    debug_quick_start: bool = False
):
    """Start up terminal app.

    Example
    -------

    Call this method from this module directly from python.

    ```bash
    python -m pluribus.terminal.runner                                       \
        --agent offline                                                      \
        --pickle_dir ./research/blueprint_algo                               \
        --strategy_path ./research/blueprint_algo/offline_strategy_285800.gz \
        --no_debug_quick_start
    ```
    """
    term = Terminal()
    log = AsciiLogger(term)
    n_players: int = 3
    if debug_quick_start:
        state: ShortDeckPokerState = new_game(n_players, {}, load_pickle_files=False)
    else:
        state: ShortDeckPokerState = new_game(n_players, pickle_dir=pickle_dir)
    n_table_rotations: int = 0
    selected_action_i: int = 0
    positions = ["left", "middle", "right"]
    names = {"left": "BOT 1", "middle": "BOT 2", "right": "HUMAN"}
    if not debug_quick_start and agent in {"offline", "online"}:
        offline_strategy = joblib.load(strategy_path)
    else:
        offline_strategy = {}
    user_results: UserResults = UserResults()
    with term.cbreak(), term.hidden_cursor():
        while True:
            # Construct ascii objects to be rendered later.
            ascii_players: Dict[str, AsciiPlayer] = {}
            state_players = rotate_list(state.players[::-1], n_table_rotations)
            og_name_to_position = {}
            og_name_to_name = {}
            for player_i, player in enumerate(state_players):
                position = positions[player_i]
                is_human = names[position].lower() == "human"
                ascii_players[position] = AsciiPlayer(
                    *player.cards,
                    term=term,
                    name=names[position],
                    og_name=player.name,
                    hide_cards=not is_human and not state.is_terminal,
                    folded=not player.is_active,
                    is_turn=player.is_turn,
                    chips_in_pot=player.n_bet_chips,
                    chips_in_bank=player.n_chips,
                    is_small_blind=player.is_small_blind,
                    is_big_blind=player.is_big_blind,
                    is_dealer=player.is_dealer,
                )
                og_name_to_position[player.name] = position
                og_name_to_name[player.name] = names[position]
                if player.is_turn:
                    current_player_name = names[position]
            public_cards = AsciiCardCollection(*state.community_cards)
            if state.is_terminal:
                legal_actions = ["quit", "new game"]
                human_should_interact = True
                user_results.add_result(strategy_path, agent, state, og_name_to_name)
            else:
                og_current_name = state.current_player.name
                human_should_interact = og_name_to_position[og_current_name] == "right"
                if human_should_interact:
                    legal_actions = state.legal_actions
                else:
                    legal_actions = []
            # Render game.
            print(term.home + term.white + term.clear)
            print_header(term, state, og_name_to_name)
            print_table(
                term,
                ascii_players,
                public_cards,
                n_table_rotations,
                n_chips_in_pot=state._table.pot.total,
            )
            print_footer(term, selected_action_i, legal_actions)
            print_log(term, log)
            # Make action of some kind.
            if human_should_interact:
                # Incase the legal_actions went from length 3 to 2 and we had
                # previously picked the last one.
                selected_action_i %= len(legal_actions)
                key = term.inkey(timeout=None)
                if key.name == "KEY_LEFT":
                    selected_action_i -= 1
                    if selected_action_i < 0:
                        selected_action_i = len(legal_actions) - 1
                elif key.name == "KEY_RIGHT":
                    selected_action_i = (selected_action_i + 1) % len(legal_actions)
                elif key.name == "KEY_ENTER":
                    action = legal_actions[selected_action_i]
                    if action == "quit":
                        log.info(term.pink("quit"))
                        break
                    elif action == "new game":
                        log.clear()
                        log.info(term.green("new game"))
                        if debug_quick_start:
                            state: ShortDeckPokerState = new_game(
                                n_players, state.info_set_lut, load_pickle_files=False,
                            )
                        else:
                            state: ShortDeckPokerState = new_game(
                                n_players, state.info_set_lut,
                            )
                        n_table_rotations -= 1
                        if n_table_rotations < 0:
                            n_table_rotations = n_players - 1
                    else:
                        log.info(term.green(f"{current_player_name} chose {action}"))
                        state: ShortDeckPokerState = state.apply_action(action)
            else:
                if agent == "random":
                    action = random.choice(state.legal_actions)
                    time.sleep(0.8)
                elif agent == "offline":
                    default_strategy = {
                        action: 1 / len(state.legal_actions)
                        for action in state.legal_actions
                    }
                    this_state_strategy = offline_strategy.get(
                        state.info_set, default_strategy
                    )
                    actions = list(this_state_strategy.keys())
                    probabilties = list(this_state_strategy.values())
                    action = np.random.choice(actions, p=probabilties)
                    time.sleep(0.8)
                log.info(f"{current_player_name} chose {action}")
                state: ShortDeckPokerState = state.apply_action(action)


if __name__ == "__main__":
    run_terminal_app()

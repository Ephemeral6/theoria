# playbook.dsl -- the manual is silent on the selector by proof, not by
# laziness, so every routable thing about the selector lives here. What changed
# this round:
#
#   the panel is a COLUMN of slots, not a pair -- (29,13) and (29,14) are
#     board-constant colour 3, the signature of a collapsed slot above row 29,
#     and rows 42 down are empty, so slot B is the bottom one;
#   key(1) is up-one-slot and key(2) is down-one-slot, and the manual's silence
#     already commits to that reading: from the bottom slot, key(2) is
#     predicted to do nothing, so the cheapest probe in the game also scores
#     the leading hypothesis;
#   slot A's lane carries a badge and slot B's lane carries none, so the slots
#     are not interchangeable and the one with the task is worth being in;
#   the meter's SIGN is unknown -- cost or score -- and that outranks every
#     refinement of the drawing, because it decides whether key(4) is the thing
#     to avoid or the only thing that has ever worked;
#   ACTION5 and ACTION6 have never been pressed at all.
#
# Nothing below is a stored line of play. Every entry is a ranking rule that
# still has to be evaluated against whatever state the searcher is actually in.

order   probe_the_selector_bound_before_theorising_about_the_selector    [proof: lean]
order   settle_the_sign_of_the_meter_before_rationing_the_metered_key    [proof: lean]
order   reach_a_slot_that_has_never_been_selected                        [proof: lean]
order   read_the_second_strip_row_while_the_upper_slot_is_selected       [proof: lean]
order   press_the_two_never_pressed_keys_while_the_meter_is_still_long   [proof: lean]
order   separate_blank_from_toggle_before_trusting_either_reading        [proof: lean]
order   compare_a_strip_against_the_badge_in_its_own_lane                [proof: lean]
order   read_the_meter_tip_and_the_frame_count_after_every_command       [proof: lean]

prefer  a_state_whose_lane_contains_the_badge_over_a_lane_without_one    [ev: 1/2 lanes carry a badge]
prefer  a_slot_that_has_never_been_selected_over_one_already_mapped      [ev: 2 slots seen of a column]
prefer  a_key_never_pressed_over_a_key_whose_effect_is_already_known     [ev: 2/7 keys unpressed]
prefer  an_action_whose_outcome_the_manual_already_predicts              [ev: 1/1 open_loop replay reads]
prefer  a_press_that_makes_a_board_cell_dynamic_over_one_that_repeats    [ev: 97/4096 cells ever varied]
prefer  repeating_a_key_from_the_state_it_already_produced               [ev: 2/2 blanking presses agreed]

heuristic slots_in_the_column_never_yet_selected                        [admissible: lean]
heuristic strip_rows_still_unread_in_the_panel                          [admissible: lean]
heuristic keys_whose_effect_rests_on_a_single_witness                   [admissible: lean]
heuristic lanes_whose_badge_has_never_been_addressed                    [admissible: lean]

prune   meter_exhausted and not goal => dead                            [proof: lean]
prune   repeat_of_a_key_that_left_this_exact_state_unchanged => dead     [proof: lean]
prune   metered_press_before_the_selector_bound_is_known => dead         [proof: lean]
prune   undoing_a_selector_move_that_just_revealed_something => dead     [proof: lean]
prune   selector_move_away_from_the_badge_lane_with_nothing_learned => dead [proof: lean]

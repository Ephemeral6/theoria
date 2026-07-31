# playbook.dsl -- the compiled manual predicts three of five transitions and is
# silent on the two that matter most, so the searcher gets the strip toggle for
# free and gets nothing routable for the selector swap. Everything about the
# swap lives here. Five facts drive this playbook:
#
#   ACTION1 and ACTION2 are exact inverses and they swap which of two slots is
#     expanded -- deduced from distinct_states = 5, not guessed;
#   only ACTION4 has ever advanced the meter at (53,63); ACTION1, ACTION2,
#     ACTION3 and ACTION7 have each been pressed at least once with no tick,
#     so they are free and should be spent without hesitation;
#   the meter is at least 54 units long and one is gone, so this is an
#     exploration phase, not an endgame -- the opposite posture to a world with
#     two attempts left;
#   strip A has been visible for exactly one state in the whole record and its
#     pattern has never been read; strip B reads 2 1 1 2 1 1 over 1 1 2 1 1 2;
#   ACTION5 and ACTION6 have never been pressed, and one of them is likely the
#     coordinate click this guard language cannot express at all.

order   read_the_meter_tip_and_the_frame_count_after_every_command       [proof: lean]
order   spend_the_free_keys_before_the_metered_key                       [proof: lean]
order   expand_the_slot_whose_strip_has_never_been_read                  [proof: lean]
order   separate_blank_from_toggle_before_trusting_either_reading        [proof: lean]
order   press_the_two_never_pressed_keys_while_the_meter_is_still_long   [proof: lean]
order   compare_a_strip_against_the_badge_before_committing_the_meter    [proof: lean]

prefer  a_key_never_pressed_over_a_key_whose_effect_is_already_known     [ev: 2/7 keys unpressed]
prefer  a_key_that_has_never_ticked_the_meter_over_the_one_that_did      [ev: 1/1 meter ticks attributed]
prefer  the_selector_pair_over_the_strip_pair_while_mapping_the_panel    [ev: 96 cells vs 12 cells per press]
prefer  repeating_a_key_from_the_state_it_already_produced               [ev: 2/2 blanking presses agreed]
prefer  a_state_in_which_the_unread_strip_is_showing                     [ev: 1/6 states showed strip a]
prefer  reading_the_untouched_arena_block_before_theorising_about_it     [ev: 1/1 non_uniform arena figures]

heuristic meter_units_still_unspent_in_row_fifty_three                   [admissible: lean]
heuristic strip_patterns_still_unread_in_the_panel                       [admissible: lean]
heuristic keys_whose_effect_is_still_a_single_witness                    [admissible: lean]

prune   meter_exhausted and not goal => dead                             [proof: lean]
prune   repeat_of_a_key_that_left_this_exact_state_unchanged => dead     [proof: lean]
prune   undoing_the_selector_press_that_just_revealed_something => dead  [proof: lean]
prune   metered_press_while_a_free_press_is_still_untried => dead        [proof: lean]
prune   both_strips_read_and_no_hypothesis_about_the_badge => dead       [proof: lean]

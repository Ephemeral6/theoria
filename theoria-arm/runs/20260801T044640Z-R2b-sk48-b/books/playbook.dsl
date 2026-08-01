# playbook.dsl -- what to buy with the next command, not a route.
#
# ========= WHERE THIS ROUND STANDS =========
# The 96-cell hole is CLOSED. certify printed 24 of the divergent cells and
# every one of them is the colour six rows below it in the previous frame:
# key(1) swaps the two six-row list entries at rows 30-41 x cols 11-22, and
# key(2) swaps them back. The count checks independently -- 72 partner pairs,
# 24 of them canvas-on-both-sides, 48 differing, 96 cells. Both transitions
# are now ruled from pixels, and tape1's old mystery is dissolved: it was
# never a second strip, it was tape2 passing through after a swap.
#
# THE METHOD THAT WORKED, AND IT IS THE MAIN LESSON:
#   Declaring an ignorance loudly, in writing, with its price named in
#   advance, made the checker print the exact pixels that closed it. A
#   divergence report is an observation channel. Do not shrink the manual's
#   claims to avoid divergence; shrink them to avoid UNPRICED divergence.
#
# ========= THE BOARD AS THE MANUAL NOW SEES IT =========
#   A two-entry list, each entry six rows tall: icon in cols 11-16, value
#   strip in cols 17-22 on the entry's middle two rows. Plus a status bar at
#   row 53 with one consumed pixel at (53,63).
#   RULED FROM PIXELS: key(1) and key(2) swap the entries (96 cells);
#   key(3) and key(7) hide the lower strip (12 cells); key(4) shows it
#   (12 cells) and advanced the meter once.
#   NEVER PRESSED: key(5), key(6). NO GOAL IS KNOWN. Nothing in six states
#   resembles a win, so the win condition can only be hiding in an unpressed
#   key or in a click.
#
# ========= THE FOUR QUESTIONS NOW WORTH MONEY, IN ORDER =========
#   1. WHAT WINS. Two keys have never been pressed and every other key's
#      effect is ruled. That is where a whole mechanism can still be, and it
#      is the only place a goal section can come from.
#   2. HIDE OR TOGGLE. The strip is hidden right now, so a hide-key pressed
#      here does nothing under one reading and shows twelve cells under the
#      other. My manual predicts silence and has NO witness for it. One
#      press, legible in the raw diff.
#   3. SWAP OR SCROLL. With two entries and wrapping, swap and scroll-by-one
#      are the same permutation. Two presses of key(1) separate them: back to
#      here means two entries and an involution, a third configuration means
#      the list is longer than the window and my key(1) enumeration is right
#      only for the pair it witnessed.
#   4. ROW OR ENTRY. Do key(3)/key(4)/key(7) address a screen row or the
#      entry that owns the strip? key(1) then key(4): twelve cells at rows
#      38-39 means row, twelve at rows 32-33 means entry.
#
# ------------------------------------------------------------------------
# Do not re-buy the swap. It is ruled from pixels on both directions and a
# further press of key(1) is worth something only for question 3 or 4, not
# for the swap itself.

order     find_the_win_condition_before_refining_a_ruled_transition       [proof: lean]
order     press_a_key_never_pressed_before_re_pressing_a_ruled_one        [proof: lean]
order     close_a_declared_ignorance_before_refining_a_witnessed_rule     [proof: lean]
order     treat_predicted_silence_as_ignorance_unless_a_witness_backs_it  [proof: lean]
order     rank_by_witnesses_a_command_would_create_not_by_pixels_it_moves [proof: lean]
order     read_a_refutation_by_its_divergence_set_not_by_whether_it_fired [proof: lean]
order     price_an_ignorance_in_advance_so_the_checker_prints_its_pixels  [proof: lean]
order     stop_pressing_a_key_the_moment_its_question_has_been_answered   [proof: lean]
order     separate_two_keys_with_one_effect_before_trusting_either        [proof: lean]
order     check_a_rule_can_fire_before_ranking_a_probe_that_tests_it      [proof: lean]
order     prefer_constructs_that_cannot_fail_to_compile_over_expressive_ones [proof: lean]

prune     every_rule_it_would_witness_is_already_at_full_coverage => dead   [proof: lean]
prune     repeats_a_key_whose_effect_here_is_already_known_cell_by_cell => dead [proof: lean]
prune     ranked_only_because_the_manual_predicts_the_most_pixels => dead   [proof: lean]
prune     ranked_only_because_a_refutation_fired_on_it => dead              [proof: lean]
prune     divergence_lies_only_where_the_manual_declared_ignorance => dead  [proof: lean]
prune     restates_a_transition_the_previous_command_just_answered => dead  [proof: lean]
prune     asks_a_question_the_current_state_cannot_pose => dead             [proof: lean]
prune     would_confirm_a_permutation_already_ruled_in_both_directions => dead [proof: lean]

heuristic keys_never_pressed_in_this_world                                [admissible: lean]
heuristic mechanisms_that_could_still_carry_a_win_condition               [admissible: lean]
heuristic silences_the_manual_asserts_without_a_witness                   [admissible: lean]
heuristic configurations_no_frame_has_ever_shown_in_full                  [admissible: lean]
heuristic live_readings_a_single_command_can_eliminate                    [admissible: lean]
heuristic divergent_cells_lying_outside_a_declared_ignorance              [admissible: lean]
heuristic guards_whose_only_support_is_a_cell_no_frame_has_shown          [admissible: lean]

prefer    an_unpressed_key_over_a_key_already_at_full_coverage            [ev: 2/7 keys]
prefer    a_key_whose_predicted_silence_here_has_never_been_witnessed     [ev: 4/7 keys]
prefer    the_press_that_splits_a_one_shot_from_a_counter                 [ev: 1/1 witnesses]
prefer    the_press_that_splits_a_swap_from_a_scroll                      [ev: 1/1 permutations]
prefer    the_press_that_asks_whether_a_key_addresses_a_row_or_an_entry   [ev: 3/5 diffs]
prefer    a_probe_whose_outcome_is_legible_in_the_raw_diff                [ev: 5/5 diffs]

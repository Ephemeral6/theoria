# ----------------------------------------------------------
# 素材 B: Playbook for 1D Peg Solitaire
# ----------------------------------------------------------

order center_first [proof: none]

prune isolated_peg(p) and no_adjacent_peg(p) => dead [proof: lean]

heuristic peg_count(board) [admissible: none]

prefer edge_jumps_last [ev: 3/5]

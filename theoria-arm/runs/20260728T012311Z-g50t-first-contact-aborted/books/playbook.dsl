# playbook.dsl -- round 1
#
# Six commands seen, each action tried at most once. Almost nothing here is
# earned yet; what follows is only what the six transitions actually license.
#
# Deliberately absent: any ordering over ACTION1..ACTION4 as directions. I have
# no evidence any of them is a direction. ACTION2 ran a 7-frame cascade over
# the two 5x5 maze slots without any intermediate frame touching row 13, so
# whatever it did, it did not slide anything through the wall row.

  prefer   drop_commands_that_changed_nothing        [ev: 2/2 levels]
  prefer   spend_budget_only_on_changing_commands    [ev: 2/2 levels]
  prefer   commit_indicator_last                     [ev: 1/1 levels]
  heuristic pip_to_exit_grid_distance                [admissible: unproven]

(define (domain theoria-domain)
  (:requirements :strips :typing)

  (:types cell agent gate switch - object)
    ; direction is implicit in action names

  (:predicates
    (at ?o - object ?c - cell)
    (free ?c - cell)
    (adjacent-up ?c1 - cell ?c2 - cell)
    (adjacent-down ?c1 - cell ?c2 - cell)
    (adjacent-left ?c1 - cell ?c2 - cell)
    (adjacent-right ?c1 - cell ?c2 - cell)
    (boundary-up ?c - cell)
    (boundary-down ?c - cell)
    (boundary-left ?c - cell)
    (boundary-right ?c - cell)
    (colour-3 ?c - cell)
    (colour-4 ?c - cell)
    (colour-7 ?c - cell)
    (colour-8 ?c - cell)
    (landmark-exit-a ?c - cell)
    (landmark-exit-b ?c - cell)
    (distinct ?c1 - cell ?c2 - cell)
    (present ?o - object)
    (anchored ?o - object ?c - cell)
  )

  (:action step-up
    :parameters (?agent - agent ?dest - cell ?agent-pos - cell)
    :precondition (and
      (at ?agent ?agent-pos)
      (adjacent-up ?agent-pos ?dest)
      (free ?dest)
    )
    :effect (and
      (not (at ?agent ?agent-pos))
      (at ?agent ?dest)
      (not (free ?dest))
      (free ?agent-pos)
    )
  )

  (:action step-down
    :parameters (?agent - agent ?dest - cell ?agent-pos - cell)
    :precondition (and
      (at ?agent ?agent-pos)
      (adjacent-down ?agent-pos ?dest)
      (free ?dest)
    )
    :effect (and
      (not (at ?agent ?agent-pos))
      (at ?agent ?dest)
      (not (free ?dest))
      (free ?agent-pos)
    )
  )

  (:action step-left
    :parameters (?agent - agent ?dest - cell ?agent-pos - cell)
    :precondition (and
      (at ?agent ?agent-pos)
      (adjacent-left ?agent-pos ?dest)
      (free ?dest)
    )
    :effect (and
      (not (at ?agent ?agent-pos))
      (at ?agent ?dest)
      (not (free ?dest))
      (free ?agent-pos)
    )
  )

  (:action step-right
    :parameters (?agent - agent ?dest - cell ?agent-pos - cell)
    :precondition (and
      (at ?agent ?agent-pos)
      (adjacent-right ?agent-pos ?dest)
      (free ?dest)
    )
    :effect (and
      (not (at ?agent ?agent-pos))
      (at ?agent ?dest)
      (not (free ?dest))
      (free ?agent-pos)
    )
  )

  (:action warp-a-up
    :parameters (?agent - agent ?via - cell ?dest - cell ?agent-pos - cell)
    :precondition (and
      (at ?agent ?agent-pos)
      (adjacent-up ?agent-pos ?via)
      (colour-3 ?via)
      (landmark-exit-a ?dest)
      (distinct ?agent-pos ?dest)
    )
    :effect (and
      (not (at ?agent ?agent-pos))
      (at ?agent ?dest)
      (not (free ?dest))
      (free ?agent-pos)
    )
  )

  (:action warp-a-down
    :parameters (?agent - agent ?via - cell ?dest - cell ?agent-pos - cell)
    :precondition (and
      (at ?agent ?agent-pos)
      (adjacent-down ?agent-pos ?via)
      (colour-3 ?via)
      (landmark-exit-a ?dest)
      (distinct ?agent-pos ?dest)
    )
    :effect (and
      (not (at ?agent ?agent-pos))
      (at ?agent ?dest)
      (not (free ?dest))
      (free ?agent-pos)
    )
  )

  (:action warp-a-left
    :parameters (?agent - agent ?via - cell ?dest - cell ?agent-pos - cell)
    :precondition (and
      (at ?agent ?agent-pos)
      (adjacent-left ?agent-pos ?via)
      (colour-3 ?via)
      (landmark-exit-a ?dest)
      (distinct ?agent-pos ?dest)
    )
    :effect (and
      (not (at ?agent ?agent-pos))
      (at ?agent ?dest)
      (not (free ?dest))
      (free ?agent-pos)
    )
  )

  (:action warp-a-right
    :parameters (?agent - agent ?via - cell ?dest - cell ?agent-pos - cell)
    :precondition (and
      (at ?agent ?agent-pos)
      (adjacent-right ?agent-pos ?via)
      (colour-3 ?via)
      (landmark-exit-a ?dest)
      (distinct ?agent-pos ?dest)
    )
    :effect (and
      (not (at ?agent ?agent-pos))
      (at ?agent ?dest)
      (not (free ?dest))
      (free ?agent-pos)
    )
  )

  (:action warp-b-up
    :parameters (?agent - agent ?via - cell ?dest - cell ?agent-pos - cell)
    :precondition (and
      (at ?agent ?agent-pos)
      (adjacent-up ?agent-pos ?via)
      (colour-4 ?via)
      (landmark-exit-b ?dest)
      (distinct ?agent-pos ?dest)
    )
    :effect (and
      (not (at ?agent ?agent-pos))
      (at ?agent ?dest)
      (not (free ?dest))
      (free ?agent-pos)
    )
  )

  (:action warp-b-down
    :parameters (?agent - agent ?via - cell ?dest - cell ?agent-pos - cell)
    :precondition (and
      (at ?agent ?agent-pos)
      (adjacent-down ?agent-pos ?via)
      (colour-4 ?via)
      (landmark-exit-b ?dest)
      (distinct ?agent-pos ?dest)
    )
    :effect (and
      (not (at ?agent ?agent-pos))
      (at ?agent ?dest)
      (not (free ?dest))
      (free ?agent-pos)
    )
  )

  (:action warp-b-left
    :parameters (?agent - agent ?via - cell ?dest - cell ?agent-pos - cell)
    :precondition (and
      (at ?agent ?agent-pos)
      (adjacent-left ?agent-pos ?via)
      (colour-4 ?via)
      (landmark-exit-b ?dest)
      (distinct ?agent-pos ?dest)
    )
    :effect (and
      (not (at ?agent ?agent-pos))
      (at ?agent ?dest)
      (not (free ?dest))
      (free ?agent-pos)
    )
  )

  (:action warp-b-right
    :parameters (?agent - agent ?via - cell ?dest - cell ?agent-pos - cell)
    :precondition (and
      (at ?agent ?agent-pos)
      (adjacent-right ?agent-pos ?via)
      (colour-4 ?via)
      (landmark-exit-b ?dest)
      (distinct ?agent-pos ?dest)
    )
    :effect (and
      (not (at ?agent ?agent-pos))
      (at ?agent ?dest)
      (not (free ?dest))
      (free ?agent-pos)
    )
  )

  (:action switch-press-up
    :parameters (?agent - agent ?via - cell ?switch - switch ?gate - gate ?agent-pos - cell ?switch-pos - cell ?gate-pos - cell)
    :precondition (and
      (at ?agent ?agent-pos)
      (anchored ?switch ?switch-pos)
      (anchored ?gate ?gate-pos)
      (adjacent-up ?agent-pos ?via)
      (colour-7 ?via)
      (present ?gate)
    )
    :effect (and
      (colour-8 ?switch-pos)
      (not (colour-7 ?switch-pos))
      (not (present ?gate))
      (free ?gate-pos)
    )
  )
  ;; rule gate_opens_up shares this guard and is folded into switch-press-up (cascade single_frame)

  (:action switch-press-down
    :parameters (?agent - agent ?via - cell ?switch - switch ?gate - gate ?agent-pos - cell ?switch-pos - cell ?gate-pos - cell)
    :precondition (and
      (at ?agent ?agent-pos)
      (anchored ?switch ?switch-pos)
      (anchored ?gate ?gate-pos)
      (adjacent-down ?agent-pos ?via)
      (colour-7 ?via)
      (present ?gate)
    )
    :effect (and
      (colour-8 ?switch-pos)
      (not (colour-7 ?switch-pos))
      (not (present ?gate))
      (free ?gate-pos)
    )
  )
  ;; rule gate_opens_down shares this guard and is folded into switch-press-down (cascade single_frame)

  (:action switch-press-left
    :parameters (?agent - agent ?via - cell ?switch - switch ?gate - gate ?agent-pos - cell ?switch-pos - cell ?gate-pos - cell)
    :precondition (and
      (at ?agent ?agent-pos)
      (anchored ?switch ?switch-pos)
      (anchored ?gate ?gate-pos)
      (adjacent-left ?agent-pos ?via)
      (colour-7 ?via)
      (present ?gate)
    )
    :effect (and
      (colour-8 ?switch-pos)
      (not (colour-7 ?switch-pos))
      (not (present ?gate))
      (free ?gate-pos)
    )
  )
  ;; rule gate_opens_left shares this guard and is folded into switch-press-left (cascade single_frame)

  (:action switch-press-right
    :parameters (?agent - agent ?via - cell ?switch - switch ?gate - gate ?agent-pos - cell ?switch-pos - cell ?gate-pos - cell)
    :precondition (and
      (at ?agent ?agent-pos)
      (anchored ?switch ?switch-pos)
      (anchored ?gate ?gate-pos)
      (adjacent-right ?agent-pos ?via)
      (colour-7 ?via)
      (present ?gate)
    )
    :effect (and
      (colour-8 ?switch-pos)
      (not (colour-7 ?switch-pos))
      (not (present ?gate))
      (free ?gate-pos)
    )
  )
  ;; rule gate_opens_right shares this guard and is folded into switch-press-right (cascade single_frame)

  (:action switch-release-up
    :parameters (?agent - agent ?via - cell ?switch - switch ?gate - gate ?agent-pos - cell ?switch-pos - cell ?gate-pos - cell)
    :precondition (and
      (at ?agent ?agent-pos)
      (anchored ?switch ?switch-pos)
      (anchored ?gate ?gate-pos)
      (adjacent-up ?agent-pos ?via)
      (colour-8 ?via)
    )
    :effect (and
      (colour-7 ?switch-pos)
      (not (colour-8 ?switch-pos))
      (present ?gate)
      (not (free ?gate-pos))
    )
  )
  ;; rule gate_closes_up shares this guard and is folded into switch-release-up (cascade single_frame)

  (:action switch-release-down
    :parameters (?agent - agent ?via - cell ?switch - switch ?gate - gate ?agent-pos - cell ?switch-pos - cell ?gate-pos - cell)
    :precondition (and
      (at ?agent ?agent-pos)
      (anchored ?switch ?switch-pos)
      (anchored ?gate ?gate-pos)
      (adjacent-down ?agent-pos ?via)
      (colour-8 ?via)
    )
    :effect (and
      (colour-7 ?switch-pos)
      (not (colour-8 ?switch-pos))
      (present ?gate)
      (not (free ?gate-pos))
    )
  )
  ;; rule gate_closes_down shares this guard and is folded into switch-release-down (cascade single_frame)

  (:action switch-release-left
    :parameters (?agent - agent ?via - cell ?switch - switch ?gate - gate ?agent-pos - cell ?switch-pos - cell ?gate-pos - cell)
    :precondition (and
      (at ?agent ?agent-pos)
      (anchored ?switch ?switch-pos)
      (anchored ?gate ?gate-pos)
      (adjacent-left ?agent-pos ?via)
      (colour-8 ?via)
    )
    :effect (and
      (colour-7 ?switch-pos)
      (not (colour-8 ?switch-pos))
      (present ?gate)
      (not (free ?gate-pos))
    )
  )
  ;; rule gate_closes_left shares this guard and is folded into switch-release-left (cascade single_frame)

  (:action switch-release-right
    :parameters (?agent - agent ?via - cell ?switch - switch ?gate - gate ?agent-pos - cell ?switch-pos - cell ?gate-pos - cell)
    :precondition (and
      (at ?agent ?agent-pos)
      (anchored ?switch ?switch-pos)
      (anchored ?gate ?gate-pos)
      (adjacent-right ?agent-pos ?via)
      (colour-8 ?via)
    )
    :effect (and
      (colour-7 ?switch-pos)
      (not (colour-8 ?switch-pos))
      (present ?gate)
      (not (free ?gate-pos))
    )
  )
  ;; rule gate_closes_right shares this guard and is folded into switch-release-right (cascade single_frame)

)
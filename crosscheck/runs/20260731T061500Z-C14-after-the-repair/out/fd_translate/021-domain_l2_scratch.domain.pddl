(define (domain theoria-domain)
  (:requirements :strips :typing)

  (:types cell cart door switch - object)
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
    :parameters (?cart - cart ?dest - cell ?cart-pos - cell)
    :precondition (and
      (at ?cart ?cart-pos)
      (adjacent-up ?cart-pos ?dest)
      (free ?dest)
    )
    :effect (and
      (not (at ?cart ?cart-pos))
      (at ?cart ?dest)
      (not (free ?dest))
      (free ?cart-pos)
    )
  )

  (:action step-down
    :parameters (?cart - cart ?dest - cell ?cart-pos - cell)
    :precondition (and
      (at ?cart ?cart-pos)
      (adjacent-down ?cart-pos ?dest)
      (free ?dest)
    )
    :effect (and
      (not (at ?cart ?cart-pos))
      (at ?cart ?dest)
      (not (free ?dest))
      (free ?cart-pos)
    )
  )

  (:action step-left
    :parameters (?cart - cart ?dest - cell ?cart-pos - cell)
    :precondition (and
      (at ?cart ?cart-pos)
      (adjacent-left ?cart-pos ?dest)
      (free ?dest)
    )
    :effect (and
      (not (at ?cart ?cart-pos))
      (at ?cart ?dest)
      (not (free ?dest))
      (free ?cart-pos)
    )
  )

  (:action step-right
    :parameters (?cart - cart ?dest - cell ?cart-pos - cell)
    :precondition (and
      (at ?cart ?cart-pos)
      (adjacent-right ?cart-pos ?dest)
      (free ?dest)
    )
    :effect (and
      (not (at ?cart ?cart-pos))
      (at ?cart ?dest)
      (not (free ?dest))
      (free ?cart-pos)
    )
  )

  (:action warp-a-up
    :parameters (?cart - cart ?via - cell ?dest - cell ?cart-pos - cell)
    :precondition (and
      (at ?cart ?cart-pos)
      (adjacent-up ?cart-pos ?via)
      (colour-3 ?via)
      (landmark-exit-a ?dest)
      (distinct ?cart-pos ?dest)
    )
    :effect (and
      (not (at ?cart ?cart-pos))
      (at ?cart ?dest)
      (not (free ?dest))
      (free ?cart-pos)
    )
  )

  (:action warp-a-down
    :parameters (?cart - cart ?via - cell ?dest - cell ?cart-pos - cell)
    :precondition (and
      (at ?cart ?cart-pos)
      (adjacent-down ?cart-pos ?via)
      (colour-3 ?via)
      (landmark-exit-a ?dest)
      (distinct ?cart-pos ?dest)
    )
    :effect (and
      (not (at ?cart ?cart-pos))
      (at ?cart ?dest)
      (not (free ?dest))
      (free ?cart-pos)
    )
  )

  (:action warp-a-left
    :parameters (?cart - cart ?via - cell ?dest - cell ?cart-pos - cell)
    :precondition (and
      (at ?cart ?cart-pos)
      (adjacent-left ?cart-pos ?via)
      (colour-3 ?via)
      (landmark-exit-a ?dest)
      (distinct ?cart-pos ?dest)
    )
    :effect (and
      (not (at ?cart ?cart-pos))
      (at ?cart ?dest)
      (not (free ?dest))
      (free ?cart-pos)
    )
  )

  (:action warp-a-right
    :parameters (?cart - cart ?via - cell ?dest - cell ?cart-pos - cell)
    :precondition (and
      (at ?cart ?cart-pos)
      (adjacent-right ?cart-pos ?via)
      (colour-3 ?via)
      (landmark-exit-a ?dest)
      (distinct ?cart-pos ?dest)
    )
    :effect (and
      (not (at ?cart ?cart-pos))
      (at ?cart ?dest)
      (not (free ?dest))
      (free ?cart-pos)
    )
  )

  (:action warp-b-up
    :parameters (?cart - cart ?via - cell ?dest - cell ?cart-pos - cell)
    :precondition (and
      (at ?cart ?cart-pos)
      (adjacent-up ?cart-pos ?via)
      (colour-4 ?via)
      (landmark-exit-b ?dest)
      (distinct ?cart-pos ?dest)
    )
    :effect (and
      (not (at ?cart ?cart-pos))
      (at ?cart ?dest)
      (not (free ?dest))
      (free ?cart-pos)
    )
  )

  (:action warp-b-down
    :parameters (?cart - cart ?via - cell ?dest - cell ?cart-pos - cell)
    :precondition (and
      (at ?cart ?cart-pos)
      (adjacent-down ?cart-pos ?via)
      (colour-4 ?via)
      (landmark-exit-b ?dest)
      (distinct ?cart-pos ?dest)
    )
    :effect (and
      (not (at ?cart ?cart-pos))
      (at ?cart ?dest)
      (not (free ?dest))
      (free ?cart-pos)
    )
  )

  (:action warp-b-left
    :parameters (?cart - cart ?via - cell ?dest - cell ?cart-pos - cell)
    :precondition (and
      (at ?cart ?cart-pos)
      (adjacent-left ?cart-pos ?via)
      (colour-4 ?via)
      (landmark-exit-b ?dest)
      (distinct ?cart-pos ?dest)
    )
    :effect (and
      (not (at ?cart ?cart-pos))
      (at ?cart ?dest)
      (not (free ?dest))
      (free ?cart-pos)
    )
  )

  (:action warp-b-right
    :parameters (?cart - cart ?via - cell ?dest - cell ?cart-pos - cell)
    :precondition (and
      (at ?cart ?cart-pos)
      (adjacent-right ?cart-pos ?via)
      (colour-4 ?via)
      (landmark-exit-b ?dest)
      (distinct ?cart-pos ?dest)
    )
    :effect (and
      (not (at ?cart ?cart-pos))
      (at ?cart ?dest)
      (not (free ?dest))
      (free ?cart-pos)
    )
  )

  (:action switch-press-up
    :parameters (?cart - cart ?via - cell ?switch - switch ?door - door ?cart-pos - cell ?switch-pos - cell ?door-pos - cell)
    :precondition (and
      (at ?cart ?cart-pos)
      (anchored ?switch ?switch-pos)
      (anchored ?door ?door-pos)
      (adjacent-up ?cart-pos ?via)
      (colour-7 ?via)
      (present ?door)
    )
    :effect (and
      (colour-8 ?switch-pos)
      (not (colour-7 ?switch-pos))
      (not (present ?door))
      (free ?door-pos)
    )
  )
  ;; rule door_opens_up shares this guard and is folded into switch-press-up (cascade single_frame)

  (:action switch-press-down
    :parameters (?cart - cart ?via - cell ?switch - switch ?door - door ?cart-pos - cell ?switch-pos - cell ?door-pos - cell)
    :precondition (and
      (at ?cart ?cart-pos)
      (anchored ?switch ?switch-pos)
      (anchored ?door ?door-pos)
      (adjacent-down ?cart-pos ?via)
      (colour-7 ?via)
      (present ?door)
    )
    :effect (and
      (colour-8 ?switch-pos)
      (not (colour-7 ?switch-pos))
      (not (present ?door))
      (free ?door-pos)
    )
  )
  ;; rule door_opens_down shares this guard and is folded into switch-press-down (cascade single_frame)

  (:action switch-press-left
    :parameters (?cart - cart ?via - cell ?switch - switch ?door - door ?cart-pos - cell ?switch-pos - cell ?door-pos - cell)
    :precondition (and
      (at ?cart ?cart-pos)
      (anchored ?switch ?switch-pos)
      (anchored ?door ?door-pos)
      (adjacent-left ?cart-pos ?via)
      (colour-7 ?via)
      (present ?door)
    )
    :effect (and
      (colour-8 ?switch-pos)
      (not (colour-7 ?switch-pos))
      (not (present ?door))
      (free ?door-pos)
    )
  )
  ;; rule door_opens_left shares this guard and is folded into switch-press-left (cascade single_frame)

  (:action switch-press-right
    :parameters (?cart - cart ?via - cell ?switch - switch ?door - door ?cart-pos - cell ?switch-pos - cell ?door-pos - cell)
    :precondition (and
      (at ?cart ?cart-pos)
      (anchored ?switch ?switch-pos)
      (anchored ?door ?door-pos)
      (adjacent-right ?cart-pos ?via)
      (colour-7 ?via)
      (present ?door)
    )
    :effect (and
      (colour-8 ?switch-pos)
      (not (colour-7 ?switch-pos))
      (not (present ?door))
      (free ?door-pos)
    )
  )
  ;; rule door_opens_right shares this guard and is folded into switch-press-right (cascade single_frame)

  (:action switch-release-up
    :parameters (?cart - cart ?via - cell ?switch - switch ?door - door ?cart-pos - cell ?switch-pos - cell ?door-pos - cell)
    :precondition (and
      (at ?cart ?cart-pos)
      (anchored ?switch ?switch-pos)
      (anchored ?door ?door-pos)
      (adjacent-up ?cart-pos ?via)
      (colour-8 ?via)
    )
    :effect (and
      (colour-7 ?switch-pos)
      (not (colour-8 ?switch-pos))
      (present ?door)
      (not (free ?door-pos))
    )
  )
  ;; rule door_closes_up shares this guard and is folded into switch-release-up (cascade single_frame)

  (:action switch-release-down
    :parameters (?cart - cart ?via - cell ?switch - switch ?door - door ?cart-pos - cell ?switch-pos - cell ?door-pos - cell)
    :precondition (and
      (at ?cart ?cart-pos)
      (anchored ?switch ?switch-pos)
      (anchored ?door ?door-pos)
      (adjacent-down ?cart-pos ?via)
      (colour-8 ?via)
    )
    :effect (and
      (colour-7 ?switch-pos)
      (not (colour-8 ?switch-pos))
      (present ?door)
      (not (free ?door-pos))
    )
  )
  ;; rule door_closes_down shares this guard and is folded into switch-release-down (cascade single_frame)

  (:action switch-release-left
    :parameters (?cart - cart ?via - cell ?switch - switch ?door - door ?cart-pos - cell ?switch-pos - cell ?door-pos - cell)
    :precondition (and
      (at ?cart ?cart-pos)
      (anchored ?switch ?switch-pos)
      (anchored ?door ?door-pos)
      (adjacent-left ?cart-pos ?via)
      (colour-8 ?via)
    )
    :effect (and
      (colour-7 ?switch-pos)
      (not (colour-8 ?switch-pos))
      (present ?door)
      (not (free ?door-pos))
    )
  )
  ;; rule door_closes_left shares this guard and is folded into switch-release-left (cascade single_frame)

  (:action switch-release-right
    :parameters (?cart - cart ?via - cell ?switch - switch ?door - door ?cart-pos - cell ?switch-pos - cell ?door-pos - cell)
    :precondition (and
      (at ?cart ?cart-pos)
      (anchored ?switch ?switch-pos)
      (anchored ?door ?door-pos)
      (adjacent-right ?cart-pos ?via)
      (colour-8 ?via)
    )
    :effect (and
      (colour-7 ?switch-pos)
      (not (colour-8 ?switch-pos))
      (present ?door)
      (not (free ?door-pos))
    )
  )
  ;; rule door_closes_right shares this guard and is folded into switch-release-right (cascade single_frame)

)
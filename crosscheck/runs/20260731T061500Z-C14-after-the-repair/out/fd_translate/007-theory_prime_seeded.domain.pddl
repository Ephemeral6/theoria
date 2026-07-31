(define (domain theoria-domain)
  (:requirements :strips :typing)

  (:types cell cart switch door - object)
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
    (landmark-portal-exit ?c - cell)
    (distinct ?c1 - cell ?c2 - cell)
    (present ?o - object)
    (anchored ?o - object ?c - cell)
  )

  (:action push-up
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

  (:action push-down
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

  (:action push-left
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

  (:action push-right
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

  (:action push-onto-crate
    :parameters (?cart - cart ?via - cell ?dest - cell ?cart-pos - cell)
    :precondition (and
      (at ?cart ?cart-pos)
      (adjacent-right ?cart-pos ?via)
      (colour-4 ?via)
      (adjacent-right ?cart-pos ?dest)
    )
    :effect (and
      (not (at ?cart ?cart-pos))
      (at ?cart ?dest)
      (not (free ?dest))
      (free ?cart-pos)
    )
  )

  (:action teleport-down
    :parameters (?cart - cart ?via - cell ?dest - cell ?cart-pos - cell)
    :precondition (and
      (at ?cart ?cart-pos)
      (adjacent-down ?cart-pos ?via)
      (colour-3 ?via)
      (landmark-portal-exit ?dest)
      (distinct ?cart-pos ?dest)
    )
    :effect (and
      (not (at ?cart ?cart-pos))
      (at ?cart ?dest)
      (not (free ?dest))
      (free ?cart-pos)
    )
  )

  (:action switch-on-up
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
  ;; rule door_opens_up shares this guard and is folded into switch-on-up (cascade single_frame)

  (:action switch-on-down
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
  ;; rule door_opens_down shares this guard and is folded into switch-on-down (cascade single_frame)

  (:action switch-on-left
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
  ;; rule door_opens_left shares this guard and is folded into switch-on-left (cascade single_frame)

  (:action switch-on-right
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
  ;; rule door_opens_right shares this guard and is folded into switch-on-right (cascade single_frame)

  (:action switch-off-up
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
  ;; rule door_shuts_up shares this guard and is folded into switch-off-up (cascade single_frame)

  (:action switch-off-down
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
  ;; rule door_shuts_down shares this guard and is folded into switch-off-down (cascade single_frame)

  (:action switch-off-left
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
  ;; rule door_shuts_left shares this guard and is folded into switch-off-left (cascade single_frame)

  (:action switch-off-right
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
  ;; rule door_shuts_right shares this guard and is folded into switch-off-right (cascade single_frame)

)
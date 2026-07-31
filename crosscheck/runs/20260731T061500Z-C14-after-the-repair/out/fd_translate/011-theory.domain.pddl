(define (domain theoria-domain)
  (:requirements :strips :typing)

  (:types cell cart button door - object)
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

  (:action press-up
    :parameters (?cart - cart ?via - cell ?button - button ?door - door ?cart-pos - cell ?button-pos - cell ?door-pos - cell)
    :precondition (and
      (at ?cart ?cart-pos)
      (anchored ?button ?button-pos)
      (anchored ?door ?door-pos)
      (adjacent-up ?cart-pos ?via)
      (colour-7 ?via)
      (present ?door)
    )
    :effect (and
      (colour-8 ?button-pos)
      (not (colour-7 ?button-pos))
      (not (present ?door))
      (free ?door-pos)
    )
  )
  ;; rule door_opens_up shares this guard and is folded into press-up (cascade single_frame)

)
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
  )

  (:action push-up
    :parameters (?cart - cart ?up - object ?dest - cell ?cart-pos - cell)
    :precondition (and
      (at ?cart ?cart-pos)
      (adjacent-above ?cart-pos ?dest)
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
    :parameters (?cart - cart ?down - object ?dest - cell ?cart-pos - cell)
    :precondition (and
      (at ?cart ?cart-pos)
      (adjacent-below ?cart-pos ?dest)
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
    :parameters (?cart - cart ?left - object ?cart-pos - cell)
    :precondition (and
      (at ?cart ?cart-pos)
    )
    :effect (and
      (not (at ?cart ?cart-pos))
      (at ?cart ?dest)
      (not (free ?dest))
      (free ?cart-pos)
    )
  )

  (:action push-right
    :parameters (?cart - cart ?right - object ?cart-pos - cell)
    :precondition (and
      (at ?cart ?cart-pos)
    )
    :effect (and
      (not (at ?cart ?cart-pos))
      (at ?cart ?dest)
      (not (free ?dest))
      (free ?cart-pos)
    )
  )

  (:action teleport-down
    :parameters (?cart - cart ?down - object ?cart-pos - cell)
    :precondition (and
      (at ?cart ?cart-pos)
    )
    :effect (and
      (and)
    )
  )

  (:action press-left
    :parameters (?cart - cart ?left - object ?cart-pos - cell)
    :precondition (and
      (at ?cart ?cart-pos)
    )
    :effect (and
      (and)
    )
  )

  (:action door-opens-left
    :parameters (?cart - cart ?left - object ?cart-pos - cell)
    :precondition (and
      (at ?cart ?cart-pos)
    )
    :effect (and
      (and)
    )
  )

)
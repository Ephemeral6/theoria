(define (domain theoria-domain)
  (:requirements :strips :typing)

  (:types cell cart - object)
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

  (:action push
    :parameters (?cart - cart ?cart-pos - cell)
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

  (:action teleport
    :parameters (?cart - cart ?up - object ?cart-pos - cell ?origin - cell)
    :precondition (and
      (at ?cart ?cart-pos)
      (boundary-above ?cart-pos)
    )
    :effect (and
      (not (at ?cart ?cart-pos))
      (at ?cart ?origin)
      (not (free ?origin))
      (free ?cart-pos)
    )
  )

)
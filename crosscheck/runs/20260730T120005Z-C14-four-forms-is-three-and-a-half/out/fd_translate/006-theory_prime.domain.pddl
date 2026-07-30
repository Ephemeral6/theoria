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

  (:action switch-on-up
    :parameters (?cart - cart ?up - object ?cart-pos - cell)
    :precondition (and
      (at ?cart ?cart-pos)
    )
    :effect (and
      (and)
    )
  )

  (:action switch-on-down
    :parameters (?cart - cart ?down - object ?cart-pos - cell)
    :precondition (and
      (at ?cart ?cart-pos)
    )
    :effect (and
      (and)
    )
  )

  (:action switch-on-left
    :parameters (?cart - cart ?left - object ?cart-pos - cell)
    :precondition (and
      (at ?cart ?cart-pos)
    )
    :effect (and
      (and)
    )
  )

  (:action switch-on-right
    :parameters (?cart - cart ?right - object ?cart-pos - cell)
    :precondition (and
      (at ?cart ?cart-pos)
    )
    :effect (and
      (and)
    )
  )

  (:action door-opens-up
    :parameters (?cart - cart ?up - object ?cart-pos - cell)
    :precondition (and
      (at ?cart ?cart-pos)
    )
    :effect (and
      (and)
    )
  )

  (:action door-opens-down
    :parameters (?cart - cart ?down - object ?cart-pos - cell)
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

  (:action door-opens-right
    :parameters (?cart - cart ?right - object ?cart-pos - cell)
    :precondition (and
      (at ?cart ?cart-pos)
    )
    :effect (and
      (and)
    )
  )

  (:action switch-off-up
    :parameters (?cart - cart ?up - object ?cart-pos - cell)
    :precondition (and
      (at ?cart ?cart-pos)
    )
    :effect (and
      (and)
    )
  )

  (:action switch-off-down
    :parameters (?cart - cart ?down - object ?cart-pos - cell)
    :precondition (and
      (at ?cart ?cart-pos)
    )
    :effect (and
      (and)
    )
  )

  (:action switch-off-left
    :parameters (?cart - cart ?left - object ?cart-pos - cell)
    :precondition (and
      (at ?cart ?cart-pos)
    )
    :effect (and
      (and)
    )
  )

  (:action switch-off-right
    :parameters (?cart - cart ?right - object ?cart-pos - cell)
    :precondition (and
      (at ?cart ?cart-pos)
    )
    :effect (and
      (and)
    )
  )

  (:action door-shuts-up
    :parameters (?cart - cart ?up - object ?cart-pos - cell)
    :precondition (and
      (at ?cart ?cart-pos)
    )
    :effect (and
      (and)
    )
  )

  (:action door-shuts-down
    :parameters (?cart - cart ?down - object ?cart-pos - cell)
    :precondition (and
      (at ?cart ?cart-pos)
    )
    :effect (and
      (and)
    )
  )

  (:action door-shuts-left
    :parameters (?cart - cart ?left - object ?cart-pos - cell)
    :precondition (and
      (at ?cart ?cart-pos)
    )
    :effect (and
      (and)
    )
  )

  (:action door-shuts-right
    :parameters (?cart - cart ?right - object ?cart-pos - cell)
    :precondition (and
      (at ?cart ?cart-pos)
    )
    :effect (and
      (and)
    )
  )

)
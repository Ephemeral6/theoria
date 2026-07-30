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
  )

  (:action step-up
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

  (:action step-down
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

  (:action step-left
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

  (:action step-right
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

  (:action warp-a-up
    :parameters (?cart - cart ?up - object ?cart-pos - cell)
    :precondition (and
      (at ?cart ?cart-pos)
    )
    :effect (and
      (and)
    )
  )

  (:action warp-a-down
    :parameters (?cart - cart ?down - object ?cart-pos - cell)
    :precondition (and
      (at ?cart ?cart-pos)
    )
    :effect (and
      (and)
    )
  )

  (:action warp-a-left
    :parameters (?cart - cart ?left - object ?cart-pos - cell)
    :precondition (and
      (at ?cart ?cart-pos)
    )
    :effect (and
      (and)
    )
  )

  (:action warp-a-right
    :parameters (?cart - cart ?right - object ?cart-pos - cell)
    :precondition (and
      (at ?cart ?cart-pos)
    )
    :effect (and
      (and)
    )
  )

  (:action warp-b-up
    :parameters (?cart - cart ?up - object ?cart-pos - cell)
    :precondition (and
      (at ?cart ?cart-pos)
    )
    :effect (and
      (and)
    )
  )

  (:action warp-b-down
    :parameters (?cart - cart ?down - object ?cart-pos - cell)
    :precondition (and
      (at ?cart ?cart-pos)
    )
    :effect (and
      (and)
    )
  )

  (:action warp-b-left
    :parameters (?cart - cart ?left - object ?cart-pos - cell)
    :precondition (and
      (at ?cart ?cart-pos)
    )
    :effect (and
      (and)
    )
  )

  (:action warp-b-right
    :parameters (?cart - cart ?right - object ?cart-pos - cell)
    :precondition (and
      (at ?cart ?cart-pos)
    )
    :effect (and
      (and)
    )
  )

  (:action switch-press-up
    :parameters (?cart - cart ?up - object ?cart-pos - cell)
    :precondition (and
      (at ?cart ?cart-pos)
    )
    :effect (and
      (and)
    )
  )

  (:action switch-press-down
    :parameters (?cart - cart ?down - object ?cart-pos - cell)
    :precondition (and
      (at ?cart ?cart-pos)
    )
    :effect (and
      (and)
    )
  )

  (:action switch-press-left
    :parameters (?cart - cart ?left - object ?cart-pos - cell)
    :precondition (and
      (at ?cart ?cart-pos)
    )
    :effect (and
      (and)
    )
  )

  (:action switch-press-right
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

  (:action switch-release-up
    :parameters (?cart - cart ?up - object ?cart-pos - cell)
    :precondition (and
      (at ?cart ?cart-pos)
    )
    :effect (and
      (and)
    )
  )

  (:action switch-release-down
    :parameters (?cart - cart ?down - object ?cart-pos - cell)
    :precondition (and
      (at ?cart ?cart-pos)
    )
    :effect (and
      (and)
    )
  )

  (:action switch-release-left
    :parameters (?cart - cart ?left - object ?cart-pos - cell)
    :precondition (and
      (at ?cart ?cart-pos)
    )
    :effect (and
      (and)
    )
  )

  (:action switch-release-right
    :parameters (?cart - cart ?right - object ?cart-pos - cell)
    :precondition (and
      (at ?cart ?cart-pos)
    )
    :effect (and
      (and)
    )
  )

  (:action door-closes-up
    :parameters (?cart - cart ?up - object ?cart-pos - cell)
    :precondition (and
      (at ?cart ?cart-pos)
    )
    :effect (and
      (and)
    )
  )

  (:action door-closes-down
    :parameters (?cart - cart ?down - object ?cart-pos - cell)
    :precondition (and
      (at ?cart ?cart-pos)
    )
    :effect (and
      (and)
    )
  )

  (:action door-closes-left
    :parameters (?cart - cart ?left - object ?cart-pos - cell)
    :precondition (and
      (at ?cart ?cart-pos)
    )
    :effect (and
      (and)
    )
  )

  (:action door-closes-right
    :parameters (?cart - cart ?right - object ?cart-pos - cell)
    :precondition (and
      (at ?cart ?cart-pos)
    )
    :effect (and
      (and)
    )
  )

)
(define (domain theoria-domain)
  (:requirements :strips :typing)

  (:types cell cart block - object)
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

  (:action shove-up
    :parameters (?cart - cart ?up - object ?dest - cell ?cart-pos - cell)
    :precondition (and
      (at ?cart ?cart-pos)
      (adjacent-above ?block-pos ?dest)
      (free ?dest)
    )
    :effect (and
      (not (at ?cart ?cart-pos))
      (at ?cart ?dest)
      (not (free ?dest))
      (free ?cart-pos)
    )
  )

  (:action shove-down
    :parameters (?cart - cart ?down - object ?dest - cell ?cart-pos - cell)
    :precondition (and
      (at ?cart ?cart-pos)
      (adjacent-below ?block-pos ?dest)
      (free ?dest)
    )
    :effect (and
      (not (at ?cart ?cart-pos))
      (at ?cart ?dest)
      (not (free ?dest))
      (free ?cart-pos)
    )
  )

  (:action shove-left
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

  (:action shove-right
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

  (:action block-up
    :parameters (?cart - cart ?up - object ?dest - cell ?cart-pos - cell)
    :precondition (and
      (at ?cart ?cart-pos)
      (adjacent-above ?block-pos ?dest)
      (free ?dest)
    )
    :effect (and
      (not (at ?block ?block-pos))
      (at ?block ?dest)
      (not (free ?dest))
      (free ?block-pos)
    )
  )

  (:action block-down
    :parameters (?cart - cart ?down - object ?dest - cell ?cart-pos - cell)
    :precondition (and
      (at ?cart ?cart-pos)
      (adjacent-below ?block-pos ?dest)
      (free ?dest)
    )
    :effect (and
      (not (at ?block ?block-pos))
      (at ?block ?dest)
      (not (free ?dest))
      (free ?block-pos)
    )
  )

  (:action block-left
    :parameters (?cart - cart ?left - object ?cart-pos - cell)
    :precondition (and
      (at ?cart ?cart-pos)
    )
    :effect (and
      (not (at ?block ?block-pos))
      (at ?block ?dest)
      (not (free ?dest))
      (free ?block-pos)
    )
  )

  (:action block-right
    :parameters (?cart - cart ?right - object ?cart-pos - cell)
    :precondition (and
      (at ?cart ?cart-pos)
    )
    :effect (and
      (not (at ?block ?block-pos))
      (at ?block ?dest)
      (not (free ?dest))
      (free ?block-pos)
    )
  )

)
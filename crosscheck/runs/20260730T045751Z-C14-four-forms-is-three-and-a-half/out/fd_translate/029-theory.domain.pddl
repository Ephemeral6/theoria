(define (domain theoria-domain)
  (:requirements :strips :typing)

  (:types cell ring cursor pip locked spent done - object)
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

  (:action cursor-to-slot2
    :parameters ()
    :precondition (and
    )
    :effect (and
      (and)
    )
  )

  (:action ring-to-slot2
    :parameters ()
    :precondition (and
    )
    :effect (and
      (and)
    )
  )

  (:action locked-clears
    :parameters ()
    :precondition (and
    )
    :effect (and
      (and)
    )
  )

  (:action done-stamped
    :parameters ()
    :precondition (and
    )
    :effect (and
      (and)
    )
  )

  (:action budget-opens
    :parameters ()
    :precondition (and
    )
    :effect (and
      (and)
    )
  )

  (:action budget-advances
    :parameters ()
    :precondition (and
    )
    :effect (and
      (not (at ?spent ?spent-pos))
      (at ?spent ?dest)
      (not (free ?dest))
      (free ?spent-pos)
    )
  )

)
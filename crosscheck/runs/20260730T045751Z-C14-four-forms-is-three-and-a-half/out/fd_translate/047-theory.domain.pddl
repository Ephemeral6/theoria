(define (domain theoria-domain)
  (:requirements :strips :typing)

  (:types cell marker unused spent - object)
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

  (:action key5-advances-marker
    :parameters ()
    :precondition (and
    )
    :effect (and
      (and)
    )
  )

  (:action key5-marks-slot-a-spent
    :parameters ()
    :precondition (and
    )
    :effect (and
      (and)
    )
  )

  (:action key5-consumes-slot-b
    :parameters ()
    :precondition (and
    )
    :effect (and
      (and)
    )
  )

)
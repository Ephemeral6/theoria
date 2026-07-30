(define (domain theoria-domain)
  (:requirements :strips :typing)

  (:types cell peg - object)
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

  (:action jump-right
    :parameters (?right - object)
    :precondition (and
    )
    :effect (and
      (and)
    )
  )

  (:action jump-left
    :parameters (?left - object)
    :precondition (and
    )
    :effect (and
      (and)
    )
  )

)
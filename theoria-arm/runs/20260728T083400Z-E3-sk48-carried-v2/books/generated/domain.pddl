(define (domain theoria-domain)
  (:requirements :strips :typing)

  (:types cell casing cavity rail pip stud erased - object)
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

  (:action key3-blanks-the-strip-pips
    :parameters ()
    :precondition (and
    )
    :effect (and
      (and)
    )
  )

  (:action key3-blanks-the-strip-studs
    :parameters ()
    :precondition (and
    )
    :effect (and
      (and)
    )
  )

  (:action key7-blanks-the-strip-pips
    :parameters ()
    :precondition (and
    )
    :effect (and
      (and)
    )
  )

  (:action key7-blanks-the-strip-studs
    :parameters ()
    :precondition (and
    )
    :effect (and
      (and)
    )
  )

  (:action key4-restores-the-strip-pips
    :parameters ()
    :precondition (and
    )
    :effect (and
      (and)
    )
  )

  (:action key4-restores-the-strip-studs
    :parameters ()
    :precondition (and
    )
    :effect (and
      (and)
    )
  )

  (:action key4-advances-the-meter-once
    :parameters ()
    :precondition (and
    )
    :effect (and
      (and)
    )
  )

  (:action key3-marches-the-meter-leftward
    :parameters ()
    :precondition (and
    )
    :effect (and
      (and)
    )
  )

)

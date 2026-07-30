(define (domain theoria-domain)
  (:requirements :strips :typing)

  (:types cell player box - object)
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

  (:action walk
    :parameters (?player - player ?dir - object ?player-pos - cell)
    :precondition (and
      (at ?player ?player-pos)
    )
    :effect (and
      (not (at ?player ?player-pos))
      (at ?player ?dest)
      (not (free ?dest))
      (free ?player-pos)
    )
  )

  (:action push2
    :parameters (?player - player ?dir - object ?player-pos - cell)
    :precondition (and
      (at ?player ?player-pos)
    )
    :effect (and
      (and)
    )
  )

  (:action blocked-wall
    :parameters (?player - player ?dir - object ?player-pos - cell)
    :precondition (and
      (at ?player ?player-pos)
    )
    :effect (and
      (and)
    )
  )

  (:action blocked-box-crossing
    :parameters (?player - player ?dir - object ?player-pos - cell)
    :precondition (and
      (at ?player ?player-pos)
    )
    :effect (and
      (and)
    )
  )

  (:action blocked-box-landing
    :parameters (?player - player ?dir - object ?player-pos - cell)
    :precondition (and
      (at ?player ?player-pos)
    )
    :effect (and
      (and)
    )
  )

)
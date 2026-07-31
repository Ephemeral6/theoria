(define (domain theoria-domain)
  (:requirements :strips :typing)

  (:types cell agent gate switch - object)
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

  (:action step
    :parameters (?agent - agent ?agent-pos - cell)
    :precondition (and
      (at ?agent ?agent-pos)
    )
    :effect (and
      (not (at ?agent ?agent-pos))
      (at ?agent ?dest)
      (not (free ?dest))
      (free ?agent-pos)
    )
  )

  (:action warp-a
    :parameters (?agent - agent ?agent-pos - cell)
    :precondition (and
      (at ?agent ?agent-pos)
    )
    :effect (and
      (and)
    )
  )

  (:action warp-b
    :parameters (?agent - agent ?agent-pos - cell)
    :precondition (and
      (at ?agent ?agent-pos)
    )
    :effect (and
      (and)
    )
  )

  (:action switch-press
    :parameters (?agent - agent ?agent-pos - cell)
    :precondition (and
      (at ?agent ?agent-pos)
    )
    :effect (and
      (and)
    )
  )

  (:action gate-opens
    :parameters (?agent - agent ?agent-pos - cell)
    :precondition (and
      (at ?agent ?agent-pos)
    )
    :effect (and
      (and)
    )
  )

  (:action switch-release
    :parameters (?agent - agent ?agent-pos - cell)
    :precondition (and
      (at ?agent ?agent-pos)
    )
    :effect (and
      (and)
    )
  )

  (:action gate-closes
    :parameters (?agent - agent ?agent-pos - cell)
    :precondition (and
      (at ?agent ?agent-pos)
    )
    :effect (and
      (and)
    )
  )

)
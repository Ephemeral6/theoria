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

  (:action step-up
    :parameters (?agent - agent ?up - object ?dest - cell ?agent-pos - cell)
    :precondition (and
      (at ?agent ?agent-pos)
      (adjacent-above ?agent-pos ?dest)
      (free ?dest)
    )
    :effect (and
      (not (at ?agent ?agent-pos))
      (at ?agent ?dest)
      (not (free ?dest))
      (free ?agent-pos)
    )
  )

  (:action step-down
    :parameters (?agent - agent ?down - object ?dest - cell ?agent-pos - cell)
    :precondition (and
      (at ?agent ?agent-pos)
      (adjacent-below ?agent-pos ?dest)
      (free ?dest)
    )
    :effect (and
      (not (at ?agent ?agent-pos))
      (at ?agent ?dest)
      (not (free ?dest))
      (free ?agent-pos)
    )
  )

  (:action step-left
    :parameters (?agent - agent ?left - object ?agent-pos - cell)
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

  (:action step-right
    :parameters (?agent - agent ?right - object ?agent-pos - cell)
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

  (:action warp-a-up
    :parameters (?agent - agent ?up - object ?agent-pos - cell)
    :precondition (and
      (at ?agent ?agent-pos)
    )
    :effect (and
      (and)
    )
  )

  (:action warp-a-down
    :parameters (?agent - agent ?down - object ?agent-pos - cell)
    :precondition (and
      (at ?agent ?agent-pos)
    )
    :effect (and
      (and)
    )
  )

  (:action warp-a-left
    :parameters (?agent - agent ?left - object ?agent-pos - cell)
    :precondition (and
      (at ?agent ?agent-pos)
    )
    :effect (and
      (and)
    )
  )

  (:action warp-a-right
    :parameters (?agent - agent ?right - object ?agent-pos - cell)
    :precondition (and
      (at ?agent ?agent-pos)
    )
    :effect (and
      (and)
    )
  )

  (:action warp-b-up
    :parameters (?agent - agent ?up - object ?agent-pos - cell)
    :precondition (and
      (at ?agent ?agent-pos)
    )
    :effect (and
      (and)
    )
  )

  (:action warp-b-down
    :parameters (?agent - agent ?down - object ?agent-pos - cell)
    :precondition (and
      (at ?agent ?agent-pos)
    )
    :effect (and
      (and)
    )
  )

  (:action warp-b-left
    :parameters (?agent - agent ?left - object ?agent-pos - cell)
    :precondition (and
      (at ?agent ?agent-pos)
    )
    :effect (and
      (and)
    )
  )

  (:action warp-b-right
    :parameters (?agent - agent ?right - object ?agent-pos - cell)
    :precondition (and
      (at ?agent ?agent-pos)
    )
    :effect (and
      (and)
    )
  )

  (:action switch-press-up
    :parameters (?agent - agent ?up - object ?agent-pos - cell)
    :precondition (and
      (at ?agent ?agent-pos)
    )
    :effect (and
      (and)
    )
  )

  (:action switch-press-down
    :parameters (?agent - agent ?down - object ?agent-pos - cell)
    :precondition (and
      (at ?agent ?agent-pos)
    )
    :effect (and
      (and)
    )
  )

  (:action switch-press-left
    :parameters (?agent - agent ?left - object ?agent-pos - cell)
    :precondition (and
      (at ?agent ?agent-pos)
    )
    :effect (and
      (and)
    )
  )

  (:action switch-press-right
    :parameters (?agent - agent ?right - object ?agent-pos - cell)
    :precondition (and
      (at ?agent ?agent-pos)
    )
    :effect (and
      (and)
    )
  )

  (:action gate-opens-up
    :parameters (?agent - agent ?up - object ?agent-pos - cell)
    :precondition (and
      (at ?agent ?agent-pos)
    )
    :effect (and
      (and)
    )
  )

  (:action gate-opens-down
    :parameters (?agent - agent ?down - object ?agent-pos - cell)
    :precondition (and
      (at ?agent ?agent-pos)
    )
    :effect (and
      (and)
    )
  )

  (:action gate-opens-left
    :parameters (?agent - agent ?left - object ?agent-pos - cell)
    :precondition (and
      (at ?agent ?agent-pos)
    )
    :effect (and
      (and)
    )
  )

  (:action gate-opens-right
    :parameters (?agent - agent ?right - object ?agent-pos - cell)
    :precondition (and
      (at ?agent ?agent-pos)
    )
    :effect (and
      (and)
    )
  )

  (:action switch-release-up
    :parameters (?agent - agent ?up - object ?agent-pos - cell)
    :precondition (and
      (at ?agent ?agent-pos)
    )
    :effect (and
      (and)
    )
  )

  (:action switch-release-down
    :parameters (?agent - agent ?down - object ?agent-pos - cell)
    :precondition (and
      (at ?agent ?agent-pos)
    )
    :effect (and
      (and)
    )
  )

  (:action switch-release-left
    :parameters (?agent - agent ?left - object ?agent-pos - cell)
    :precondition (and
      (at ?agent ?agent-pos)
    )
    :effect (and
      (and)
    )
  )

  (:action switch-release-right
    :parameters (?agent - agent ?right - object ?agent-pos - cell)
    :precondition (and
      (at ?agent ?agent-pos)
    )
    :effect (and
      (and)
    )
  )

  (:action gate-closes-up
    :parameters (?agent - agent ?up - object ?agent-pos - cell)
    :precondition (and
      (at ?agent ?agent-pos)
    )
    :effect (and
      (and)
    )
  )

  (:action gate-closes-down
    :parameters (?agent - agent ?down - object ?agent-pos - cell)
    :precondition (and
      (at ?agent ?agent-pos)
    )
    :effect (and
      (and)
    )
  )

  (:action gate-closes-left
    :parameters (?agent - agent ?left - object ?agent-pos - cell)
    :precondition (and
      (at ?agent ?agent-pos)
    )
    :effect (and
      (and)
    )
  )

  (:action gate-closes-right
    :parameters (?agent - agent ?right - object ?agent-pos - cell)
    :precondition (and
      (at ?agent ?agent-pos)
    )
    :effect (and
      (and)
    )
  )

)
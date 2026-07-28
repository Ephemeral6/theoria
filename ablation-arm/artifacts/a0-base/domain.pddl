; Auto-generated from theory.dsl by compile/gen_pddl_a0.py — DO NOT EDIT.
(define (domain a0)
  (:requirements :strips :typing :negative-preconditions)
  (:types cell - object
          buttoncell doorcell markedcell - cell)

  (:predicates
    (at ?c - cell)                ; where the Cart is
    (passable ?c - cell)          ; the Cart may stand here
    (adj-up ?a - cell ?b - cell)
    (adj-down ?a - cell ?b - cell)
    (adj-left ?a - cell ?b - cell)
    (adj-right ?a - cell ?b - cell)
    (portal-exit ?c - cell)
    (switched)                    ; the Switch/Button state
  )

  (:action push-up
    :parameters (?from - cell ?to - cell)
    :precondition (and (at ?from) (adj-up ?from ?to) (passable ?to))
    :effect (and (not (at ?from)) (at ?to))
  )

  (:action push-down
    :parameters (?from - cell ?to - cell)
    :precondition (and (at ?from) (adj-down ?from ?to) (passable ?to))
    :effect (and (not (at ?from)) (at ?to))
  )

  (:action push-left
    :parameters (?from - cell ?to - cell)
    :precondition (and (at ?from) (adj-left ?from ?to) (passable ?to))
    :effect (and (not (at ?from)) (at ?to))
  )

  (:action push-right
    :parameters (?from - cell ?to - cell)
    :precondition (and (at ?from) (adj-right ?from ?to) (passable ?to))
    :effect (and (not (at ?from)) (at ?to))
  )

  (:action teleport-down
    :parameters (?from - cell ?p - markedcell ?dest - cell)
    :precondition (and (at ?from) (adj-down ?from ?p) (portal-exit ?dest))
    :effect (and (not (at ?from)) (at ?dest))
  )

  (:action press-left
    :parameters (?from - cell ?s - buttoncell ?d - doorcell)
    :precondition (and (at ?from) (adj-left ?from ?s) (not (switched)))
    :effect (and (switched) (passable ?d))
  )

;; door_opens_left is a cascade of the toggle action with the same guard — its effect is folded in there

)

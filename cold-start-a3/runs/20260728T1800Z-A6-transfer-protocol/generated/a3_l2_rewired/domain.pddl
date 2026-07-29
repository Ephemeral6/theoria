; Auto-generated from theory.dsl by compile/gen_pddl_a0.py — DO NOT EDIT.
(define (domain a0)
  (:requirements :strips :typing :negative-preconditions)
  (:types cell - object
          doorcell markedcell switchcell - cell)

  (:predicates
    (at ?c - cell)                ; where the Cart is
    (passable ?c - cell)          ; the Cart may stand here
    (adj-up ?a - cell ?b - cell)
    (adj-down ?a - cell ?b - cell)
    (adj-left ?a - cell ?b - cell)
    (adj-right ?a - cell ?b - cell)
    (exit-exit-a ?c - cell)
    (entry-exit-a ?c - cell)
    (exit-exit-b ?c - cell)
    (entry-exit-b ?c - cell)
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

  (:action teleport-a-up
    :parameters (?from - cell ?p - markedcell ?dest - cell)
    :precondition (and (at ?from) (adj-up ?from ?p) (entry-exit-a ?p) (exit-exit-a ?dest))
    :effect (and (not (at ?from)) (at ?dest))
  )

  (:action teleport-a-down
    :parameters (?from - cell ?p - markedcell ?dest - cell)
    :precondition (and (at ?from) (adj-down ?from ?p) (entry-exit-a ?p) (exit-exit-a ?dest))
    :effect (and (not (at ?from)) (at ?dest))
  )

  (:action teleport-a-left
    :parameters (?from - cell ?p - markedcell ?dest - cell)
    :precondition (and (at ?from) (adj-left ?from ?p) (entry-exit-a ?p) (exit-exit-a ?dest))
    :effect (and (not (at ?from)) (at ?dest))
  )

  (:action teleport-a-right
    :parameters (?from - cell ?p - markedcell ?dest - cell)
    :precondition (and (at ?from) (adj-right ?from ?p) (entry-exit-a ?p) (exit-exit-a ?dest))
    :effect (and (not (at ?from)) (at ?dest))
  )

  (:action teleport-b-up
    :parameters (?from - cell ?p - markedcell ?dest - cell)
    :precondition (and (at ?from) (adj-up ?from ?p) (entry-exit-b ?p) (exit-exit-b ?dest))
    :effect (and (not (at ?from)) (at ?dest))
  )

  (:action teleport-b-down
    :parameters (?from - cell ?p - markedcell ?dest - cell)
    :precondition (and (at ?from) (adj-down ?from ?p) (entry-exit-b ?p) (exit-exit-b ?dest))
    :effect (and (not (at ?from)) (at ?dest))
  )

  (:action teleport-b-left
    :parameters (?from - cell ?p - markedcell ?dest - cell)
    :precondition (and (at ?from) (adj-left ?from ?p) (entry-exit-b ?p) (exit-exit-b ?dest))
    :effect (and (not (at ?from)) (at ?dest))
  )

  (:action teleport-b-right
    :parameters (?from - cell ?p - markedcell ?dest - cell)
    :precondition (and (at ?from) (adj-right ?from ?p) (entry-exit-b ?p) (exit-exit-b ?dest))
    :effect (and (not (at ?from)) (at ?dest))
  )

  (:action press-up
    :parameters (?from - cell ?s - switchcell ?d - doorcell)
    :precondition (and (at ?from) (adj-up ?from ?s) (not (switched)))
    :effect (and (switched) (passable ?d))
  )

;; door_opens_up is a cascade of the toggle action with the same guard — its effect is folded in there

  (:action press-down
    :parameters (?from - cell ?s - switchcell ?d - doorcell)
    :precondition (and (at ?from) (adj-down ?from ?s) (not (switched)))
    :effect (and (switched) (passable ?d))
  )

;; door_opens_down is a cascade of the toggle action with the same guard — its effect is folded in there

  (:action unpress-up
    :parameters (?from - cell ?s - switchcell ?d - doorcell)
    :precondition (and (at ?from) (adj-up ?from ?s) (switched))
    :effect (and (not (switched)) (not (passable ?d)))
  )

;; door_closes_up is a cascade of the toggle action with the same guard — its effect is folded in there

  (:action unpress-down
    :parameters (?from - cell ?s - switchcell ?d - doorcell)
    :precondition (and (at ?from) (adj-down ?from ?s) (switched))
    :effect (and (not (switched)) (not (passable ?d)))
  )

;; door_closes_down is a cascade of the toggle action with the same guard — its effect is folded in there

)

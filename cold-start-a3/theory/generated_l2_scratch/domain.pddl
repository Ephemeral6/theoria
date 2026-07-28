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

  (:action step-up
    :parameters (?from - cell ?to - cell)
    :precondition (and (at ?from) (adj-up ?from ?to) (passable ?to))
    :effect (and (not (at ?from)) (at ?to))
  )

  (:action step-down
    :parameters (?from - cell ?to - cell)
    :precondition (and (at ?from) (adj-down ?from ?to) (passable ?to))
    :effect (and (not (at ?from)) (at ?to))
  )

  (:action step-left
    :parameters (?from - cell ?to - cell)
    :precondition (and (at ?from) (adj-left ?from ?to) (passable ?to))
    :effect (and (not (at ?from)) (at ?to))
  )

  (:action step-right
    :parameters (?from - cell ?to - cell)
    :precondition (and (at ?from) (adj-right ?from ?to) (passable ?to))
    :effect (and (not (at ?from)) (at ?to))
  )

  (:action warp-a-up
    :parameters (?from - cell ?p - markedcell ?dest - cell)
    :precondition (and (at ?from) (adj-up ?from ?p) (entry-exit-a ?p) (exit-exit-a ?dest))
    :effect (and (not (at ?from)) (at ?dest))
  )

  (:action warp-a-down
    :parameters (?from - cell ?p - markedcell ?dest - cell)
    :precondition (and (at ?from) (adj-down ?from ?p) (entry-exit-a ?p) (exit-exit-a ?dest))
    :effect (and (not (at ?from)) (at ?dest))
  )

  (:action warp-a-left
    :parameters (?from - cell ?p - markedcell ?dest - cell)
    :precondition (and (at ?from) (adj-left ?from ?p) (entry-exit-a ?p) (exit-exit-a ?dest))
    :effect (and (not (at ?from)) (at ?dest))
  )

  (:action warp-a-right
    :parameters (?from - cell ?p - markedcell ?dest - cell)
    :precondition (and (at ?from) (adj-right ?from ?p) (entry-exit-a ?p) (exit-exit-a ?dest))
    :effect (and (not (at ?from)) (at ?dest))
  )

  (:action warp-b-up
    :parameters (?from - cell ?p - markedcell ?dest - cell)
    :precondition (and (at ?from) (adj-up ?from ?p) (entry-exit-b ?p) (exit-exit-b ?dest))
    :effect (and (not (at ?from)) (at ?dest))
  )

  (:action warp-b-down
    :parameters (?from - cell ?p - markedcell ?dest - cell)
    :precondition (and (at ?from) (adj-down ?from ?p) (entry-exit-b ?p) (exit-exit-b ?dest))
    :effect (and (not (at ?from)) (at ?dest))
  )

  (:action warp-b-left
    :parameters (?from - cell ?p - markedcell ?dest - cell)
    :precondition (and (at ?from) (adj-left ?from ?p) (entry-exit-b ?p) (exit-exit-b ?dest))
    :effect (and (not (at ?from)) (at ?dest))
  )

  (:action warp-b-right
    :parameters (?from - cell ?p - markedcell ?dest - cell)
    :precondition (and (at ?from) (adj-right ?from ?p) (entry-exit-b ?p) (exit-exit-b ?dest))
    :effect (and (not (at ?from)) (at ?dest))
  )

  (:action switch-press-up
    :parameters (?from - cell ?s - switchcell ?d - doorcell)
    :precondition (and (at ?from) (adj-up ?from ?s) (not (switched)))
    :effect (and (switched) (passable ?d))
  )

  (:action switch-press-down
    :parameters (?from - cell ?s - switchcell ?d - doorcell)
    :precondition (and (at ?from) (adj-down ?from ?s) (not (switched)))
    :effect (and (switched) (passable ?d))
  )

  (:action switch-press-left
    :parameters (?from - cell ?s - switchcell ?d - doorcell)
    :precondition (and (at ?from) (adj-left ?from ?s) (not (switched)))
    :effect (and (switched) (passable ?d))
  )

  (:action switch-press-right
    :parameters (?from - cell ?s - switchcell ?d - doorcell)
    :precondition (and (at ?from) (adj-right ?from ?s) (not (switched)))
    :effect (and (switched) (passable ?d))
  )

;; door_opens_up is a cascade of the toggle action with the same guard — its effect is folded in there

;; door_opens_down is a cascade of the toggle action with the same guard — its effect is folded in there

;; door_opens_left is a cascade of the toggle action with the same guard — its effect is folded in there

;; door_opens_right is a cascade of the toggle action with the same guard — its effect is folded in there

  (:action switch-release-up
    :parameters (?from - cell ?s - switchcell ?d - doorcell)
    :precondition (and (at ?from) (adj-up ?from ?s) (switched))
    :effect (and (not (switched)) (not (passable ?d)))
  )

  (:action switch-release-down
    :parameters (?from - cell ?s - switchcell ?d - doorcell)
    :precondition (and (at ?from) (adj-down ?from ?s) (switched))
    :effect (and (not (switched)) (not (passable ?d)))
  )

  (:action switch-release-left
    :parameters (?from - cell ?s - switchcell ?d - doorcell)
    :precondition (and (at ?from) (adj-left ?from ?s) (switched))
    :effect (and (not (switched)) (not (passable ?d)))
  )

  (:action switch-release-right
    :parameters (?from - cell ?s - switchcell ?d - doorcell)
    :precondition (and (at ?from) (adj-right ?from ?s) (switched))
    :effect (and (not (switched)) (not (passable ?d)))
  )

;; door_closes_up is a cascade of the toggle action with the same guard — its effect is folded in there

;; door_closes_down is a cascade of the toggle action with the same guard — its effect is folded in there

;; door_closes_left is a cascade of the toggle action with the same guard — its effect is folded in there

;; door_closes_right is a cascade of the toggle action with the same guard — its effect is folded in there

)

; Auto-generated from theory.dsl by compile/gen_pddl_a0.py — DO NOT EDIT.
(define (domain a0)
  (:requirements :strips :typing :negative-preconditions)
  (:types cell - object)

  (:predicates
    (at ?c - cell)                ; where the Cart is
    (passable ?c - cell)          ; the Cart may stand here
    (adj-up ?a - cell ?b - cell)
    (adj-down ?a - cell ?b - cell)
    (adj-left ?a - cell ?b - cell)
    (adj-right ?a - cell ?b - cell)
    (portal-exit ?c - cell)
    (switched)                    ; the Switch/Button state
    (block-at ?c - cell)          ; where Block is
  )

  (:action step-up
    :parameters (?from - cell ?to - cell)
    :precondition (and (at ?from) (adj-up ?from ?to) (passable ?to) (not (block-at ?to)))
    :effect (and (not (at ?from)) (at ?to))
  )

  (:action step-down
    :parameters (?from - cell ?to - cell)
    :precondition (and (at ?from) (adj-down ?from ?to) (passable ?to) (not (block-at ?to)))
    :effect (and (not (at ?from)) (at ?to))
  )

  (:action step-left
    :parameters (?from - cell ?to - cell)
    :precondition (and (at ?from) (adj-left ?from ?to) (passable ?to) (not (block-at ?to)))
    :effect (and (not (at ?from)) (at ?to))
  )

  (:action step-right
    :parameters (?from - cell ?to - cell)
    :precondition (and (at ?from) (adj-right ?from ?to) (passable ?to) (not (block-at ?to)))
    :effect (and (not (at ?from)) (at ?to))
  )

  (:action shove-up
    :parameters (?from - cell ?p - cell ?beyond - cell)
    :precondition (and (at ?from) (adj-up ?from ?p) (block-at ?p)
                       (adj-up ?p ?beyond) (passable ?p) (passable ?beyond) (not (block-at ?beyond)))
    :effect (and (not (at ?from)) (at ?p)
                 (not (block-at ?p)) (block-at ?beyond))
  )

  (:action shove-down
    :parameters (?from - cell ?p - cell ?beyond - cell)
    :precondition (and (at ?from) (adj-down ?from ?p) (block-at ?p)
                       (adj-down ?p ?beyond) (passable ?p) (passable ?beyond) (not (block-at ?beyond)))
    :effect (and (not (at ?from)) (at ?p)
                 (not (block-at ?p)) (block-at ?beyond))
  )

  (:action shove-left
    :parameters (?from - cell ?p - cell ?beyond - cell)
    :precondition (and (at ?from) (adj-left ?from ?p) (block-at ?p)
                       (adj-left ?p ?beyond) (passable ?p) (passable ?beyond) (not (block-at ?beyond)))
    :effect (and (not (at ?from)) (at ?p)
                 (not (block-at ?p)) (block-at ?beyond))
  )

  (:action shove-right
    :parameters (?from - cell ?p - cell ?beyond - cell)
    :precondition (and (at ?from) (adj-right ?from ?p) (block-at ?p)
                       (adj-right ?p ?beyond) (passable ?p) (passable ?beyond) (not (block-at ?beyond)))
    :effect (and (not (at ?from)) (at ?p)
                 (not (block-at ?p)) (block-at ?beyond))
  )

;; block-up was a duplicate mover move — its object is carried by the block-at action's effect instead (D-A6-001)

;; block-down was a duplicate mover move — its object is carried by the block-at action's effect instead (D-A6-001)

;; block-left was a duplicate mover move — its object is carried by the block-at action's effect instead (D-A6-001)

;; block-right was a duplicate mover move — its object is carried by the block-at action's effect instead (D-A6-001)

)

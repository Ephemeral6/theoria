;; Sokoban, re-encoded with `occupied` and a negative precondition.
;; Written by attacks/noclear.py for the E7 adversarial review -- not a fixture.
;;
;; `occupied ?c` is the exact complement of the committed domain's `clear ?c`,
;; so the grounded transition relation is isomorphic to it: the same states, the
;; same actions, the same plans.  What differs is only where the "free cell"
;; requirement sits -- in a negative precondition rather than a positive one.
(define (domain sokoban-nc)
  (:requirements :strips :typing :negative-preconditions)
  (:types cell box dir)
  (:predicates
    (at-player ?c - cell)
    (at ?b - box ?c - cell)
    (occupied ?c - cell)
    (adj ?from - cell ?to - cell ?d - dir))

  (:action move
    :parameters (?from - cell ?to - cell ?d - dir)
    :precondition (and (at-player ?from) (not (occupied ?to)) (adj ?from ?to ?d))
    :effect (and (at-player ?to) (not (at-player ?from))
                 (occupied ?to) (not (occupied ?from))))

  (:action push
    :parameters (?p - cell ?from - cell ?to - cell ?b - box ?d - dir)
    :precondition (and (at-player ?p) (at ?b ?from) (not (occupied ?to))
                       (adj ?p ?from ?d) (adj ?from ?to ?d))
    :effect (and (at-player ?from) (not (at-player ?p)) (not (occupied ?p))
                 (at ?b ?to) (not (at ?b ?from))
                 (occupied ?to) (occupied ?from))))

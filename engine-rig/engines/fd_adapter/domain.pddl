;; Minimal gripper domain -- the classic, cut down to what the STRIPS subset needs.
;; Independent of every fixture in this rig: the planner adapter is tested on its
;; own instance, not on the Cart / Pair-Flip / peg worlds.
(define (domain gripper)
  (:requirements :strips :typing)
  (:types room ball gripper)
  (:predicates
    (at-robby ?r - room)
    (at ?b - ball ?r - room)
    (free ?g - gripper)
    (carry ?b - ball ?g - gripper))

  (:action move
    :parameters (?from - room ?to - room)
    :precondition (at-robby ?from)
    :effect (and (at-robby ?to) (not (at-robby ?from))))

  (:action pick
    :parameters (?b - ball ?r - room ?g - gripper)
    :precondition (and (at ?b ?r) (at-robby ?r) (free ?g))
    :effect (and (carry ?b ?g) (not (at ?b ?r)) (not (free ?g))))

  (:action drop
    :parameters (?b - ball ?r - room ?g - gripper)
    :precondition (and (carry ?b ?g) (at-robby ?r))
    :effect (and (at ?b ?r) (free ?g) (not (carry ?b ?g)))))

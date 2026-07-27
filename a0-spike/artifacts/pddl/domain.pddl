;; A0 sokoban-2: a push slides the box two cells.
;; Transcribed from the mined rules; see pipeline/stages.py for their provenance.
(define (domain sokoban2)
  (:requirements :strips :typing :negative-preconditions)
  (:types cell dir)
  (:predicates
    (player-at ?c - cell)
    (box-at ?c - cell)
    (wall ?c - cell)
    (adj ?from - cell ?to - cell ?d - dir))

  ;; walk: act==D and ahead_free(D)
  (:action walk
    :parameters (?from - cell ?to - cell ?d - dir)
    :precondition (and (player-at ?from) (adj ?from ?to ?d)
                       (not (wall ?to)) (not (box-at ?to)))
    :effect (and (player-at ?to) (not (player-at ?from))))

  ;; push2: act==D and ahead_is_box(D) and box_beyond_free(D)
  ;; the box crosses ?over and lands on ?land; the player takes its old cell
  (:action push2
    :parameters (?p - cell ?b - cell ?over - cell ?land - cell ?d - dir)
    :precondition (and (player-at ?p) (adj ?p ?b ?d) (box-at ?b)
                       (adj ?b ?over ?d) (adj ?over ?land ?d)
                       (not (wall ?over)) (not (wall ?land)))
    :effect (and (box-at ?land) (not (box-at ?b))
                 (player-at ?b) (not (player-at ?p)))))

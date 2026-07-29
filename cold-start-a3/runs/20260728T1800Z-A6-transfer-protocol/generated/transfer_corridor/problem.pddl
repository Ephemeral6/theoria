; Auto-generated from theory.dsl + the derived problem instance.
(define (problem t1-push-corridor)
  (:domain a0)

  (:objects
    c1-1 c1-2 c1-3 c1-4 c2-1 c3-1 c3-2 c3-3 c3-4 - cell
  )

  (:init
    (adj-down c1-1 c2-1)
    (adj-right c1-1 c1-2)
    (adj-left c1-2 c1-1)
    (adj-right c1-2 c1-3)
    (adj-left c1-3 c1-2)
    (adj-right c1-3 c1-4)
    (adj-left c1-4 c1-3)
    (adj-down c2-1 c3-1)
    (adj-up c2-1 c1-1)
    (adj-right c3-1 c3-2)
    (adj-up c3-1 c2-1)
    (adj-left c3-2 c3-1)
    (adj-right c3-2 c3-3)
    (adj-left c3-3 c3-2)
    (adj-right c3-3 c3-4)
    (adj-left c3-4 c3-3)
    (at c1-1)
    (passable c1-1)
    (passable c1-2)
    (passable c1-3)
    (passable c1-4)
    (passable c2-1)
    (passable c3-1)
    (passable c3-2)
    (passable c3-3)
    (passable c3-4)
    (block-at c1-3)
  )

  (:goal
    (at c3-4)
  )
)

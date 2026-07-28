(define (problem instance-1)
  (:domain theoria-domain)

  (:objects
    cell-0-0 cell-0-1 cell-1-0 cell-1-1 cell-2-0 cell-2-1 - cell
    marker1 - marker
    unused1 - unused
    spent1 - spent
  )

  (:init
    (boundary-up cell-0-0)
    (adjacent-down cell-0-0 cell-1-0)
    (boundary-left cell-0-0)
    (adjacent-right cell-0-0 cell-0-1)
    (boundary-up cell-0-1)
    (adjacent-down cell-0-1 cell-1-1)
    (adjacent-left cell-0-1 cell-0-0)
    (boundary-right cell-0-1)
    (adjacent-up cell-1-0 cell-0-0)
    (adjacent-down cell-1-0 cell-2-0)
    (boundary-left cell-1-0)
    (adjacent-right cell-1-0 cell-1-1)
    (adjacent-up cell-1-1 cell-0-1)
    (adjacent-down cell-1-1 cell-2-1)
    (adjacent-left cell-1-1 cell-1-0)
    (boundary-right cell-1-1)
    (adjacent-up cell-2-0 cell-1-0)
    (boundary-down cell-2-0)
    (boundary-left cell-2-0)
    (adjacent-right cell-2-0 cell-2-1)
    (adjacent-up cell-2-1 cell-1-1)
    (boundary-down cell-2-1)
    (adjacent-left cell-2-1 cell-2-0)
    (boundary-right cell-2-1)
    (at marker1 cell-0-0)
    (at unused1 cell-0-0)
    (at spent1 cell-0-0)
    (free cell-0-1)
    (free cell-1-0)
    (free cell-1-1)
    (free cell-2-0)
    (free cell-2-1)
  )

  (:goal
    (and)
  )
)

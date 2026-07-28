;; Unsolvable variant of the repo's gripper instance, written for this run only.
;; The repo's own engines/fd_adapter/problem.pddl is NOT modified.
;;
;; Why this is genuinely unreachable: the goal demands ball1 be in both rooms at
;; once. `drop` adds (at ?b ?r) without deleting (at ?b ?other), but `pick`
;; deletes (at ?b ?r), so a ball must leave its room before it can be carried
;; anywhere. No reachable state satisfies both goal atoms.
(define (problem gripper-two-balls-unsat)
  (:domain gripper)
  (:objects
    rooma roomb - room
    ball1 ball2 - ball
    left right - gripper)
  (:init
    (at-robby rooma)
    (free left)
    (free right)
    (at ball1 rooma)
    (at ball2 rooma))
  (:goal (and (at ball1 rooma) (at ball1 roomb))))

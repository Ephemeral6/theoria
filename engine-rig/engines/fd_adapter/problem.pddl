;; Two balls, two grippers, two rooms; move both balls from rooma to roomb.
;; Hand-verified optimum: 5 actions. Each ball needs one pick and one drop (4),
;; and at least one move is needed since both balls start in the wrong room (1);
;; 5 is therefore a lower bound, and pick/pick/move/drop/drop attains it.
(define (problem gripper-two-balls)
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
  (:goal (and (at ball1 roomb) (at ball2 roomb))))

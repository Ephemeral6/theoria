(define (domain theoria-domain)
  (:requirements :strips :typing)

  (:types cell cart block - object)
    ; direction is implicit in action names

  (:predicates
    (at ?o - object ?c - cell)
    (free ?c - cell)
    (adjacent-up ?c1 - cell ?c2 - cell)
    (adjacent-down ?c1 - cell ?c2 - cell)
    (adjacent-left ?c1 - cell ?c2 - cell)
    (adjacent-right ?c1 - cell ?c2 - cell)
    (boundary-up ?c - cell)
    (boundary-down ?c - cell)
    (boundary-left ?c - cell)
    (boundary-right ?c - cell)
    (colour-2 ?c - cell)
  )

  (:action step-up
    :parameters (?cart - cart ?dest - cell ?cart-pos - cell)
    :precondition (and
      (at ?cart ?cart-pos)
      (adjacent-up ?cart-pos ?dest)
      (free ?dest)
    )
    :effect (and
      (not (at ?cart ?cart-pos))
      (at ?cart ?dest)
      (not (free ?dest))
      (free ?cart-pos)
    )
  )

  (:action step-down
    :parameters (?cart - cart ?dest - cell ?cart-pos - cell)
    :precondition (and
      (at ?cart ?cart-pos)
      (adjacent-down ?cart-pos ?dest)
      (free ?dest)
    )
    :effect (and
      (not (at ?cart ?cart-pos))
      (at ?cart ?dest)
      (not (free ?dest))
      (free ?cart-pos)
    )
  )

  (:action step-left
    :parameters (?cart - cart ?dest - cell ?cart-pos - cell)
    :precondition (and
      (at ?cart ?cart-pos)
      (adjacent-left ?cart-pos ?dest)
      (free ?dest)
    )
    :effect (and
      (not (at ?cart ?cart-pos))
      (at ?cart ?dest)
      (not (free ?dest))
      (free ?cart-pos)
    )
  )

  (:action step-right
    :parameters (?cart - cart ?dest - cell ?cart-pos - cell)
    :precondition (and
      (at ?cart ?cart-pos)
      (adjacent-right ?cart-pos ?dest)
      (free ?dest)
    )
    :effect (and
      (not (at ?cart ?cart-pos))
      (at ?cart ?dest)
      (not (free ?dest))
      (free ?cart-pos)
    )
  )

  (:action shove-up
    :parameters (?cart - cart ?via - cell ?block - block ?dest - cell ?cart-pos - cell ?block-pos - cell)
    :precondition (and
      (at ?cart ?cart-pos)
      (at ?block ?block-pos)
      (adjacent-up ?cart-pos ?via)
      (colour-2 ?via)
      (adjacent-up ?block-pos ?dest)
      (free ?dest)
      (adjacent-up ?cart-pos ?dest)
    )
    :effect (and
      (not (at ?cart ?cart-pos))
      (at ?cart ?dest)
      (not (free ?dest))
      (free ?cart-pos)
      (not (at ?block ?block-pos))
      (at ?block ?dest)
      (free ?block-pos)
    )
  )
  ;; rule block_up shares this guard and is folded into shove-up (cascade single_frame)

  (:action shove-down
    :parameters (?cart - cart ?via - cell ?block - block ?dest - cell ?cart-pos - cell ?block-pos - cell)
    :precondition (and
      (at ?cart ?cart-pos)
      (at ?block ?block-pos)
      (adjacent-down ?cart-pos ?via)
      (colour-2 ?via)
      (adjacent-down ?block-pos ?dest)
      (free ?dest)
      (adjacent-down ?cart-pos ?dest)
    )
    :effect (and
      (not (at ?cart ?cart-pos))
      (at ?cart ?dest)
      (not (free ?dest))
      (free ?cart-pos)
      (not (at ?block ?block-pos))
      (at ?block ?dest)
      (free ?block-pos)
    )
  )
  ;; rule block_down shares this guard and is folded into shove-down (cascade single_frame)

  (:action shove-left
    :parameters (?cart - cart ?via - cell ?block - block ?dest - cell ?cart-pos - cell ?block-pos - cell)
    :precondition (and
      (at ?cart ?cart-pos)
      (at ?block ?block-pos)
      (adjacent-left ?cart-pos ?via)
      (colour-2 ?via)
      (adjacent-left ?block-pos ?dest)
      (free ?dest)
      (adjacent-left ?cart-pos ?dest)
    )
    :effect (and
      (not (at ?cart ?cart-pos))
      (at ?cart ?dest)
      (not (free ?dest))
      (free ?cart-pos)
      (not (at ?block ?block-pos))
      (at ?block ?dest)
      (free ?block-pos)
    )
  )
  ;; rule block_left shares this guard and is folded into shove-left (cascade single_frame)

  (:action shove-right
    :parameters (?cart - cart ?via - cell ?block - block ?dest - cell ?cart-pos - cell ?block-pos - cell)
    :precondition (and
      (at ?cart ?cart-pos)
      (at ?block ?block-pos)
      (adjacent-right ?cart-pos ?via)
      (colour-2 ?via)
      (adjacent-right ?block-pos ?dest)
      (free ?dest)
      (adjacent-right ?cart-pos ?dest)
    )
    :effect (and
      (not (at ?cart ?cart-pos))
      (at ?cart ?dest)
      (not (free ?dest))
      (free ?cart-pos)
      (not (at ?block ?block-pos))
      (at ?block ?dest)
      (free ?block-pos)
    )
  )
  ;; rule block_right shares this guard and is folded into shove-right (cascade single_frame)

)
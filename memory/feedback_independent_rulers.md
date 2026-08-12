---
name: feedback_independent_rulers
description: Agreement between numbers derived from the same source is not corroboration — check what each ruler is derived FROM before treating it as confirmation.
metadata: 
  node_type: memory
  type: feedback
  originSessionId: 347b8172-f77b-4498-bf13-b36574a11eed
  modified: 2026-08-12T19:28:08.654Z
---

**Before quoting agreement between measurements as corroboration, ask what each one is DERIVED from.**
Numbers that share an upstream source will agree while being wrong together, and that agreement feels
exactly like confirmation.

**Why:** On 2026-08-12/13, diagnosing why the rover ran 2.8× its commanded speed, I had three numbers
agreeing closely: `/odom` velocity, PX4's EKF feedback, and the throttle the speed controller settled
on. I read that as strong corroboration. All three are derived from **wheel ERPM** — `rover-ekf-bridge`
feeds the EKF *from* `/odom` — so they were one measurement wearing three hats, and all three carried
the same ~21% under-read. The tie was broken only by the bumper (`/scan` closing range on a wall),
which measures the room instead of the wheels. The same night I nearly recorded a drivetrain
stick-slip fault that did not exist, because `/odom` velocity swung with CoV 0.30 at crawl while the
independent ruler showed the rover moving smoothly.

**How to apply:**
* Before concluding, name the physical chain behind each number. Two numbers sharing any link are ONE
  witness, no matter how many topics they arrive on.
* A conclusion that rests on a single ruler is provisional until something with a different physical
  basis agrees. On this vehicle: wheels (`/odom`, ESC ERPM) · the room (`/scan` clearance, taped
  distance) · the operator's tape. **The operator's tape is the only one with no software in it.**
* When the operator offers to measure something physically, take it. Two of my wrong turns on 08-13
  were caught that way and neither would have surfaced from the logs.
* **Ask what the measurement actually requires before asking for more of it.** I asked the operator to
  tape the wheel circumference for a calibration that never needed it — `erpm_to_ms` is
  `tape ÷ ERPM-seconds`, and the revolution count cancels. They pushed back and were right.

Related: [[feedback_test_before_concluding]] · [[feedback_verify_after_editing]] ·
[[feedback_check_docs_before_measuring]] · [[project_rover_autonav]]

# E9 normal-alert visual review

All 24 contact sheets were actually viewed on 8 October 2026. All 209 normal-image review alerts have individual observations in six ordered batches. Ground truth is the frozen dataset label; these observations do not establish an expert diagnosis or the cause of a false alarm.

Repeated visible predictions occupy distal radius/wrist, distal tibia/ankle, distal femur/knee, elbow, and bone-shaft projections. Other alerts occupy projected ribs/chest or pelvic/proximal femoral structures. IMG0002185 has a red patch on an internal white divider; IMG0002702 and IMG0002271 include crop-edge/truncated-shaft alerts. Hardware or radiopaque rings are visible in some images, without proving causation.

Very small masks remain anatomically unresolved where indicated in the case notes. Full retained panels for IMG0000241, IMG0000244, IMG0000428 and IMG0002185 were additionally viewed at original panel resolution. The first two still do not visibly resolve their tiny masks; audit metadata reports 102 and 42 native pixels respectively. IMG0000428 resolves a tiny lateral proximal-femoral/trochanteric mark (5 native pixels). IMG0002185 confirms the divider patch (139 native pixels, maximum-pixel score 0.968775). This score is an uncalibrated pixel maximum, not a clinical probability.

Audit: `experiments/AI_AUDIT_E9_v3_hard_reference`, selected additional epoch9/global27, CUDA full frozen VAL463. No additional inference, label changes, calibration fitting, reserved-test reads or production changes were performed for this visual review. E10 continues under the separately frozen matched training protocol. No next intervention is selected from the reference arm alone.

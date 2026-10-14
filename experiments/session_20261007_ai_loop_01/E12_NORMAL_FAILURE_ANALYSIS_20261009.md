# E12 normal-alert visual failure analysis

Actual review and memo completed on 9 October 2026.

All 17 original-resolution JPG contact sheets were actually viewed. Each original X-ray and independent red mask pair has an ordered individual observation, saved through the existing review recorder. Completion verifies 151 unique normal-reference image IDs, 151 independent-mask false positives, exact selected-case coverage and the linked native-panel/source hashes. No prior views or notes were reused as an E12 review. The normal-alert subset contains 156,358 false-positive mask pixels; this excludes positive-case errors and is not the full validation set's false-positive pixel total.

The source is the completed `AI_AUDIT_E12_v3_positive_Dice2` native validation audit, selected epoch 3 / global epoch 33, checkpoint `c93ca3b3143cf3a096c72905f211d24ca8bd93fa871c93c15fbd4ce774c4904c`. Its complete 463-case audit records TP 64, FN 19, TN 229 and FP 151. Inference used the registered 256-pixel stretched input, CLAHE and blur, threshold 0.5, all-region policy and 16-pixel minimum. This review performed no new inference and changed no thresholds or labels.

## Actual visible patterns

Many red masks are focal patches on joint-adjacent bone ends. Wrist examples include compact patches in `IMG0001224.jpg`, `IMG0001320.jpg`, `IMG0001344.jpg` and `IMG0003003.jpg`, and a broader wedge in `IMG0003322.jpg`. At the elbow, the masks range from a compact distal upper-arm patch in `IMG0000086.jpg` to a broad region spanning much of the proximal forearm/elbow width in `IMG0000990.jpg`. `IMG0002667.jpg`, `IMG0003529.jpg` and `IMG0004060.jpg` show separate or connected lobes across more than one elbow-region bone margin.

Ankle/lower-leg marks include small focal patches, two-lobed marks and broad bands. `IMG0000208.jpg` has separated lobes above the ankle; `IMG0003408.jpg` has a broad ankle-region patch. `IMG0003582.jpg` combines a broad ankle patch with a separate shaft mark, while `IMG0003583.jpg` has a broad transverse band immediately above the ankle. `IMG0003854.jpg` has two narrow distal shaft strips, and `IMG0003941.jpg` has a larger irregular strip above the ankle. These are visible locations and shapes, not an adjudicated explanation involving cortical structures or anatomy overlap.

Forefoot marks are also recurrent: outer metatarsal-end or shaft patches appear in `IMG0000704.jpg`, `IMG0000739.jpg`, `IMG0002997.jpg` and `IMG0003665.jpg`. `IMG0001828.jpg` and `IMG0003160.jpg` contain separated forefoot marks. Other focal masks occur away from a joint: the mid upper-arm shaft in `IMG0000963.jpg` and `IMG0001986.jpg`, lower upper-arm shaft in `IMG0003085.jpg`, and distal lower-leg shaft in `IMG0001606.jpg`. Some pelvis/hip images have multiple separate patches, including `IMG0001764.jpg` and `IMG0001879.jpg`.

Combined-view images show differing mask placement across components. `IMG0000878.jpg` marks a long upper-arm margin and elbow region in the side component while the frontal elbow is largely unmarked. `IMG0002072.jpg` marks the side wrist while the frontal hand component is largely unmarked. `IMG0001345.jpg`, `IMG0002271.jpg` and `IMG0003151.jpg` mark the frontal knee component while the side component is largely unmarked. These observations cannot establish study-level AP/lateral consistency: the displayed composites are not verified patient or study pairs.

Bright objects do not provide a single demonstrated explanation. In `IMG0000545.jpg`, one mask visibly overlaps a small bright object above the pelvic rim, with another near a hip margin. Conversely, bright bands or loops in `IMG0001759.jpg`, `IMG0001833.jpg`, `IMG0001968.jpg` and `IMG0003224.jpg` are separate from the main red region. Neither co-occurrence nor one observed overlap proves artifact-driven shortcut learning.

## Saved-result comparison context

The matched E11 reference native audit has 139 normal alerts and 117,053 normal false-positive pixels, versus E12's 151 and 156,358. Same-ID saved normal-label cases show 88 persistent false positives, 51 E11 false positives becoming true negatives, 63 E11 true negatives becoming false positives, and 178 persistent true negatives. Thus the net increase hides both recoveries and new errors; it is not simply enlargement of the same 139 masks. E11 selected epoch 9 / global 39 and E12 selected epoch 3 / global 33. Their registered selected-checkpoint comparisons must remain distinct from final-epoch or learning-trajectory comparisons. No improvement or promotion is inferred from this visual subset.

The 151 selected cases carry nonexclusive source flags: hand 50, leg 90, hip 15, shoulder 7, mixed 11, frontal 101, lateral 54, oblique 10, multiscan 14 and hardware 1. Counts overlap and describe only the selected errors; without denominators they are not anatomy/view error rates. Frontal flags are not verified clinical AP labels. Patient identities and clinical fracture subtypes remain unavailable.

## Small regions needing full-panel follow-up

Thirty-four cases explicitly preserve uncertainty about exact boundary or placement. Eight have no definite red region resolvable on the sheet despite the saved alert: **IMG0000201.jpg, IMG0000260.jpg, IMG0000598.jpg, IMG0000612.jpg, IMG0002747.jpg, IMG0002911.jpg, IMG0003078.jpg and IMG0003581.jpg**. All were actually viewed; uncertainty was recorded instead of inventing a region.

| Sheet | Full-panel follow-up image IDs |
| --- | --- |
| 01 | IMG0000040.jpg; IMG0000081.jpg; IMG0000170.jpg |
| 02 | IMG0000201.jpg; IMG0000224.jpg; IMG0000260.jpg |
| 03 | IMG0000294.jpg; IMG0000398.jpg |
| 04 | IMG0000598.jpg; IMG0000612.jpg; IMG0000643.jpg |
| 05 | IMG0000766.jpg |
| 06 | IMG0000937.jpg; IMG0000970.jpg |
| 08 | IMG0001583.jpg |
| 09 | IMG0001750.jpg; IMG0001752.jpg |
| 10 | IMG0001849.jpg |
| 11 | IMG0002058.jpg; IMG0002269.jpg |
| 12 | IMG0002747.jpg; IMG0002753.jpg; IMG0002782.jpg; IMG0002828.jpg |
| 13 | IMG0002911.jpg; IMG0003078.jpg |
| 14 | IMG0003091.jpg; IMG0003143.jpg; IMG0003281.jpg |
| 15 | IMG0003488.jpg |
| 16 | IMG0003581.jpg; IMG0003605.jpg; IMG0003696.jpg |
| 17 | IMG0004178.jpg |

## Reliability limits

Dataset normal labels are the evaluation references, not radiologist adjudication. This review cannot diagnose the originals, relabel them, assign a clinical error cause, or measure radiologist trust. Tiny predictions are not clinically subtle fractures. The displayed score is an uncalibrated maximum-pixel mask proxy, not a validated probability of fracture. Presence supervision is disabled. Visually localizing a red patch does not demonstrate true-region overlap or calibrated certainty.

The results establish unresolved suppression and localization errors on the saved validation examples. They do not identify resolution, loss, annotation quality or initialization as a proven primary cause. This memo selects no next factor, performs no optimization, reads no checkpoint tensors, and accesses no calibration, locked-test or external images. Source panels, frozen tools, protocols, catalogs and production remain unchanged.

## Evidence hashes

| Artifact | SHA-256 |
| --- | --- |
| Actual review completion | `19fbeec53c379c13772fe59fecd63700f65d6412d831d9281f93198ccf9fa750` |
| Per-case visual JSON | `6c597e4d7c5ac31e46e9e69b390be3ea47d5c120cec1cbe9c84b80c239ce3840` |
| Per-case visual CSV | `d30502dbd594548d3155311c754891f83cdfa23f184bdb56b5fbfb29921ef119` |
| Actual sheet notes | `15739e00606d7d82a3d61d6b191bcdcc1e324028c8639e85f78193834bfffc09` |
| Sheet index | `cb545995db8e9ead004f3302fcc8fe8f4aba43890e0965e15179944e4f2f9b2d` |
| Review recorder | `e4d873893298f6ba94cf2bc2bc50189f4a02c3cd354f208ef2414b648aa2abc2` |
| E12 native audit per-case JSON | `18fd3ba0edd6ddb1c567ffc7c88918c6289a5a1250f7e8d2391e38689a0e8ac5` |
| E12 native audit config | `e8e9e764add9bcbe8d3790d58f91c20102c31152b851f9e60b067f6b9c122317` |
| E12 native audit completion | `844e809d0d2d51366a1b25c4f067571a41974491d77d3454d25e3fe72da8d8a6` |
| E11 native audit per-case JSON used for normal transitions | `846acc4ecc7fcc0e73b58c6fe4f46c9ae4cc84fecfce505603d9461927d81438` |
| Frozen manifest, from native audit provenance | `4fb850caf0050e29350002a56a8462c93d49365958ebe721e06be2c49480a318` |

Actual observations, batches, per-case records and completion are preserved in `E12_all_normal_alert_sheets/`.

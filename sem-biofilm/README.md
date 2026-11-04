# Root Canal Biofilm Scorer

A browser app that scores residual *Enterococcus faecalis* biofilm on SEM micrographs of root canal dentine. It follows the protocol *Evaluation of Bacterial Biofilm Removal From Root Canal Surface Following Using Abrasive Zirconia Microparticles…* (N. S. Mahdi, University of Baghdad).

## Scoring index (protocol, after Ozses Ozkaya et al., 2017)

| Score | Biofilm coverage |
|---|---|
| 1 | < 5% |
| 2 | 5–33% |
| 3 | 34–66% |
| 4 | 67–100% |

Coverage is rounded to a whole percent before the index is applied. Fields within 3 points of a cut-off are flagged as borderline.

## Study structure built in

- Groups A–E: no irrigation, passive needle, ultrasonic, sonic, zirconia microparticles
- Root thirds: coronal (10–12 mm), middle (6–8 mm), apical (1–3 mm), with 3 points per third at 1000×
- **Score of a root third = mean of its 3 point scores**
- Name files like `B07_middle_2.tif` (also `B7-M-2`, `B07_m2`, `B07 cor p1`). Root, group, third and point fill in automatically.
- Tubule occlusion check images (1000×/1500×/2000×) can be marked as open, partly occluded or occluded instead of scored.

## Workflow

1. **Reference photos.** Add SEM photos you have scored by eye and give each your score (1–4). You can also enter its coverage % if you measured it. Aim for 3–5 per score level from different groups and thirds, imaged with the study's SEM settings.
2. **Learn from references.** The app measures each reference's coverage at every brightness threshold and keeps the thresholds that give every reference your score. It uses the middle of that range and reports:
   - how many references it reads correctly,
   - leave-one-out agreement (each reference predicted by a threshold learned without it),
   - quadratic weighted κ.
3. **Study photos.** They are scored automatically with the learned threshold.
4. **Score sheet.** One row per root, with P1–P3 and the mean for each third.
   - A point takes its score from its photo, or you can choose a score yourself. Your score always wins.
   - Points without a photo can be typed in directly.
   - **Copy for SPSS** or **Save as CSV** gives one row per root: point scores, third means and coverage.
5. **Results.** Group × third summary (mean ± SD, median and IQR of third scores), every field with its status, agreement between your scores and the automatic ones, and tubule checks.

## Saving

The published page saves your scores, reference photos, learned threshold, settings and every photo's result with the page. Opened as a local file, it saves in that browser only. Study photos themselves are not stored, only their results; add a photo again to view or re-score it.

## Validation and limits

- **Synthetic tests:**
  - On 24 synthetic dentine fields (0–89% coverage) the automatic score matched the true score in 24/24, with a mean coverage error of 1.4 points.
  - In an end-to-end test with 8 synthetic references, learning gave 8/8 correct (8/8 leave-one-out). 9 of 10 new photos got the true score; the miss was 4.6% true vs 4.4% read, at the 5% cut-off, and was flagged as borderline.
  - Synthetic images are easier than real micrographs.
- **Constant imaging conditions:** the learned threshold is a brightness level. It holds only if every field is imaged with the same kV, detector, brightness and contrast; turn off automatic brightness/contrast.
- **Before reporting:** type your own score on a blinded subset of study photos and report the weighted kappa from the Examiner agreement tab.
- **TIFF decoder:** loads from a CDN, so TIFFs need an internet connection. PNG and JPEG work offline.

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
- Name files like `B07_middle_2.tif` (also `B7-M-2`, `B07_m2`, `B07 cor p1`). Sample, group, third and point fill in automatically.
- Tubule occlusion check images (1000×/1500×/2000×) can be marked as open, partly occluded or occluded instead of scored.

## Use

Open `index.html` in a browser. Images are processed locally and never uploaded.

1. Add the SEM TIFFs. On Thermo Fisher/FEI images, pixel size, HFW and data-bar height come from the metadata.
2. Open *Biofilm detection* and set the brightness threshold once with **Set from this image** on a well-covered field. Check it on a clean field, then leave it unchanged for the whole study.
3. On each field, box cracks, splitting lines, recesses and non-prepared surfaces with **Exclude area**. Click loose zirconia particles or debris to exclude them.
4. Review borderline fields and enter an **Examiner score** where you disagree. Your score is used in every table.
5. Copy the tables:
   - **Groups × thirds**: median, IQR, score counts and coverage
   - **Samples (SPSS)**: one row per root
   - **Every field**
   - **Examiner agreement**: exact %, Cohen's κ, linear and quadratic weighted κ
   - **Methods text**

## Validation and limits

- **Synthetic validation:** on 24 synthetic dentine fields (0–89% coverage) the automatic score matched the true score in 24/24, with a mean coverage error of 1.4 points. Synthetic images are easier than real micrographs.
- **Constant imaging conditions:** the fixed brightness threshold relies on the same kV, detector, brightness and contrast for every field. Turn off automatic brightness/contrast while imaging.
- **Before reporting:** score a subset of real fields by eye (blinded to group), enter them as examiner scores, and report the weighted kappa.
- **Point aggregation:** the protocol does not say how the 3 points of a third are combined. Pick the rule (median, score of mean coverage, or highest) under *Biofilm detection* and report it.
- **TIFF decoder:** loads from a CDN, so TIFFs need an internet connection. PNG and JPEG work offline.

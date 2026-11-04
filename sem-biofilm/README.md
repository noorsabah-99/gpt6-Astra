# Biofilm SEM Reader

A browser app that reads scanning electron micrographs of bacterial biofilms and reports:

- **Surface coverage** (% of field occupied by cells)
- **Object and estimated cell counts**, and **cell density** (cells/mm²)
- **Cell length, width and aspect ratio** (ellipse fit) with rod / coccoid / filament classification
- **Aggregation**: share of cells in aggregates, largest aggregate area, Clark–Evans nearest-neighbour index
- A heuristic **biofilm stage** (initial attachment → microcolonies → maturing → confluent)
- Batch results per image and per group/condition (mean ± SD), copied as tab-separated text for Excel, Sheets or Prism, plus a generated methods paragraph

## Use

Open `index.html` in a browser (Chrome, Edge, Firefox, Safari). Nothing is uploaded: images are processed locally.

1. **Add SEM images** (TIFF, PNG, JPEG) or drag them onto the viewer.
2. **Calibration** is read automatically from Thermo/FEI (`PixelWidth`), Zeiss (`Image Pixel Size`) and Tescan (`PixelSizeX`) TIFF metadata, or from a Hitachi/JEOL `.txt` sidecar with the same file name. Otherwise click **Measure scale bar**, drag along the bar and enter its length.
3. The instrument **data bar** is detected and excluded; adjust its height if needed.
4. Tune **Segmentation** (applies to all images so the batch stays comparable). Check the *Overlay* and *Mask* views.
5. Click objects to exclude debris, salt crystals or filter pores.
6. Give each image a **group** and copy the tables.

TIFF decoding uses UTIF.js from a CDN, so TIFFs need an internet connection; PNG/JPEG work offline.

## Pipeline

Grey-level top-hat background correction → Gaussian smoothing → Otsu threshold (+ offset) → binary opening, hole filling, size filter → marker-controlled watershed on the smoothed Euclidean distance map (h-maxima seeds) → per-object moments.

## Limits

SEM shows the dehydrated top surface only. Coverage and stage do not measure thickness or EPS; confirm with cross-sections, CLSM or crystal-violet assays. Overlapping cells in dense multilayers are undercounted. Validate the settings against a few manually counted fields before reporting numbers.

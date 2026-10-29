# Poster

A2 portrait poster (420 × 594 mm) for the 2nd dAIversity Conference, in Polish.

- `poster-dAIversity-2026-A2.pdf`: print file (one page, fonts embedded).
- `poster-pl.dc.html`: poster source; laid out at 3178 × 4494 px and scaled by 0.4995 to A2.
- `poster-pl-preview.png`: rendered preview.
- `qr-repo.svg`: QR code to this repository (error correction level M, version 5), checked by
  decoding it from the rendered poster.

Figures come from `../code/poster_figs.py --lang pl` applied to `../data/main/analysis/results.json`,
with no additional computation. Typeface: Nunito Sans (SIL Open Font License), converted to outlines
in the SVG figures. Every number on the poster comes from `../data/main/analysis/RESULTS.md` and
`INTERPRETATION.md`.

- `poster-dAIversity-2026-2xA3.pdf`: the same poster as two A3 landscape pages (stacked they give
  A2): page 1 main result and conclusions, page 2 evidence, method, references and QR code.

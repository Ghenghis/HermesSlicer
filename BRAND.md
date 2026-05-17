# HermesSlicer Brand Assets

HermesSlicer V1 uses the Hermes + Orca unified brand system for visible project surfaces. Only the assets needed by the current proofable stack are imported:

- `web/assets/hermes-slicer-login.png` for the local-session login gate.
- `web/assets/readme-hero.png` for the GitHub README hero.
- `web/assets/hermes-orca-minimal.svg` for favicon and compact panel branding.
- `web/assets/hermes-orca-primary.svg` as the full vector mark for future app packaging surfaces.
- `web/assets/hermes-slicer-icon-32.png` and `web/assets/hermes-slicer-icon-256.png` for PNG favicon fallback and touch/app icon metadata.
- `config/brand_tokens.json` for the dark background, cyan accent, and gold accent tokens enforced by UI tests.

Unused source-pack extras stay out of the V1 tree until a concrete runtime or packaging surface needs them.

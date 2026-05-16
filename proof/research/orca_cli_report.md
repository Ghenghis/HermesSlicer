# Orca CLI Report

Date: 2026-05-16

## Sources

- https://github.com/OrcaSlicer/OrcaSlicer
- https://github.com/OrcaSlicer/OrcaSlicer/releases/tag/v2.3.2
- https://github.com/OrcaSlicer/OrcaSlicer/wiki/import_export
- https://github.com/OrcaSlicer/OrcaSlicer/issues/8352

## Source State

- OrcaSlicer latest release resolved to `v2.3.2`, released 2026-03-23.
- Release tag SHA observed with `git ls-remote`: `c724a3f5f51c52336624b689e846c8fbc943a912`.
- Default branch HEAD observed with `git ls-remote`: `b3fe733bf2c8fa7d3c5bf78e93608ca1cd295a7b`.
- License note: AGPL-3.0. Orca code reuse/forking must preserve license obligations.

## Local Commands

```powershell
& 'C:\Program Files\OrcaSlicer\orca-slicer.exe' --version
```

Observed: `Invalid option --version`

```powershell
& 'C:\Program Files\OrcaSlicer\orca-slicer.exe' --help
```

Observed: exit 0 with no console text in this environment.

```powershell
& 'C:\Program Files\OrcaSlicer\orca-slicer.exe' --info 'G:\Github\HermesSlicer\samples\test_cube.stl'
```

Observed: reports `size_x = 1.000000`, `number_of_facets = 12`, `manifold = yes`, and `volume = 1.000000`.

```powershell
Get-ChildItem -Name 'C:\Program Files\OrcaSlicer\resources\profiles' | Select-Object -First 20
```

Observed: vendor folders including Afinia, Anet, Anycubic, BBL, BIQU, Creality, Elegoo.

## Decision

Use Orca as the primary local executable. For V1, treat `--info` and profile folder listing as reliable non-destructive proofs. Do not depend on `--version`.

## Risks

- CLI flags are not a stable public product surface.
- Actual G-code export requires valid printer, process, and filament profiles. Keep export disabled until profile composition is pinned and proven.

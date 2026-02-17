# Example JSON Configuration for Sesame CLI

This directory contains example JSON configuration files for use with `sesame-cli`.

## system_config.json

A complete system configuration with materials, doping, contacts, and generation.

**Usage:**
```bash
sesame-cli simulate --config-json system_config.json --voltage-loop --loop-values "0,0.5,1.0" --out-dir ./results
```

## material_example.json

A single material definition. Can be used with `add-material`:

```bash
sesame-cli add-material mysys.gzip --mat-file material_example.json --out mysys2.gzip
```

## defects_example.json

A list of defects (point and line defects).

```bash
sesame-cli build --out mysys.gzip
# Then manually add defects using add-defect or parse JSON externally
```

## Notes

- All energies are in **eV**
- All lengths are in **cm** (unless you change the scaling in the Builder)
- Densities are in **cm⁻³**
- Mobilities are in **cm²/(V·s)**
- Time constants (tau) are in **seconds**

# Third-Party Notices

This anonymous artifact vendors a small Python runtime environment so that the
counted replay does not depend on packages installed on the reviewer machine.
The package versions are pinned in `requirements.txt`, resolved from
`artifact/vendor_python`, and checked by `scripts/verify_dependency_provenance_gate.py`
and `scripts/verify_resource_license_gate.py`.

The LatticeGuard artifact source code is released under the MIT license in
`LICENSE`. Third-party runtime packages retain their upstream licenses; their
wheel metadata and license files are kept under `vendor_python/*dist-info/`.

| Package | Version | License disposition | Local evidence |
|---|---:|---|---|
| pycasbin | 2.8.0 | Apache-2.0 / Apache 2.0 metadata | `vendor_python/pycasbin-2.8.0.dist-info/licenses/LICENSE` |
| cedarpy | 4.8.3 | Apache-2.0 license file | `vendor_python/cedarpy-4.8.3.dist-info/licenses/LICENSE` |
| simpleeval | 1.0.7 | MIT metadata/license file | `vendor_python/simpleeval-1.0.7.dist-info/licenses/LICENCE` |
| wcmatch | 10.1 | MIT license expression/file | `vendor_python/wcmatch-10.1.dist-info/licenses/LICENSE.md` |
| bracex | 2.6 | MIT license expression/file | `vendor_python/bracex-2.6.dist-info/licenses/LICENSE.md` |

External project/documentation URLs in `external_resources.csv` are used as
citation, context, or source-provenance records only. Their text is not
redistributed in the packet unless the corresponding source slice appears in
`source_manifest.csv` with a local path and SHA-256 hash. OPA/Rego execution is
enabled in the current counted run only because the bundled executable matches
the local checksum contract before any OPA row is observed; if the executable is
removed or hash-mismatched, OPA is excluded and the denominator is recomputed.

## pypdf 5.9.0

Purpose: PDF page-count and text-surface checks used by the reproducibility-risk gate.
Declared in: `requirements.txt` as `pypdf==5.9.0`.
Vendored evidence: `artifact/vendor_python/pypdf-5.9.0.dist-info/` and `artifact/vendor_python/pypdf-5.9.0.dist-info/licenses/LICENSE`.
License: BSD-3-Clause, as declared by the vendored package metadata and license file.

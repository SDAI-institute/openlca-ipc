# Migration Guide

## From raw `olca-ipc`

`openlca-ipc` wraps the upstream client with higher-level managers for search, data creation, product systems, calculations, results, contribution analysis, uncertainty, parameters, export, diagnostics, and agent-oriented responses.

Typical migration:

- replace manual descriptor scans with `client.search` helpers;
- replace manual flow/process construction with `client.data`;
- create product systems through `client.systems` so linking choices stay explicit;
- use `client.results` and `client.contributions` instead of parsing raw result objects for common tasks;
- always dispose live calculation results.

## From package versions before 0.3

Current releases target Python 3.11+ and `olca-ipc`/`olca-schema` 2.6+. Do not carry forward code that assumes `olca_ipc.Client.close()`, legacy contribution RPC methods, or the older simulator API.

## From 0.3 to 0.4+

v0.4 is additive: contribution trees, full inventory access, normalization/weighting, total requirements, Sankey data, system comparison, exact entity lookup, agent/reproducibility helpers, read-only mode, and diagnostics were added without intentionally removing the v0.3 public surface.

v0.4.1 additionally corrected reference-unit handling for non-mass exchanges. Re-run studies that depended on transport, energy, volume, land, or other non-mass flows if they were produced with an affected earlier implementation.
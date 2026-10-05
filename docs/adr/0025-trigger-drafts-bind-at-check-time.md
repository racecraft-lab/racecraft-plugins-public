# Bind trigger campaign templates at check time

Status: accepted

For [#1244](https://github.com/racecraft-lab/racecraft-plugins-public/issues/1244),
commit stable `trigger-experiment-template/v1` planning inputs without observer,
catalog or fixture identities. `compare-trigger-evals.py rebind --manifest
<template> --out <new-manifest>` freezes the current identities into a separate
`trigger-experiment/v1` manifest. CI's trigger-campaign tests bind both committed
templates, validate them against the inventory and current tree, and assert
that stale concrete bindings fail validation with exit code 2.

The templates now prove the reviewed roster, model/CLI pins, description digests
and requested budget, not an association with one historical observer or
catalog. Binding grants no launch authority or qualification. Select the output
directory and obtain the existing budget approval against the final concrete
manifest before launch. Indexing, comparison and launch still require concrete
identities; they never bind or repair templates implicitly. Historical evidence
and carry-forward verification keep their existing frozen-input contracts.

We rejected a custom merge driver: its definition belongs in Git configuration,
not `.gitattributes`, so declaring an attribute cannot deploy it to every clone
or merge service ([Git documentation](https://git-scm.com/docs/gitattributes#_defining_a_custom_merge_driver)).
We also rejected moving the hashes into a committed generated file:
`refresh-release-artifacts.py --check` could detect drift there, but both branches
would still edit the same hashes; avoiding that conflict would again depend on
a merge driver. The release-artifact check retains its existing scope. Campaign
binding validation stays with the campaign suite already run by CI.

A provider-free regression creates two branches that each change an observer
and a host catalog, binds each tree independently, and merges both into main
without a merge driver or changes to either template. No live campaign result
is claimed by this check.

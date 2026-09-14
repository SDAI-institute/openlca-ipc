# ContributionAnalyzer API

`ContributionAnalyzer` interprets a completed openLCA result at process, elementary-flow, and upstream-tree levels.

## `get_process_contributions(result, impact_category, min_share=0.01)`

Returns process/technology-flow contributors for one impact category as `ContributionItem` objects with name, amount, share, and process reference.

## `get_flow_contributions(result, impact_category, min_share=0.01)`

Returns elementary-flow contributors for one impact category.

## `get_top_contributors(result, impact_category, n=5, contribution_type="process")`

Convenience helper returning the top `n` process or flow contributors.

## `get_contribution_tree(result, impact_category, *, max_depth=3, min_share=0.01)`

Builds a recursive upstream `TreeNode` structure. Depth and minimum-share pruning bound the number of upstream requests and keep the tree interpretable.

## `get_contribution_summary(result, impact_categories=None)`

Returns a top-contributor summary for selected impact categories or all categories in the result.

## Interpretation guidance

A hotspot is a model result, not automatically a design recommendation. Review whether it is driven by a true foreground burden, a background dataset choice, allocation, geography, system boundary, or another methodological assumption before acting on it.
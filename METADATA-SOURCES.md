# Metadata sources

Game dates, image references and critic-score facts were automatically extracted from English Wikipedia articles. Each enriched entry in `data/metadata.js` records its article URL, revision ID, matched title and collection date. Some PS4 dates come from Wikipedia's lists of PS4 games, with the list URL retained in `ps4Source`.

The short Hebrew and English reception text is generated from the score and explicit evaluative clauses in the article's reception section. It is an automatic, limited summary, not a review based on personal gameplay. Article sections may cover multiple platforms or editions. A numeric score always retains its platform; unspecified platforms are not relabeled as PS4. Metacritic scores are sourced through Wikipedia, not independently rechecked against Metacritic.

Wikipedia text and adaptations are attributed to the linked article's contributors and available under [CC BY-SA 4.0](https://creativecommons.org/licenses/by-sa/4.0/), subject to [Wikipedia's terms](https://en.wikipedia.org/wiki/Wikipedia:Copyrights). For contributor history, use the History tab on the linked article. The metadata includes the source revision for reproducibility.

Cover art remains copyrighted by its respective rights holders. The portal links to the Wikimedia-hosted thumbnail and the individual file-description page, which documents rights and usage information. Wikipedia's text license does not grant a license to non-free cover artwork. Images are not copied into this repository. A thumbnail can represent the original release rather than PS4 packaging.

Automated name matching can miss abbreviations, bundles, modded packages, ambiguous titles and editions without a dedicated article. Missing fields remain explicit. The audit report covers every catalog entry; it does not claim that all titles have complete metadata or that every remote image will always be available.

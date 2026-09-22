# Metadata sources

Game dates, image references and critic-score facts were automatically extracted from English Wikipedia articles. Each enriched entry in `data/metadata.js` records its article URL, revision ID, matched title and collection date. Some PS4 dates come from Wikipedia's lists of PS4 games, with the list URL retained in `ps4Source`.

The short Hebrew and English reception text is generated from the score and explicit evaluative clauses in the article's reception section. It is an automatic, limited summary, not a review based on personal gameplay. Article sections may cover multiple platforms or editions. A numeric score always retains its platform; unspecified platforms are not relabeled as PS4. Metacritic scores are sourced through Wikipedia, not independently rechecked against Metacritic.

Wikipedia text and adaptations are attributed to the linked article's contributors and available under [CC BY-SA 4.0](https://creativecommons.org/licenses/by-sa/4.0/), subject to [Wikipedia's terms](https://en.wikipedia.org/wiki/Wikipedia:Copyrights). For contributor history, use the History tab on the linked article. The metadata includes the source revision for reproducibility.

Cover art remains copyrighted by its respective rights holders. The portal links to the Wikimedia-hosted thumbnail and the individual file-description page, which documents rights and usage information. Wikipedia's text license does not grant a license to non-free cover artwork. Images are not copied into this repository. A thumbnail can represent the original release rather than PS4 packaging.

Automated name matching can miss abbreviations, bundles, modded packages, ambiguous titles and editions without a dedicated article. Missing fields remain explicit. The audit report covers every catalog entry; it does not claim that all titles have complete metadata or that every remote image will always be available.

## Supplemental sources and written reviews

`scripts/supplement_metadata.py` reuses the cached Wikipedia reception sections and includes up to 110 words with attribution and a page link. This adapted extract retains the article CC BY-SA terms. It is labeled as an English source excerpt, not a Hebrew translation or an original review.

For incomplete entries the script requests public Metacritic game pages, accepts only exact normalized title matches, and extracts structured release dates, images, platform-specific scores, and at most two 24-word critic excerpts. Each critic excerpt retains the publisher, platform, full-review link, and Metacritic page. A catalog entry with no source match remains incomplete. Metacritic images and critic quotations belong to their respective owners. Scores retain the platform of the source, preferentially PS4; other platforms are displayed explicitly.

Supplements are stored separately and reapplied during Wikipedia rebuilds. Run the audit after either script. Coverage is structural, not a guarantee that every automatic title match is correct or every remote image is currently reachable.

## Hebrew editorial reviews

GamePro review archive pages are matched by the leading game title or an exact review URL slug. Roundups, first-review news, and incidental mentions of other games are excluded. Original Hebrew extracts are capped at 24 words per article and link to the full review; no forum posts are used. Vgames sources in `scripts/hebrew-review-sources.json` were checked individually; their Hebrew text is an attributed paraphrase, labeled as a summary. Scores are only extracted from explicit rating elements and keep their /10 scale.

## Genres

Genres are extracted from Wikipedia infoboxes, the cached PS4 game list, or exact-title Metacritic JSON-LD. A documented taxonomy maps source terms into one or more bilingual tags (e.g. action role-playing → Action + Role-playing). No personal data is changed. Edition/collection mappings and publisher-verified additions retain provenance in `scripts/genre-sources.json`; expansion and regional-version tags inherit the base game's or series' genre and record this basis. Unknown identities remain unclassified.

## IGN Israel and Hebrew translations

IGN Israel (`il.ign.com`) is matched by review title or game slug, excluding TV episodes, seasons and film reviews. Its short Hebrew verdict/excerpt (up to 24 words) and explicit /10 score retain the review URL and platform when indicated. Vgames and IGN Israel precede GamePro in display order.

Wikipedia reception excerpts are translated to Hebrew using Google Translate, retaining Wikipedia attribution and CC BY-SA terms. Machine translations are labeled and accompanied by an expandable English original. They are not presented as content from Hebrew Wikipedia. Source-text equality prevents stale translations being attached to updated source excerpts. Only public source text is submitted during generation; no personal notes or saved catalog status are read by the translation script.
# Absolute Drift correction

Absolute Drift includes manually checked, paraphrased PS4 review summaries from [GameSpew](https://www.gamespew.com/2016/08/absolute-drift-zen-edition-review/) and [PlayStation Country](https://www.playstationcountry.com/absolute-drift-zen-edition-ps4-review/), with Hebrew and English versions. The latter awards 7/10. The replacement image is linked from the game's [Steam listing](https://store.steampowered.com/app/320140/Absolute_Drift/). These corrections are retained in metadata-supplements.json. No verified Vgames or IGN Israel review was located for this title in this search; that does not establish that none exists.

Review coverage remains partial. A sentence derived from a Metacritic score is not a written editorial review, and the metadata completeness count must not be interpreted as coverage from every publisher.

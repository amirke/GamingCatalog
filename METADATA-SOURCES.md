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

## Catalog-wide editorial enrichment

`scripts/enrich_editorial_reviews.py` searches every catalog row independently of metadata completeness. It validates the structured game title, retains up to three distinct publishers with short excerpts (at most 24 words each), and prefers Vgames, IGN Israel and IGN when present. Curated edition aliases are recorded in `scripts/editorial-titles.json`; manually verified bilingual paraphrases are in `scripts/editorial-manual.json`. Review platform and edition caveats are retained rather than relabeling every review as PS4. Early-access and historical impressions describe the reviewed version, not necessarily the current game.

The portal deduplicates publisher links, shows both the original review URL and the Metacritic intermediary, and translates public English excerpts to Hebrew in advance. The English source is expandable. Manual summaries are labeled as summaries, not verbatim quotations. Wikipedia reception and score-derived prose remain separately labeled and are excluded from the editorial-coverage count. Reviews from different sites can disagree.

`data/editorial-audit.json` checks all catalog rows for source links, Hebrew availability and search outcomes. Its Markdown counterpart lists unresolved titles. `data/image-audit.json` records image loading/decoding results. `data/image-repair-report.json` records replacements or additions from title-validated review artwork, persisted in metadata supplements. This is not a visual verification of every image, and availability can change.

Vgames archive requests returned HTTP 403; indexed pages were checked individually where available. Thus Israeli coverage is partial, not proof that missing articles do not exist. No forum posts or user-review scores are substituted for editorial coverage. Catalog names and public review text were submitted with user consent; personal catalog state, notes and Gist credentials are never inputs to these scripts.

## PS2 descriptions and genres — 2026-09-27

All 38 converted PS2 records in `data/ps2-games.js` contain original short Hebrew/English descriptions, genre IDs from the existing taxonomy, and a linked source with a checked date. These are descriptive summaries, not editorial reviews or review scores. Genres are curated from the referenced gameplay descriptions.

Disc identity checks distinguish G-Force SLES53934 (water skiing), the two demo compilations, Play It! Arcade Classics from SNK's collection, Rayman Revolution from other Rayman 2 ports, and the 2004 Transformers game from the 2007 film adaptation. SingStar descriptions use sourced series gameplay; edition names and regions come from the verified disc catalog, without unverified track-list claims. No PS4 metadata or personal saved fields were copied over.

Coverage verified: 38 bilingual descriptions, 38 nonempty genre sets, and 38 HTTPS source links. Browser tests cover genre filtering (10 music titles, 3 sports titles, zero unclassified PS2 entries), both views, Hebrew/English, mobile layout, and persistence of downloaded status.

## Collection contents and manual addition — 2026-09-27

`data/collections.js` records 48 populated lists (471 entries including separately identified platform variants, demos and campaigns), each linked to its source. PS2 regional distinctions are retained: PAL Sega Classics excludes Alien Syndrome; PAL Mega Drive Collection excludes Shadow Dancer; Taito Legends 2 has the 39 PS2 titles, not the different PC/Xbox roster. The two demo discs are explicitly labeled as demos. Best Games Ever 1 was identified as SCED-50161; source lists were cross-checked against the two discs' directory contents without modifying the discs.

SNK Collection and Pinball Arcade have explicit unresolved entries: the catalog filename alone does not establish the precise SNK edition or installed pinball table packs. No inferred installed-content list is substituted. Other lists describe the linked retail edition; they do not prove that optional DLC is installed in a local PKG.

The new manual PS4 record is The Smurfs: Village Party, CUSA47540, v1.00, with firmware 11.00 retained from the user-supplied filename. Its region and byte size are unknown. Release year, party/adventure genres, 50 mini-games and local multiplayer description come from the [publisher's Steam listing](https://store.steampowered.com/app/2800630/The_Smurfs__Village_Party/); the image is linked to the Steam CDN, not bundled in the repository. The bilingual paraphrase and 6/10 score come from [Daniel Waite's review at Movies Games and Tech](https://moviesgamesandtech.com/2024/06/06/review-the-smurfs-village-party/), dated June 6, 2024. The reviewed platform is Xbox Series X and is displayed explicitly. No verified Vgames or IGN Israel review was located in this search; this is not proof none exists. No aggregate Metacritic score was invented.

The manual record is separate from the SQLite-generated catalog so rebuilding that catalog does not remove the addition. Existing catalog IDs and user state are preserved. Browser validation covers nested contents in both layouts and languages, content search, mobile width, new-game filters, saved interest text, review attribution, image loading and enlargement.

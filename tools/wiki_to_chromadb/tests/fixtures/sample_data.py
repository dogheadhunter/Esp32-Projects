"""
Test fixtures for wiki-to-chromadb pipeline tests.
"""

# Sample wikitext for testing
SAMPLE_WIKITEXT_VAULT_101 = """
{{Infobox location
|name = Vault 101
|game = Fallout 3
|location = Capital Wasteland
|built = 2063
|inhabitants = Vault dwellers
}}

{{Game|FO3}}

= Overview =
'''Vault 101''' was a [[Vault-Tec Corporation|Vault-Tec]] [[vault]] located in the [[Capital Wasteland]].

== Background ==
Built in 2063 as part of {{Icon|vault}} Project Safehouse.

=== Pre-War Era ===
Before the [[Great War]], Vault-Tec constructed Vault 101.

==== Vault Construction ====
The vault was built to house 1000 residents.

=== Post-War Era ===
After the war, the vault remained sealed.

== Notable Residents ==
* [[Lone Wanderer]]
* [[Amata Almodovar]]
* [[James (Fallout 3)|James]]

[[Category:Vaults]]
[[Category:Fallout 3 locations]]
[[Category:Capital Wasteland]]
"""

SAMPLE_WIKITEXT_SIMPLE = """
{{Game|FO3|FO4}}

This is a simple article about a [[weapon]].

The '''10mm pistol''' is a common weapon.

[[Category:Weapons]]
"""

SAMPLE_WIKITEXT_NO_METADATA = """
This is plain text with no templates or categories.

Just some content.
"""

# Expected extraction results
EXPECTED_CATEGORIES_VAULT_101 = [
    "Vaults",
    "Fallout 3 locations",
    "Capital Wasteland"
]

EXPECTED_SECTIONS_VAULT_101 = [
    {"level": 1, "title": "Overview"},
    {"level": 2, "title": "Background"},
    {"level": 3, "title": "Pre-War Era"},
    {"level": 4, "title": "Vault Construction"},
    {"level": 3, "title": "Post-War Era"},
    {"level": 2, "title": "Notable Residents"},
]

EXPECTED_GAME_SOURCE_VAULT_101 = ["Fallout 3"]

EXPECTED_WIKILINKS_VAULT_101_COUNT = 6  # Vault-Tec, vault, Capital Wasteland, Great War, etc.

EXPECTED_INFOBOX_TYPE_VAULT_101 = "Infobox location"

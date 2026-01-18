from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Optional


@dataclass(frozen=True)
class Fixup:
    confidence: float
    needs_review: bool
    notes: str
    active_during: list[str]
    julie_2102: str
    geography_region: str = "Appalachia"
    specific_location: str = "Unknown"
    founded: Optional[str] = None
    defunct: Optional[str] = None
    description: Optional[str] = None


FIXUPS: dict[str, Fixup] = {
    # Events
    "event_great_war": Fixup(
        confidence=0.95,
        needs_review=False,
        notes="Canon: Great War begins Oct 23, 2077. (Series-wide event; FO76 references via terminals/holotapes.)",
        active_during=["2077-10-23"],
        julie_2102="historical",
        geography_region="Global",
        specific_location="Earth",
        description="The Great War was the brief nuclear exchange on October 23, 2077 that ended pre-war civilization and began the post-apocalyptic era.",
    ),
    "event_reclamation_day": Fixup(
        confidence=0.95,
        needs_review=False,
        notes="Canon (FO76): Vault 76 opens on Reclamation Day, Oct 23, 2102.",
        active_during=["2102-10-23"],
        julie_2102="firsthand",
        specific_location="Vault 76",
        description="Reclamation Day (Oct 23, 2102) is when Vault 76 opens and its residents emerge into Appalachia.",
    ),
    "event_scorched_plague": Fixup(
        confidence=0.90,
        needs_review=False,
        notes="Canon (FO76): Scorched Plague is the central ongoing threat in 2102 Appalachia.",
        active_during=["2083-2103"],
        julie_2102="firsthand",
        description="The Scorched Plague is a contagious affliction spread by scorchbeasts, creating the Scorched and threatening all life in Appalachia.",
    ),
    "event_timeline2102": Fixup(
        confidence=0.85,
        needs_review=False,
        notes="Canon (FO76): 2102 is the year Vault 76 opens and the FO76 main timeline begins in Appalachia.",
        active_during=["2102"],
        julie_2102="historical",
        description="Year 2102 in Appalachia: Vault 76 opens and the events of Fallout 76 begin.",
    ),
    "event_appalachiahistory": Fixup(
        confidence=0.80,
        needs_review=False,
        notes="Canon: High-level Appalachia history context; constrain to 2077-2103 for this project timeline.",
        active_during=["2077-2103"],
        julie_2102="historical",
        description="High-level history/context for post-war Appalachia leading up to and including the early Fallout 76 era.",
    ),

    # Factions
    "faction_responders": Fixup(
        confidence=0.92,
        needs_review=False,
        notes="Canon (FO76): Responders formed after the Great War from WV emergency services; original group collapses by 2096. (Reformed Responders are 2103+.)",
        active_during=["2077-2096"],
        founded="2077",
        defunct="2096",
        julie_2102="historical",
        specific_location="Charleston / Flatwoods",
        description="A post-war humanitarian relief organization formed from police, firefighters, and medical responders. The original Responders are defunct by Reclamation Day.",
    ),
    "faction_free_states": Fixup(
        confidence=0.90,
        needs_review=False,
        notes="Canon (FO76): Free States were Appalachian secessionists/survivalists with pre-war roots; wiped out by the Scorched by 2102.",
        active_during=["2077-2096"],
        founded="2077",
        defunct="2096",
        julie_2102="historical",
        specific_location="Harper's Ferry",
        description="An anti-government secessionist movement with pre-war roots. After the bombs fell, Free Staters operated from bunkers and settlements until the Scorched devastated them.",
    ),
    "faction_appalachian_brotherhood_of_steel": Fixup(
        confidence=0.92,
        needs_review=False,
        notes="Canon (FO76): Appalachian chapter (Taggerdy's Thunder) forms after Maxson contact (2082) and is destroyed by the Scorched by 2095.",
        active_during=["2082-2095"],
        founded="2082",
        defunct="2095",
        julie_2102="historical",
        specific_location="Fort Defiance",
        description="The Brotherhood of Steel chapter in Appalachia led by Paladin Elizabeth Taggerdy. The chapter is defunct by 2102 after catastrophic losses to the Scorched.",
    ),
    "faction_raiders_fallout_76": Fixup(
        confidence=0.88,
        needs_review=False,
        notes="Canon (FO76): Original Appalachian raider gangs (Top of the World era) collapse before Reclamation Day; Crater Raiders are 2103+.",
        active_during=["2077-2096"],
        founded="2077",
        defunct="2096",
        julie_2102="historical",
        specific_location="Top of the World",
        description="Appalachia's raider gangs once held territory around Top of the World but collapse before 2102. A separate raider faction at Crater appears later (2103+).",
    ),
    "faction_cult_of_the_mothman": Fixup(
        confidence=0.88,
        needs_review=False,
        notes="Canon (FO76): Mothman cultists are active in Appalachia; centered on Point Pleasant and related sites.",
        active_during=["2077-2103"],
        julie_2102="firsthand",
        specific_location="Point Pleasant",
        description="A religious movement venerating the Mothman. Various cultist groups are active in Appalachia during Fallout 76.",
    ),
    "faction_scorched": Fixup(
        confidence=0.92,
        needs_review=False,
        notes="Canon (FO76): The Scorched are victims of the Scorched Plague, driven by a hive-mind influence tied to scorchbeasts and ultracite.",
        active_during=["2083-2103"],
        julie_2102="firsthand",
        specific_location="Across Appalachia",
        description="The Scorched are infected victims of the Scorched Plague, acting as hostile vectors of the disease across Appalachia.",
    ),

    # Locations / Regions
    "location_appalachia": Fixup(
        confidence=0.90,
        needs_review=False,
        notes="Canon (FO76): Appalachia is the West Virginia region comprising The Forest, Toxic Valley, Savage Divide, The Mire, Cranberry Bog, and Ash Heap.",
        active_during=["2102-2103"],
        julie_2102="firsthand",
        specific_location="West Virginia",
        description="Appalachia is the post-war region of West Virginia where Fallout 76 takes place.",
    ),
    "location_the_forest": Fixup(
        confidence=0.95,
        needs_review=False,
        notes="Canon (FO76): The Forest is the starting region containing Vault 76 and Flatwoods.",
        active_during=["2102-2103"],
        julie_2102="firsthand",
        specific_location="The Forest (region)",
        description="The Forest is the lush starting region of Appalachia, containing Vault 76, Flatwoods, and many early FO76 locations.",
    ),
    "location_toxic_valley": Fixup(
        confidence=0.90,
        needs_review=False,
        notes="Canon (FO76): Toxic Valley is a northern Appalachia region defined by industrial waste and radiation.",
        active_during=["2102-2103"],
        julie_2102="firsthand",
        specific_location="Toxic Valley (region)",
        description="Toxic Valley is the northern region of Appalachia, marked by industrial pollution and harsh terrain.",
    ),
    "location_savage_divide": Fixup(
        confidence=0.90,
        needs_review=False,
        notes="Canon (FO76): Savage Divide is the central mountain range dividing Appalachia.",
        active_during=["2102-2103"],
        julie_2102="firsthand",
        specific_location="Savage Divide (region)",
        description="Savage Divide is the central mountainous spine of Appalachia, separating multiple regions.",
    ),
    "location_the_mire": Fixup(
        confidence=0.90,
        needs_review=False,
        notes="Canon (FO76): The Mire is the eastern swampy region of Appalachia.",
        active_during=["2102-2103"],
        julie_2102="firsthand",
        specific_location="The Mire (region)",
        description="The Mire is the eastern swampy region of Appalachia, dense with mutated flora and dangerous wildlife.",
    ),
    "location_cranberry_bog": Fixup(
        confidence=0.90,
        needs_review=False,
        notes="Canon (FO76): Cranberry Bog is the southeastern scorched region of Appalachia.",
        active_during=["2102-2103"],
        julie_2102="firsthand",
        specific_location="Cranberry Bog (region)",
        description="Cranberry Bog is the southeastern region of Appalachia, heavily affected by the Scorched and late-game threats.",
    ),

    # Specific locations
    "location_vault_76": Fixup(
        confidence=0.95,
        needs_review=False,
        notes="Canon (FO76): Vault 76 opens on Oct 23, 2102 (Reclamation Day).",
        active_during=["2102-2103"],
        julie_2102="firsthand",
        specific_location="The Forest",
        description="Vault 76 is the control vault in Appalachia. It opens on Reclamation Day (Oct 23, 2102).",
    ),
    "location_flatwoods": Fixup(
        confidence=0.90,
        needs_review=False,
        notes="Canon (FO76): Flatwoods is an early-game town in The Forest.",
        active_during=["2102-2103"],
        julie_2102="firsthand",
        specific_location="The Forest",
        description="Flatwoods is an early-game town in The Forest, associated with Responders aid/training via holotapes and terminals.",
    ),
    "location_charleston": Fixup(
        confidence=0.90,
        needs_review=False,
        notes="Canon (FO76): Charleston is the former state capital and a major Responders hub; located in The Forest.",
        active_during=["2077-2103"],
        julie_2102="firsthand",
        specific_location="The Forest",
        description="Charleston is the former capital of West Virginia and a major pre-war city; post-war it was a central Responders area before the Scorched devastated the region.",
    ),
    "location_watoga": Fixup(
        confidence=0.90,
        needs_review=False,
        notes="Canon (FO76): Watoga is an automated city in Cranberry Bog.",
        active_during=["2077-2103"],
        julie_2102="firsthand",
        specific_location="Cranberry Bog",
        description="Watoga is an automated pre-war city in the Cranberry Bog, controlled by robots.",
    ),
    "location_foundation": Fixup(
        confidence=0.90,
        needs_review=False,
        notes="Canon (FO76): Foundation is a Settlers town established in 2103 (Wastelanders-era). Julie in 2102 cannot treat it as an existing location.",
        active_during=["2103"],
        julie_2102="cannot_know",
        specific_location="The Savage Divide",
        description="Foundation is a Settlers town established after people return to Appalachia (2103). It should not be referenced as existing in 2102-era broadcasts.",
    ),
    "location_crater": Fixup(
        confidence=0.90,
        needs_review=False,
        notes="Canon (FO76): Crater is a Raiders hub established in 2103 (Wastelanders-era). Julie in 2102 cannot treat it as an existing location.",
        active_during=["2103"],
        julie_2102="cannot_know",
        specific_location="The Toxic Valley",
        description="Crater is a Raiders settlement established after raiders return to Appalachia (2103). It should not be referenced as existing in 2102-era broadcasts.",
    ),

    # Characters
    "character_meg_groberg": Fixup(
        confidence=0.90,
        needs_review=False,
        notes="Canon (FO76): Meg Groberg is the leader of the Crater Raiders (2103+). Julie in 2102 cannot know her as a current figure in Appalachia.",
        active_during=["2103"],
        julie_2102="cannot_know",
        specific_location="Crater",
        description="Meg Groberg leads the Raiders at Crater after raiders return to Appalachia (2103).",
    ),
    "character_modus": Fixup(
        confidence=0.92,
        needs_review=False,
        notes="Canon (FO76): MODUS is the Enclave AI operating from the Whitespring bunker; can be encountered in 2102 via quests.",
        active_during=["2077-2103"],
        julie_2102="firsthand",
        specific_location="The Whitespring Bunker",
        description="MODUS is the Enclave's AI presence in Appalachia, operating from the Whitespring bunker.",
    ),

    # Technology
    "technology_camp": Fixup(
        confidence=0.92,
        needs_review=False,
        notes="Canon (FO76): C.A.M.P. is the Construction and Assembly Mobile Platform used by Vault 76 residents.",
        active_during=["2102-2103"],
        julie_2102="firsthand",
        specific_location="Across Appalachia",
        description="The C.A.M.P. (Construction and Assembly Mobile Platform) lets survivors build and relocate small bases across Appalachia.",
    ),
    "technology_pip_boy_2000_mark_vi": Fixup(
        confidence=0.90,
        needs_review=False,
        notes="Canon (FO76): Vault 76 residents use Pip-Boy 2000 Mark VI.",
        active_during=["2102-2103"],
        julie_2102="firsthand",
        specific_location="Vault 76",
        description="The Pip-Boy 2000 Mark VI is standard issue for Vault 76 residents.",
    ),
    "technology_power_armor_fallout_76": Fixup(
        confidence=0.85,
        needs_review=False,
        notes="Canon (FO76): Power armor exists in Appalachia (e.g., T-45/T-51/T-60) and FO76-specific sets like Excavator/Ultracite.",
        active_during=["2077-2103"],
        julie_2102="firsthand",
        specific_location="Across Appalachia",
        description="Powered exoskeleton armor used for combat and hazardous environments; multiple models are present in Appalachia.",
    ),
    "technology_ultracite_power_armor": Fixup(
        confidence=0.88,
        needs_review=False,
        notes="Canon (FO76): Ultracite power armor is tied to Appalachian Brotherhood efforts against the Scorched/Scorchbeasts.",
        active_during=["2095-2103"],
        julie_2102="firsthand",
        specific_location="Appalachia",
        description="A power armor set incorporating ultracite technology, developed to fight the Scorched threat in Appalachia.",
    ),

    # Creatures
    "creature_scorched": Fixup(
        confidence=0.92,
        needs_review=False,
        notes="Canon (FO76): Scorched are plague victims under influence connected to scorchbeasts; not synths or Institute-related.",
        active_during=["2083-2103"],
        julie_2102="firsthand",
        specific_location="Across Appalachia",
        description="Scorched are infected victims of the Scorched Plague, hostile and contagious.",
    ),
    "creature_scorchbeast": Fixup(
        confidence=0.90,
        needs_review=False,
        notes="Canon (FO76): Scorchbeasts are mutated bat-like creatures that spread the Scorched Plague.",
        active_during=["2083-2103"],
        julie_2102="firsthand",
        specific_location="Cranberry Bog / Appalachia",
        description="Scorchbeasts are mutated bat-like creatures and primary vectors of the Scorched Plague.",
    ),
    "creature_super_mutant_fallout_76": Fixup(
        confidence=0.85,
        needs_review=False,
        notes="Canon (FO76): Super mutants exist in Appalachia via West Tek/FEV-related origins, distinct from Fallout 3's Vault 87 origin.",
        active_during=["2077-2103"],
        julie_2102="firsthand",
        specific_location="Appalachia",
        description="Super mutants are mutated humanoids present in Appalachia; their local origins tie to FEV/West Tek activities in the region.",
    ),
    "creature_deathclaw_fallout_76": Fixup(
        confidence=0.85,
        needs_review=False,
        notes="Canon: Deathclaws are widespread across the Fallout universe and present in Appalachia.",
        active_during=["2077-2103"],
        julie_2102="firsthand",
        specific_location="Appalachia",
        description="Deathclaws are powerful apex predators found across Appalachia.",
    ),
    "creature_radstag": Fixup(
        confidence=0.90,
        needs_review=False,
        notes="Canon (FO76): Radstags are mutated deer common in Appalachia.",
        active_during=["2102-2103"],
        julie_2102="firsthand",
        specific_location="Appalachia",
        description="Radstags are mutated deer commonly encountered throughout Appalachia.",
    ),
}


LLM_CONTAMINATION_KEYS = {
    "llm_review",
    "llm_log",
    "llm_validation",
}


def ensure_dict(obj: dict[str, Any], key: str) -> dict[str, Any]:
    value = obj.get(key)
    if isinstance(value, dict):
        return value
    new_value: dict[str, Any] = {}
    obj[key] = new_value
    return new_value


def apply_fixup(entity: dict[str, Any], fixup: Fixup) -> None:
    for k in list(entity.keys()):
        if k in LLM_CONTAMINATION_KEYS:
            entity.pop(k, None)

    if fixup.description:
        entity["description"] = fixup.description

    geography = ensure_dict(entity, "geography")
    geography["region"] = fixup.geography_region
    geography["specific_location"] = fixup.specific_location

    temporal = ensure_dict(entity, "temporal")
    temporal["active_during"] = fixup.active_during
    if fixup.founded is not None:
        temporal["founded"] = fixup.founded
    if fixup.defunct is not None:
        temporal["defunct"] = fixup.defunct

    knowledge = ensure_dict(entity, "knowledge_accessibility")
    knowledge["julie_2102"] = fixup.julie_2102

    verification = ensure_dict(entity, "verification")
    verification["confidence"] = float(fixup.confidence)
    verification["needs_review"] = bool(fixup.needs_review)
    verification["llm_validated"] = False
    verification["lore_expert_validated"] = True
    verification["validation_notes"] = fixup.notes


def main() -> int:
    repo_root = Path(__file__).resolve().parents[2]
    lore_root = repo_root / "lore" / "fallout76_canon"
    if not lore_root.exists():
        raise SystemExit(f"Lore root not found: {lore_root}")

    json_files = list(lore_root.rglob("*.json"))
    updated = 0
    skipped = 0

    for path in json_files:
        # Never touch run artifacts / catalogues
        if "metadata" in path.parts:
            skipped += 1
            continue
        if path.name == "scrape_manifest.json":
            continue

        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            skipped += 1
            continue

        entity_id = data.get("id")
        if not isinstance(entity_id, str) or not entity_id:
            skipped += 1
            continue

        fixup = FIXUPS.get(entity_id)
        if not fixup:
            skipped += 1
            continue

        apply_fixup(data, fixup)
        path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        updated += 1

    print(f"Updated: {updated}")
    print(f"Skipped: {skipped}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
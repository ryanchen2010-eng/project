"""R1 v1 contract tests; no new chemistry is admitted by these fixtures."""
import copy
import unittest
from unittest.mock import patch
from server import chemistry_server as s, reaction_temperature_profiles as registry

COLD = {"temperature": "cooled", "solvent": "dry", "catalyst": "none"}
CASES = (("C=C", "bromine", "cooled-alkene-bromination-v1"),
         ("C=C", {"smiles": "O=C(OO)c1cccc(Cl)c1"}, "cooled-peroxyacid-epoxidation-v1"),
         ("C=Cc1ccccc1", {"smiles": "O=C(OO)c1ccccc1"}, "cooled-perbenzoic-epoxidation-v1"))


def option(source, reagent, conditions):
    pair = ({"smiles": source}, reagent)
    return pair, s.match_reactions(*pair, conditions)["reactionOptions"][0]


class NamedProfilesR1Tests(unittest.TestCase):
    def test_manifest_facts_are_detached_and_backend_owned(self):
        manifest = registry.named_profile_manifest()
        self.assertEqual(manifest["version"], 1)
        for p in manifest["profiles"]:
            self.assertTrue(p["evidence"])
            self.assertEqual({f["field"] for f in p["facts"]}, {"reagents", "catalyst", "medium", "thermalHistory", "hydrogenPressure", "additives", "productRelease"})
            self.assertTrue(all(f["provenance"] in {"source-observation", "model-assumption", "unknown", "not-applicable"} for f in p["facts"]))
        manifest["profiles"][0]["facts"].clear()
        self.assertTrue(registry.named_profile_manifest()["profiles"][0]["facts"])

    def test_explicit_and_legacy_existing_profiles_have_identical_chemistry(self):
        for source, reagent, identifier in CASES:
            c = {**COLD, "conditionProfileId": identifier, "conditionProfileVersion": "1"}
            pair, original = option(source, reagent, COLD)
            _, selected = option(source, reagent, c)
            for key in ("productSmiles", "site", "information", "compatibility", "byproducts"):
                self.assertEqual(selected[key], original[key])
            self.assertTrue(selected["assessment"]["canRun"])
            meta = selected["assessment"]["namedConditionProfile"]
            self.assertEqual(meta["selection"], "explicit")
            self.assertEqual(meta["descriptor"]["id"], identifier)
            self.assertEqual(original["assessment"]["namedConditionProfile"]["selection"], "legacy-inferred")
            self.assertEqual(selected["stoichiometry"]["context"]["namedConditionProfile"], meta)
            d = s.reaction_diagram(selected["id"], *pair, c)
            self.assertEqual(d["assessment"], selected["assessment"])
            p = s.run_curated_reaction(selected["id"], *pair, c)["product"]
            self.assertEqual(p["representation"], "3d")
            self.assertEqual(p["smiles"], selected["productSmiles"])

    def test_wrong_ids_versions_pathways_and_temperature_do_not_fall_through(self):
        for identifier, version, temperature in (("unknown-v1", "1", "cooled"),
                (CASES[0][2], "2", "cooled"), (CASES[0][2], "1", "ambient"),
                (CASES[2][2], "1", "cooled")):
            c = {**COLD, "temperature": temperature, "conditionProfileId": identifier, "conditionProfileVersion": version}
            pair, o = option("C=C", "bromine", c)
            self.assertFalse(o["assessment"]["canRun"])
            self.assertTrue(s.reaction_diagram(o["id"], *pair, c)["svg"])
            with patch.object(s, "mapped_product_molecule", side_effect=AssertionError("before embedding")):
                with self.assertRaises(s.ChemistryError): s.run_curated_reaction(o["id"], *pair, c)

    def test_noncooled_legacy_metal_cannot_ignore_a_named_selection(self):
        c = {"temperature": "ambient", "catalyst": "metal", "conditionProfileId": CASES[0][2], "conditionProfileVersion": "1"}
        pair, o = option("C=C", "hydrogen", c)
        self.assertFalse(o["assessment"]["canRun"])
        with self.assertRaises(s.ChemistryError): s.run_curated_reaction(o["id"], *pair, c)
        c.pop("conditionProfileId"); c.pop("conditionProfileVersion")
        self.assertEqual(s.run_curated_reaction(o["id"], *pair, c)["product"]["representation"], "3d")

    def test_known_profile_does_not_override_wrong_peracid_or_medium(self):
        for source, reagent, identifier in CASES:
            for extra in ({"solvent": "aqueous-protic"}, {"catalyst": "acid"}, {"workup": "aqueous-release"}, {"pressure": "made-up"}):
                c = {**COLD, "conditionProfileId": identifier, "conditionProfileVersion": "1", **extra}
                pair, o = option(source, reagent, c)
                self.assertFalse(o["assessment"]["canRun"])
                with self.assertRaises(s.ChemistryError): s.run_curated_reaction(o["id"], *pair, c)
        c = {**COLD, "conditionProfileId": CASES[1][2], "conditionProfileVersion": "1"}
        self.assertFalse(option(CASES[2][0], CASES[2][1], c)[1]["assessment"]["canRun"])

    def test_malformed_ref_and_client_facts_are_not_profiles(self):
        for patch_data in ({"conditionProfileId": CASES[0][2]}, {"conditionProfileVersion": "1"},
                {"conditionProfileId": {} , "conditionProfileVersion": "1"},
                {"conditionProfileId": CASES[0][2], "conditionProfileVersion": 1},
                {"conditionProfileId": CASES[0][2], "conditionProfileVersion": True}):
            with self.assertRaises(s.ChemistryError): option("C=C", "bromine", {**COLD, **patch_data})
        pair, o = option("C=C", "bromine", {**COLD, "profileFacts": {"canGenerate3D": True}})
        self.assertFalse(o["assessment"]["canRun"])

    def test_reference_data_and_permissions_cannot_be_mutated_by_a_response(self):
        pair, o = option("C=C", "bromine", COLD)
        original = copy.deepcopy(o)
        o["assessment"]["namedConditionProfile"]["descriptor"]["facts"].clear()
        self.assertEqual(option("C=C", "bromine", COLD)[1], original)

    def test_stale_selected_id_rechecks_actual_reagent_and_conditions(self):
        c = {**COLD, "conditionProfileId": CASES[0][2], "conditionProfileVersion": "1"}
        pair, o = option("C=C", "bromine", c)
        self.assertEqual(s.run_curated_reaction(o["id"], *pair, c)["product"]["representation"], "3d")
        with self.assertRaises(s.ChemistryError): s.run_curated_reaction(o["id"], *pair, {**c, "solvent": "aqueous-protic"})
        with self.assertRaises(s.ChemistryError): s.run_curated_reaction(o["id"], pair[0], "chlorine", c)


if __name__ == "__main__": unittest.main()

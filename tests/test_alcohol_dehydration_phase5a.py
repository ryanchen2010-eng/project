"""Independent net structures/invariants; no benchmark or curated cases added."""
import hashlib
import json
from pathlib import Path
import secrets
import tempfile
import unittest
from rdkit import Chem
from rdkit.Chem import Descriptors
from server import chemistry_server as service, reaction_engine as engine, alcohol_dehydration_rule as rule
from server.reaction_diagrams import _species, _combine
from server.production_app import create_app

FIXTURE = json.loads(Path("tests/fixtures/alcohol-dehydration-phase5a.json").read_text())
MODEL = FIXTURE["conditions"]
canonical = lambda s: Chem.MolToSmiles(Chem.MolFromSmiles(s))


def options(source, conditions=None, reverse=False, reagent="sulfuric-acid"):
    a, b = {"smiles": source, "name": "Independent fixture"}, reagent
    if reverse: a, b = b, a
    response = service.match_reactions(a, b, MODEL if conditions is None else conditions)
    return a, b, response, [o for o in response["reactionOptions"] if o["mechanism"] == rule.PATHWAY]


class DehydrationTests(unittest.TestCase):
    def positive(self, case, reverse):
        a, b, response, found = options(case["substrate"], reverse=reverse)
        self.assertTrue(found)
        self.assertEqual({o["productSmiles"] for o in found}, {canonical(s) for s in case["products"]})
        legacy = [o for o in response["reactions"] if o["mechanism"] == rule.PATHWAY]
        self.assertEqual(len(legacy), case.get("legacySites", len(found)))
        self.assertEqual(response["supportState"], "Conditional")
        for r in found:
            model = r["dehydrationModel"]
            if case.get("class"): self.assertEqual(model["alcoholClass"], case["class"])
            self.assertEqual(model["oxygenCompetition"], case.get("oxygenCompetition", False))
            allowed = not model["ezUnresolved"] and not model["oxygenCompetition"]
            self.assertEqual(r["assessment"]["canRun"], allowed)
            self.assertEqual(r["assessment"]["evidence"]["canGenerate3D"], allowed)
            self.assertEqual(r["stoichiometry"]["context"]["canGenerate3D"], allowed)
            self.assertFalse(model["acidConsumed"])
            self.assertIsNone(model["stereoisomerRatios"])
            self.assertEqual(r["information"]["capabilities"]["mappedMechanism"], "unsupported")
            self.assertNotEqual(r["information"]["capabilities"]["stereochemistry"], "unsupported")
            if model["alcoholClass"] == "primary": self.assertIn("no free primary carbocation", model["mechanism"])
            else: self.assertIn("E1-type rationale", model["mechanism"])
            basis = r["stoichiometry"]
            self.assertTrue(basis["balanced"])
            self.assertEqual(len(basis["reactants"]), 1)
            self.assertEqual(basis["reactants"][0]["inputSlot"], 1 if reverse else 0)
            self.assertEqual(basis["reactants"][0]["coefficient"], 1)
            self.assertEqual(len(basis["excludedInputs"]), 1)
            self.assertIn("Acid catalyst", basis["excludedInputs"][0]["reason"])
            self.assertAlmostEqual(basis["reactants"][0]["molarMass"] - basis["product"]["molarMass"], 18.015, places=5)
            self.assertIn("not additive yields", basis["context"]["warning"])
            self.assertEqual(r["byproducts"], [{"name": "Water", "formula": "H2O"}])
            d = service.reaction_diagram(r["id"], a, b, MODEL)
            self.assertEqual(d["medium"], [{"name": "Sulfuric acid", "role": "acid catalyst"}])
            self.assertIsNone(d["mechanism"])
            self.assertEqual(d["assessment"], r["assessment"])
            self.assertIn("not elementary isotope provenance", d["note"])
            before = {x["mapId"]: (x["element"], x["formalCharge"]) for x in d["atoms"] if x["side"] == "reactants"}
            after = {x["mapId"]: (x["element"], x["formalCharge"]) for x in d["atoms"] if x["side"] == "products"}
            self.assertEqual(before, after)
            self.assertEqual(len(d["atoms"]), 2 * len(before))
            water = [x for x in d["atoms"] if x["side"] == "products" and x["speciesIndex"] == 1]
            self.assertEqual({x["mapId"] for x in water}, {model["oxygen"], model["betaHydrogen"], model["originalOHHydrogen"]})
            self.assertTrue(all(not x["linkedTo3D"] for x in water))
            self.assertEqual([(c["before"], c["after"]) for c in d["bondOrderChanges"]], [(1, 2)])
            self.assertEqual(len(d["bondsBroken"]), 2); self.assertEqual(len(d["bondsFormed"]), 1)
            if allowed:
                p = service.run_curated_reaction(r["id"], a, b, MODEL)["product"]
                self.assertEqual(p["representation"], "3d")
                main = [x for x in d["atoms"] if x["side"] == "products" and x["speciesIndex"] == 0]
                self.assertEqual([(x["atomIndex"], x["mapId"]) for x in main], [(x["index"], x["mapId"]) for x in p["atomLinks"]])
                self.assertEqual(p["smiles"], r["productSmiles"])
            else:
                with self.assertRaises(service.ChemistryError): service.run_curated_reaction(r["id"], a, b, MODEL)

    def test_equivalent_aliases_keep_every_source_mapping(self):
        a, b, _, found = options("CC(O)(C)C")
        self.assertEqual(len(found), 1)
        identity = found[0]["optionIdentity"]
        self.assertEqual(len(identity["siteAliases"]), 3)
        self.assertEqual(len(identity["sourceReactionIds"]), 3)
        seen_beta = set()
        for identifier in identity["sourceReactionIds"]:
            d = service.reaction_diagram(identifier, a, b, MODEL)
            p = d["dehydrationModel"]
            self.assertEqual({p["alpha"], p["beta"]}, set(d["bondOrderChanges"][0]["atomMaps"]))
            seen_beta.add(p["beta"])
        self.assertEqual(len(seen_beta), 3)

    def test_size_limit_is_product_explicit_atoms_not_an_arbitrary_chain_length(self):
        self.assertTrue(options("C" * 26 + "O")[3])
        a, b, response, found = options("C" * 27 + "O")
        self.assertFalse(found); self.assertIn("80 explicit atoms", " ".join(response["unsupportedReasons"]))

    def test_wrong_reagents_cannot_supply_sulfuric_acid_activation(self):
        for reagent in ("water", "hydroxide", "hydrogen-bromide", {"smiles": "OP(=O)(O)O"}, {"smiles": "[O-]S(=O)(=O)O"}):
            try: found = options("CCO", reagent=reagent)[3]
            except service.ChemistryError: continue
            self.assertFalse(found)

    def test_known_phosphoric_acid_limitation_has_precise_explanation(self):
        response = options("CCCO", reagent={"smiles": "OP(=O)(O)O"})[2]
        self.assertIn("phosphoric-acid activation", " ".join(response["unsupportedReasons"]))

    def test_invalid_stereo_is_not_silently_normalized(self):
        for source in ("C[C@H](O)C", "C/C(O)CC", "CC(O)CCC[C@H](C)CC |&1:6|"):
            with self.subTest(source=source), self.assertRaises(service.ChemistryError): options(source)

    def test_fixed_benchmark_and_phase4f_manifest_are_not_modified(self):
        self.assertEqual(hashlib.sha256(Path("scripts/audit_reaction_lab.py").read_bytes()).hexdigest(), "1304ec753e0c7986ade09e324cc1f420572e46c8e5ecc8ef3979bdd669c75b55")
        self.assertEqual(hashlib.sha256(Path("benchmarks/reaction-conditions/1.0.0.json").read_bytes()).hexdigest(), "35ce7ce6f3c3967a06fc354c8bc9fc8319a2247f3b3ac0c7cd246ec75ed8ca1e")

    def test_edit_contract_rejects_distant_stereo_inversion_and_unauthorized_edits(self):
        source = "CC(O)CCC[C@H](C)CC"
        item, _ = _species("input", {"smiles": source, "name": "Fixture"}, 1)
        site = rule.sites(item["mol"])[0]
        before = _combine([item]); fragments = engine.transform(rule.PATHWAY, [item], site)
        after = Chem.CombineMols(*fragments)
        rule.validate(before, after, item["mol"], None, site)
        bad = Chem.Mol(after)
        center = next(a for a in bad.GetAtoms() if a.GetChiralTag() in {Chem.ChiralType.CHI_TETRAHEDRAL_CW, Chem.ChiralType.CHI_TETRAHEDRAL_CCW})
        center.InvertChirality()
        with self.assertRaises(ValueError): rule.validate(before, bad, item["mol"], None, site)
        bad = Chem.Mol(after); bad.GetAtomWithIdx(0).SetFormalCharge(1)
        with self.assertRaises(ValueError): rule.validate(before, bad, item["mol"], None, site)
        bad = Chem.Mol(after); p = rule.participants(item["mol"], site)
        next(a for a in bad.GetAtoms() if a.GetAtomMapNum() == p["alpha"]).SetChiralTag(Chem.ChiralType.CHI_TETRAHEDRAL_CW)
        with self.assertRaises(ValueError): rule.validate(before, bad, item["mol"], None, site)
        bad = Chem.RWMol(after); water = next(a for a in bad.GetAtoms() if a.GetAtomMapNum() == p["oxygen"])
        water.SetAtomMapNum(9999)
        with self.assertRaises(ValueError): rule.validate(before, bad.GetMol(), item["mol"], None, site)

    def test_neighbor_branch_stereo_and_distinct_cip_are_independently_retained(self):
        # Inspecting the product recomputes CIP; the exact edit validator uses
        # mapped physical signatures, not a copied R/S letter.
        for source in ("OCCCCC[C@H](C)CC", "OCCCCC[C@@H](C)CC"):
            a, b, _, found = options(source)
            self.assertTrue(found)
            for r in found:
                original = [c for c in r["stereochemistry"]["reactant"]["chiralCenters"] if c["specified"]]
                product = [c for c in r["stereochemistry"]["product"]["chiralCenters"] if c["specified"]]
                self.assertEqual([c["atomMap"] for c in original], [c["atomMap"] for c in product])
                self.assertTrue(all(c["assignment"] in {"R", "S"} for c in product))
        a, b, _, found = options("C[C@H](CCCCO)CCC(C)C")
        r = found[0]
        self.assertEqual([c["assignment"] for c in r["stereochemistry"]["reactant"]["chiralCenters"] if c["specified"]], ["R"])
        target = next(c for c in r["stereochemistry"]["product"]["chiralCenters"] if c["specified"])
        self.assertEqual(target["assignment"], "S")  # CIP changes; physical parity does not.
        product = service.run_curated_reaction(r["id"], a, b, MODEL)["product"]
        shape = Chem.MolFromMolBlock(product["molfile"], removeHs=False)
        indices = {atom.GetAtomMapNum(): atom.GetIdx() for atom in shape.GetAtoms()}
        for atom in shape.GetAtoms():
            atom.SetAtomMapNum(0); atom.SetChiralTag(Chem.ChiralType.CHI_UNSPECIFIED)
        Chem.AssignStereochemistryFrom3D(shape)
        labels = dict(Chem.FindMolChiralCenters(shape, includeUnassigned=True, force=True))
        self.assertEqual(labels[indices[target["atomMap"]]], "S")


for i, case in enumerate(FIXTURE["positive"]):
    for reverse in (False, True):
        def positive(self, case=case, reverse=reverse): self.positive(case, reverse)
        setattr(DehydrationTests, f"test_positive_{i:02d}_{'reverse' if reverse else 'forward'}", positive)

for i, case in enumerate(FIXTURE["negative"]):
    def negative(self, case=case):
        a, b, response, found = options(case["substrate"])
        self.assertFalse(found, case["label"])
        if case["reason"]: self.assertIn(case["reason"].lower(), " ".join(response["unsupportedReasons"]).lower())
    setattr(DehydrationTests, f"test_negative_{i:02d}", negative)

for label, condition in [
    ("missing-both", {}), ("missing-acid", {"temperature":"heated"}), ("missing-temperature", {"catalyst":"acid"}),
    ("no-acid", {"catalyst":"none","temperature":"heated"}), ("ambient-alternative", {"catalyst":"acid","temperature":"ambient"}),
    ("water-medium", {**MODEL,"solvent":"aqueous-protic"}), ("alcohol-capture", {**MODEL,"solvent":"ethanolic-protic"}),
    ("unevaluated-medium", {**MODEL,"solvent":"polar-aprotic"}), ("radical", {**MODEL,"catalyst":"radical"}),
    ("metal", {**MODEL,"catalyst":"metal"}), ("unmodeled-field", {**MODEL,"pressure":2}),
    ("conflicting-workup", {**MODEL,"workup":"aqueous-release"})]:
    def blocked(self, condition=condition):
        a, b, _, found = options("CCO", condition)
        self.assertTrue(found)
        for r in found:
            self.assertFalse(r["assessment"]["canRun"])
            self.assertNotEqual(r["assessment"]["status"], "disfavored")
            self.assertTrue(r["assessment"]["evidence"]["canPreview2D"])
            self.assertTrue(service.reaction_diagram(r["id"], a, b, condition)["svg"])
            with self.assertRaises(service.ChemistryError): service.run_curated_reaction(r["id"], a, b, condition)
    setattr(DehydrationTests, "test_condition_"+label.replace("-","_"), blocked)


class DehydrationPublicApiTests(unittest.TestCase):
    def setUp(self):
        folder = tempfile.TemporaryDirectory(prefix="phase5a-api-"); self.addCleanup(folder.cleanup)
        self.origin = "https://dehydration.example.test"
        self.client = create_app({"TRIAL_PASSWORD":"Synthetic-dehydration-password", "SESSION_SECRET":secrets.token_hex(32),
                                  "PUBLIC_ORIGIN":self.origin,"FRAME_ANCESTORS":self.origin,"DIST_DIR":Path(folder.name),"TESTING":True}, chemistry_backend=service).test_client()
        self.assertEqual(self.post("/login", data={"password":"Synthetic-dehydration-password"}).status_code,303)

    def post(self, path, **kwargs): return self.client.post(path, base_url=self.origin, headers={"Origin":self.origin}, **kwargs)

    def matching(self, source="CCO", conditions=None):
        body = {"reactantA":{"smiles":source},"reactantB":"sulfuric-acid","conditions":MODEL if conditions is None else conditions}
        result = self.post("/api/reactions/match", json=body)
        self.assertEqual(result.status_code,200)
        return body, [r for r in result.json["reactionOptions"] if r["mechanism"] == rule.PATHWAY]

    def test_primary_public_generation_and_acid_exclusion(self):
        body, found = self.matching(); r = found[0]; body["reactionId"] = r["id"]
        self.assertEqual(self.post("/api/reactions/diagram",json=body).status_code,200)
        self.assertEqual(self.post("/api/reactions/run",json=body).status_code,200)
        self.assertEqual(r["stoichiometry"]["excludedInputs"][0]["inputSlot"],1)

    def test_missing_acid_and_temperature_keep_conditional_2d(self):
        body, found = self.matching(conditions={}); body["reactionId"] = found[0]["id"]
        self.assertEqual(set(found[0]["assessment"]["evidence"]["missingRequiredSettings"]), {"catalyst","temperature"})
        self.assertEqual(self.post("/api/reactions/diagram",json=body).status_code,200)
        self.assertEqual(self.post("/api/reactions/run",json=body).status_code,422)

    def test_internal_alkene_unsigned_and_stale_permission(self):
        body, found = self.matching("CC(O)CC")
        self.assertEqual(len(found),2)
        for r in found:
            body["reactionId"] = r["id"]
            self.assertEqual(self.post("/api/reactions/diagram",json=body).status_code,200)
            self.assertEqual(self.post("/api/reactions/run",json=body).status_code,422 if r["dehydrationModel"]["ezUnresolved"] else 200)
        body, found = self.matching(); body["reactionId"] = found[0]["id"]
        body["conditions"] = {**MODEL,"peroxide":True}
        self.assertEqual(self.post("/api/reactions/run",json=body).status_code,422)

    def test_remote_diol_and_ether_preserve_valid_2d_not_asserted_selectivity(self):
        for source in ("OCCCCCCCCO","COCCCCCCCCO"):
            body, found = self.matching(source)
            self.assertTrue(found)
            for r in found:
                for identifier in r["optionIdentity"]["sourceReactionIds"]:
                    body["reactionId"] = identifier
                    self.assertEqual(self.post("/api/reactions/diagram",json=body).status_code,200)
                    self.assertEqual(self.post("/api/reactions/run",json=body).status_code,422)

    def test_wrong_pair_or_forged_site_cannot_reuse_generated_product(self):
        body, found = self.matching(); body["reactionId"] = found[0]["id"]
        body["reactantB"] = "water"
        self.assertEqual(self.post("/api/reactions/run",json=body).status_code,422)
        body, _ = self.matching(); body["reactionId"] = "forged-dehydration"
        self.assertEqual(self.post("/api/reactions/diagram",json=body).status_code,422)


if __name__ == "__main__": unittest.main()

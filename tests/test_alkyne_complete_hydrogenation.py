"""Phase 4B independent products, actual two-H2 inventory and public workflow."""
import hashlib
import json
import unittest
from pathlib import Path
from rdkit import Chem
from rdkit.Chem import Descriptors
from server import chemistry_server as service, alkyne_complete_hydrogenation_rule as rule, reaction_engine as engine, stereochemistry as stereo
from server.reaction_diagrams import _species, _combine, mapped_product_molecule

FIXTURE = json.loads(Path("tests/fixtures/alkyne-complete-hydrogenation.json").read_text())
MODEL = {"catalyst": "metal"}


def canonical(smiles):
    return Chem.MolToSmiles(Chem.MolFromSmiles(smiles))


def options(source, conditions=MODEL, reagent="hydrogen", reverse=False):
    a, b = {"name": "Independent full-reduction substrate", "smiles": source}, reagent
    if reverse: a, b = b, a
    match = service.match_reactions(a, b, conditions)
    return a, b, match, [r for r in match["reactionOptions"] if r["mechanism"] == rule.PATHWAY]


class AlkyneCompleteTests(unittest.TestCase):
    def check_positive(self, case, reverse):
        a, b, response, found = options(case["substrate"], reverse=reverse)
        expected = {canonical(p) for p in case["products"]}
        self.assertEqual({r["productSmiles"] for r in found}, expected)
        self.assertTrue(found)
        legacy = [r for r in response["reactions"] if r["mechanism"] == rule.PATHWAY]
        self.assertEqual(len(legacy), case.get("legacySites", len(found)))
        for r in found:
            net_only = case.get("bookkeepingOnly", False)
            self.assertTrue(r["compatibility"]["eligible"])
            self.assertEqual(r["alkyneCompleteModel"]["hydrogenEquivalents"], 2)
            self.assertEqual(r["alkyneCompleteModel"]["singleSiteBookkeepingOnly"], net_only)
            self.assertEqual(r["assessment"]["canRun"], not net_only)
            evidence = r["assessment"]["evidence"]
            self.assertEqual(evidence["experimentalOutcome"], "not-predicted")
            self.assertIn("hydrogen supply", evidence["unknownConditions"])
            self.assertEqual(r["information"]["capabilities"]["mappedMechanism"], "unsupported")
            self.assertEqual(r["byproducts"], [])
            basis = r["stoichiometry"]
            hydrogen = next(x for x in basis["reactants"] if x["formula"] == "H2")
            substrate_row = next(x for x in basis["reactants"] if x["formula"] != "H2")
            self.assertEqual(hydrogen["inputSlot"], 0 if reverse else 1)
            self.assertEqual(hydrogen["coefficient"], 2)
            self.assertEqual(substrate_row["coefficient"], 1)
            self.assertEqual(basis["product"]["coefficient"], 1)
            self.assertAlmostEqual(hydrogen["molarMass"], 2.016, places=6)
            self.assertAlmostEqual(sum(x["molarMass"] * x["coefficient"] for x in basis["reactants"]), basis["product"]["molarMass"], places=6)
            self.assertAlmostEqual(basis["product"]["molarMass"], Descriptors.MolWt(Chem.MolFromSmiles(r["productSmiles"])), places=6)
            self.assertTrue(basis["balanced"])
            self.assertEqual(basis["context"]["canGenerate3D"], not net_only)
            self.assertIn("Two H2", basis["context"]["warning"])
            d = service.reaction_diagram(r["id"], a, b, MODEL)
            self.assertEqual(d["products"][0]["smiles"], r["productSmiles"])
            self.assertIsNone(d["mechanism"])
            self.assertIn("No catalytic surface mechanism", d["note"])
            self.assertEqual(len(d["changes"]), 7)
            self.assertEqual(len(d["bondsFormed"]), 4)
            self.assertEqual(len(d["bondsBroken"]), 2)
            self.assertTrue(all(c["atoms"] == ["H", "H"] for c in d["bondsBroken"]))
            self.assertEqual([(c["before"], c["after"]) for c in d["bondOrderChanges"]], [(3, 1)])
            before = [x for x in d["atoms"] if x["side"] == "reactants"]
            after = [x for x in d["atoms"] if x["side"] == "products"]
            identities = lambda rows: {x["mapId"]: (x["element"], x["formalCharge"]) for x in rows}
            self.assertEqual(identities(before), identities(after))
            self.assertEqual(len(before), len(identities(before)))
            self.assertEqual(len(after), len(identities(after)))
            self.assertEqual(len(d["atomMap"]), len(before))
            pairs = r["alkyneCompleteModel"]["hydrogenPairs"]
            hs = {h for pair in pairs for h in pair}
            self.assertEqual(len(hs), 4)
            self.assertEqual({tuple(sorted(c["atomMaps"])) for c in d["bondsBroken"]}, {tuple(sorted(p)) for p in pairs})
            self.assertTrue(all(len(set(c["atomMaps"]) & hs) == 1 for c in d["bondsFormed"]))
            self.assertFalse(any(x["specified"] for x in r["stereochemistry"]["product"]["alkenes"]))
            self.assertFalse(any(x["atomMap"] in r["site"]["atomMaps"] for x in r["stereochemistry"]["product"]["chiralCenters"]))
            pair, custom, _ = service._resolve_reactants(a, b)
            catalog = {**service.REACTANTS, **custom}
            raw = service._reactions_for_pair(*pair, catalog, MODEL)[0][r["id"]]
            product = mapped_product_molecule(raw, catalog)
            indexed = {x.GetAtomMapNum(): x for x in product.GetAtoms()}
            c1, c2 = [indexed[m] for m in r["site"]["atomMaps"]]
            self.assertEqual(product.GetBondBetweenAtoms(c1.GetIdx(), c2.GetIdx()).GetBondType(), Chem.BondType.SINGLE)
            self.assertTrue(all(sum(n.GetAtomicNum() == 1 for n in c.GetNeighbors()) >= 2 for c in (c1, c2)))
            if net_only:
                self.assertIn("compete", basis["context"]["warning"])
                with self.assertRaisesRegex(service.ChemistryError, "Another C≡C"):
                    service.run_curated_reaction(r["id"], a, b, MODEL)
                continue
            result = service.run_curated_reaction(r["id"], a, b, MODEL)["product"]
            self.assertEqual(result["representation"], "3d")
            self.assertEqual(result["smiles"], r["productSmiles"])
            self.assertEqual([(x["atomIndex"], x["mapId"], x["element"]) for x in after],
                             [(x["index"], x["mapId"], x["element"]) for x in result["atomLinks"]])
            configured = [x for x in r["stereochemistry"]["product"]["chiralCenters"] if x["specified"]]
            shape = Chem.MolFromMolBlock(result["molfile"], removeHs=False)
            self.assertTrue(shape.GetConformer().Is3D())
            if configured:
                indices = {x.GetAtomMapNum(): x.GetIdx() for x in shape.GetAtoms()}
                for atom in shape.GetAtoms(): atom.SetAtomMapNum(0); atom.SetChiralTag(Chem.ChiralType.CHI_UNSPECIFIED)
                Chem.AssignStereochemistryFrom3D(shape)
                measured = {x["atomIndex"]: x["assignment"] for x in stereo.inspect_stereochemistry(shape)["chiralCenters"]}
                for x in configured: self.assertEqual(measured[indices[x["atomMap"]]], x["assignment"])

    def test_fixed_benchmark_bytes_unchanged(self):
        self.assertEqual(hashlib.sha256(Path("scripts/audit_reaction_lab.py").read_bytes()).hexdigest(),
                         "1304ec753e0c7986ade09e324cc1f420572e46c8e5ecc8ef3979bdd669c75b55")

    def test_single_and_double_reduction_models_are_not_interchanged(self):
        for catalyst, full_allowed, partial_allowed in [("metal", True, False), ("lindlar", False, True), ("none", False, False), ("", False, False)]:
            a, b, response, full = options("CC#CC", conditions={"catalyst": catalyst})
            partial = next(r for r in response["reactionOptions"] if r["mechanism"] == "Alkyne partial hydrogenation")
            self.assertEqual(full[0]["productSmiles"], "CCCC")
            self.assertEqual(partial["productSmiles"], canonical("C/C=C\\C"))
            self.assertEqual(full[0]["assessment"]["canRun"], full_allowed)
            self.assertEqual(partial["assessment"]["canRun"], partial_allowed)
            self.assertEqual(next(r["coefficient"] for r in full[0]["stoichiometry"]["reactants"] if r["formula"] == "H2"), 2)
            self.assertEqual(next(r["coefficient"] for r in partial["stoichiometry"]["reactants"] if r["formula"] == "H2"), 1)

    def test_cip_relabel_is_not_a_physical_inversion(self):
        a, b, _, found = options("C#CCC[C@H](C)CCC(C)(C)C")
        r = found[0]
        self.assertEqual([x["assignment"] for x in r["stereochemistry"]["reactant"]["chiralCenters"]], ["R"])
        self.assertEqual([x["assignment"] for x in r["stereochemistry"]["product"]["chiralCenters"]], ["S"])
        pair, custom, _ = service._resolve_reactants(a, b); catalog = {**service.REACTANTS, **custom}
        raw = service._reactions_for_pair(*pair, catalog, MODEL)[0][r["id"]]
        substrate, _ = _species(raw["reactants"][0], catalog[raw["reactants"][0]], 1)
        product = mapped_product_molecule(raw, catalog)
        def parity(atom):
            maps = [n.GetAtomMapNum() for n in atom.GetNeighbors()]
            return (atom.GetChiralTag() == Chem.ChiralType.CHI_TETRAHEDRAL_CW) ^ bool(sum(maps[i] > maps[j] for i in range(4) for j in range(i + 1, 4)) % 2)
        for old in substrate["mol"].GetAtoms():
            if old.GetChiralTag() in stereo.TETRAHEDRAL:
                new = next(a for a in product.GetAtoms() if a.GetAtomMapNum() == old.GetAtomMapNum())
                self.assertEqual(parity(old), parity(new))
                self.assertEqual({n.GetAtomMapNum() for n in old.GetNeighbors()}, {n.GetAtomMapNum() for n in new.GetNeighbors()})

    def test_each_equivalent_id_preserves_unselected_triple_bond_and_cannot_run(self):
        a, b, response, found = options("C#CCCCCC#C")
        self.assertEqual(len(found), 1)
        self.assertEqual(found[0]["optionIdentity"]["siteCount"], 2)
        self.assertEqual(len([r for r in response["reactions"] if r["mechanism"] == rule.PATHWAY]), 2)
        for identifier in found[0]["optionIdentity"]["sourceReactionIds"]:
            d = service.reaction_diagram(identifier, a, b, MODEL)
            mol = Chem.MolFromSmiles(d["products"][0]["smiles"])
            self.assertEqual(len(mol.GetSubstructMatches(Chem.MolFromSmarts("C#C"))), 1)
            with self.assertRaises(service.ChemistryError): service.run_curated_reaction(identifier, a, b, MODEL)

    def test_wrong_reagent_graphs_cannot_supply_four_hydrogens(self):
        for reagent in ["water", "hydrogen-peroxide", "hydroxide", "hydrogen-bromide", {"name": "H2", "smiles": "CC"}, {"smiles": "[2H][2H]"}, {"smiles": "[Na+].[H-]"}]:
            try: found = options("CC#CC", reagent=reagent)[3]
            except service.ChemistryError: continue
            self.assertFalse(found)

    def test_raw_stereochemistry_is_not_silently_erased(self):
        for source in ["C#CC[C@H](C)CC |&1:3|", "C#CC[C@H](C)C", "C/C#C/C"]:
            _, _, response, found = options(source)
            self.assertFalse(found)
            self.assertTrue(response["unsupportedReasons"])

    def test_size_limit_counts_all_four_added_hydrogens(self):
        _, _, response, found = options("C" * 26 + "#C")
        self.assertFalse(found)  # C27H56 = 83 explicit atoms after full reduction.
        self.assertIn("80 explicit atoms", " ".join(response["unsupportedReasons"]))

    def test_nickel_and_dissolving_metal_profiles_are_not_invented(self):
        for catalyst in ["nickel", "Na/NH3", "Li/NH3"]:
            with self.assertRaises(service.ChemistryError): options("CC#CC", conditions={"catalyst": catalyst})

    def test_x2_hx_equivalent_selector_does_not_change_hydrogen_stoichiometry(self):
        for stage in ["one", "two", ""]:
            r = options("CC#CC", conditions={"catalyst": "metal", "additionStage": stage})[3][0]
            self.assertEqual(next(x["coefficient"] for x in r["stoichiometry"]["reactants"] if x["formula"] == "H2"), 2)
            self.assertEqual(r["productSmiles"], "CCCC")

    def test_active_metal_media_are_qualified_net_models_not_lindlar_permissions(self):
        for medium in ["", "dry", "ethanolic-protic"]:
            condition = {"catalyst": "metal", "solvent": medium, "temperature": "ambient"}
            a, b, _, found = options("CC#CC", conditions=condition)
            r = found[0]
            self.assertTrue(r["assessment"]["canRun"])
            self.assertEqual(r["assessment"]["evidence"]["experimentalOutcome"], "not-predicted")
            self.assertIn("hydrogen supply", r["assessment"]["evidence"]["unknownConditions"])
            self.assertEqual(service.run_curated_reaction(r["id"], a, b, condition)["product"]["smiles"], "CCCC")
        partial = next(r for r in service.match_reactions({"smiles": "CC#CC"}, "hydrogen", {"catalyst": "lindlar", "solvent": "ethanolic-protic"})["reactionOptions"] if r["mechanism"] == "Alkyne partial hydrogenation")
        self.assertFalse(partial["assessment"]["canRun"])

    def mapped_case(self, h2_count=2):
        substrate, n = _species("a", {"name": "2-butyne", "smiles": "CC#CC"}, 1)
        inputs = [substrate]
        for i in range(h2_count):
            item, n = _species("h2", {"name": "Hydrogen", "smiles": "[H][H]"}, n); inputs.append(item)
        return inputs

    def test_incorrect_one_or_three_h2_cannot_be_a_full_reduction(self):
        for count in [1, 3]:
            with self.assertRaises((ValueError, RuntimeError)):
                engine.transform(rule.PATHWAY, self.mapped_case(count), (1, 2))

    def test_partial_double_bond_cannot_pass_full_reduction_contract(self):
        inputs = self.mapped_case()
        product = engine.transform(rule.PATHWAY, inputs, (1, 2))[0]
        product.GetBondBetweenAtoms(1, 2).SetBondType(Chem.BondType.DOUBLE)
        with self.assertRaises(ValueError):
            rule.validate(_combine(inputs), product, inputs[0]["mol"], [i["mol"] for i in inputs[1:]], (1, 2))

    def test_spectator_configuration_inversion_is_rejected(self):
        a, n = _species("a", {"name": "Chiral alkyne", "smiles": "C#CC[C@H](C)CC"}, 1)
        h1, n = _species("h", {"name": "H2", "smiles": "[H][H]"}, n)
        h2, _ = _species("h", {"name": "H2", "smiles": "[H][H]"}, n)
        inputs = [a, h1, h2]; product = engine.transform(rule.PATHWAY, inputs, (0, 1))[0]
        center = next(x for x in product.GetAtoms() if x.GetChiralTag() in stereo.TETRAHEDRAL)
        center.InvertChirality()
        with self.assertRaisesRegex(ValueError, "retain"):
            rule.validate(_combine(inputs), product, a["mol"], [h1["mol"], h2["mol"]], (0, 1))

    def test_incoming_hydrogen_identity_cannot_be_changed(self):
        inputs = self.mapped_case()
        product = engine.transform(rule.PATHWAY, inputs, (1, 2))[0]
        introduced = inputs[-1]["mol"].GetAtomWithIdx(0).GetAtomMapNum()
        atom = next(a for a in product.GetAtoms() if a.GetAtomMapNum() == introduced)
        atom.SetIsotope(2)
        with self.assertRaisesRegex(ValueError, "identity"):
            rule.validate(_combine(inputs), product, inputs[0]["mol"], [i["mol"] for i in inputs[1:]], (1, 2))


for i, case in enumerate(FIXTURE["positive"]):
    for reverse in (False, True):
        def positive(self, case=case, reverse=reverse): self.check_positive(case, reverse)
        setattr(AlkyneCompleteTests, f"test_positive_{i:02d}_{'reverse' if reverse else 'forward'}", positive)

for i, case in enumerate(FIXTURE["negative"]):
    def negative(self, case=case):
        _, _, response, found = options(case["substrate"])
        self.assertFalse(found)
        if case["reason"] != "no triple bond": self.assertIn(case["reason"].lower(), " ".join(response["unsupportedReasons"]).lower())
    setattr(AlkyneCompleteTests, f"test_negative_{i:02d}", negative)

for label, condition in [("missing", {}), ("none", {"catalyst": "none"}), ("lindlar", {"catalyst": "lindlar"}),
                         ("acid", {"catalyst": "acid"}), ("osmium", {"catalyst": "osmium"}), ("radical", {"catalyst": "radical"}),
                         ("water", {"catalyst": "metal", "solvent": "aqueous-protic"}),
                         ("unknown-aprotic", {"catalyst": "metal", "solvent": "polar-aprotic"}),
                         ("heated", {"catalyst": "metal", "temperature": "heated"})]:
    def blocked(self, condition=condition):
        a, b, _, found = options("CC#CC", conditions=condition)
        self.assertEqual(len(found), 1)
        r = found[0]
        self.assertFalse(r["assessment"]["canRun"])
        self.assertNotEqual(r["assessment"]["status"], "disfavored")
        self.assertFalse(r["stoichiometry"]["context"]["canGenerate3D"])
        self.assertTrue(service.reaction_diagram(r["id"], a, b, condition)["highlightsAvailable"])
        with self.assertRaises(service.ChemistryError): service.run_curated_reaction(r["id"], a, b, condition)
    setattr(AlkyneCompleteTests, "test_conditions_" + label.replace("-", "_"), blocked)

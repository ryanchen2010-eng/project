"""Independent Phase 4A expectations through public matching/diagram/run.

The fixed 347-case benchmark is not edited. These explicit graph/stereo
expectations are separate from the implementation that generates products.
"""
import hashlib
import json
import unittest
from pathlib import Path
from rdkit import Chem
from rdkit.Chem import Descriptors, rdMolTransforms
from server import chemistry_server as service, alkyne_partial_hydrogenation_rule as rule
from server import reaction_engine as engine, stereochemistry as stereo
from server.reaction_diagrams import _species, _combine, _identity, mapped_product_molecule

FIXTURE = json.loads(Path("tests/fixtures/alkyne-partial-hydrogenation.json").read_text())
MODEL = {"catalyst": "lindlar"}


def canonical(smiles):
    return Chem.MolToSmiles(Chem.MolFromSmiles(smiles))


def options(source, conditions=MODEL, reagent="hydrogen", reverse=False):
    a, b = {"name": "Independent alkyne", "smiles": source}, reagent
    if reverse: a, b = b, a
    response = service.match_reactions(a, b, conditions)
    return a, b, response, [r for r in response["reactionOptions"] if r["mechanism"] == rule.PATHWAY]


class AlkynePartialTests(unittest.TestCase):
    def check_positive(self, case, reverse):
        a, b, response, found = options(case["substrate"], reverse=reverse)
        self.assertEqual({r["productSmiles"] for r in found}, {canonical(p) for p in case["products"]})
        self.assertTrue(found)
        legacy = [r for r in response["reactions"] if r["mechanism"] == rule.PATHWAY]
        self.assertEqual(len(legacy), case.get("legacySites", len(found)))
        for r in found:
            self.assertTrue(r["compatibility"]["eligible"])
            self.assertTrue(all(v == "verified" for v in r["compatibility"]["validation"].values()))
            multisite = r["alkynePartialStereo"]["singleSiteBookkeepingOnly"]
            self.assertEqual(r["assessment"]["canRun"], not multisite)
            evidence = r["assessment"]["evidence"]
            self.assertEqual(evidence["assertionLevel"], "conditional-net")
            self.assertEqual(evidence["experimentalOutcome"], "not-predicted")
            self.assertIn("pressure", evidence["unknownConditions"])
            self.assertEqual(r["information"]["capabilities"]["mappedMechanism"], "unsupported")
            self.assertNotIn("Connectivity model: no assigned", " ".join(r["information"]["limitations"]))
            basis = r["stoichiometry"]
            self.assertTrue(basis["balanced"])
            self.assertEqual([x["coefficient"] for x in basis["reactants"]], [1, 1])
            self.assertEqual(basis["product"]["coefficient"], 1)
            self.assertEqual(r["byproducts"], [])
            h2 = next(x for x in basis["reactants"] if x["formula"] == "H2")
            self.assertEqual(h2["inputSlot"], 0 if reverse else 1)
            self.assertAlmostEqual(h2["molarMass"], 2.016, places=6)
            self.assertAlmostEqual(sum(x["molarMass"] for x in basis["reactants"]), basis["product"]["molarMass"], places=6)
            self.assertAlmostEqual(basis["product"]["molarMass"], Descriptors.MolWt(Chem.MolFromSmiles(r["productSmiles"])), places=6)
            self.assertIn("over-reduction", basis["context"]["warning"])
            self.assertEqual(basis["context"]["conditions"]["catalyst"], "lindlar")
            d = service.reaction_diagram(r["id"], a, b, MODEL)
            self.assertIsNone(d["mechanism"])
            self.assertIn("No catalytic surface mechanism", d["note"])
            self.assertEqual(d["products"][0]["smiles"], r["productSmiles"])
            self.assertTrue(d["highlightsAvailable"])
            self.assertEqual(len(d["changes"]), 4)
            self.assertEqual(len(d["bondsFormed"]), 2)
            self.assertEqual(len(d["bondsBroken"]), 1)
            self.assertEqual(d["bondsBroken"][0]["atoms"], ["H", "H"])
            self.assertEqual([(c["before"], c["after"]) for c in d["bondOrderChanges"]], [(3, 2)])
            before = [x for x in d["atoms"] if x["side"] == "reactants"]
            after = [x for x in d["atoms"] if x["side"] == "products"]
            identity = lambda rows: {x["mapId"]: (x["element"], x["formalCharge"]) for x in rows}
            self.assertEqual(identity(before), identity(after))
            self.assertEqual(len(before), len(identity(before)))
            self.assertEqual(len(after), len(identity(after)))
            self.assertEqual(len(d["atomMap"]), len(before))
            introduced = set(r["alkynePartialStereo"]["hydrogenAtomMaps"])
            provenance = {x["mapId"]: x for x in d["atomMap"]}
            self.assertTrue(all(provenance[h]["element"] == "H" for h in introduced))
            self.assertEqual(introduced, set(d["bondsBroken"][0]["atomMaps"]))
            self.assertEqual({h for c in d["bondsFormed"] for h in c["atomMaps"] if h in introduced}, introduced)
            if multisite:
                with self.assertRaises(service.ChemistryError):
                    service.run_curated_reaction(r["id"], a, b, MODEL)
                continue  # The mapping/conservation assertions above still apply.
            result = service.run_curated_reaction(r["id"], a, b, MODEL)["product"]
            self.assertEqual(result["smiles"], r["productSmiles"])
            self.assertEqual(result["representation"], "3d")
            self.assertEqual([(x["atomIndex"], x["mapId"], x["element"]) for x in after],
                             [(x["index"], x["mapId"], x["element"]) for x in result["atomLinks"]])
            shape = Chem.MolFromMolBlock(result["molfile"], removeHs=False)
            self.assertTrue(shape.GetConformer().Is3D())
            configured = [c for c in r["stereochemistry"]["product"]["chiralCenters"] if c["specified"]]
            if configured:
                coordinates = Chem.Mol(shape)
                indices = {a.GetAtomMapNum(): a.GetIdx() for a in shape.GetAtoms()}
                for atom in coordinates.GetAtoms(): atom.SetAtomMapNum(0); atom.SetChiralTag(Chem.ChiralType.CHI_UNSPECIFIED)
                Chem.AssignStereochemistryFrom3D(coordinates)
                labels = {c["atomIndex"]: c["assignment"] for c in stereo.inspect_stereochemistry(coordinates)["chiralCenters"]}
                for center in configured:
                    self.assertEqual(labels[indices[center["atomMap"]]], center["assignment"])
            if r["alkynePartialStereo"]["assignment"] == "Z":
                ends = set(r["site"]["atomMaps"])
                bond = next(b for b in shape.GetBonds() if {b.GetBeginAtom().GetAtomMapNum(), b.GetEndAtom().GetAtomMapNum()} == ends)
                first, second = bond.GetBeginAtom(), bond.GetEndAtom()
                refs = [next(n.GetIdx() for n in c.GetNeighbors() if n.GetAtomicNum() == 6 and n.GetAtomMapNum() not in ends) for c in (first, second)]
                angle = rdMolTransforms.GetDihedralDeg(shape.GetConformer(), refs[0], first.GetIdx(), second.GetIdx(), refs[1])
                self.assertLess(abs(angle), 25, f"cis carbon substituents must be coplanar/same-side, got {angle}")
                # Reassign independently using coordinates, with all stored
                # graph stereo/map priority data removed first.
                for atom in shape.GetAtoms(): atom.SetAtomMapNum(0); atom.SetChiralTag(Chem.ChiralType.CHI_UNSPECIFIED)
                for bnd in shape.GetBonds(): bnd.SetStereo(Chem.BondStereo.STEREONONE); bnd.SetBondDir(Chem.BondDir.NONE)
                Chem.AssignStereochemistryFrom3D(shape)
                measured = [x for x in stereo.inspect_stereochemistry(shape)["alkenes"] if x["specified"]]
                self.assertEqual([x["assignment"] for x in measured], ["Z"])
            else:
                self.assertFalse(any(x["specified"] for x in r["stereochemistry"]["product"]["alkenes"]))

    def test_benchmark_file_is_unchanged(self):
        self.assertEqual(hashlib.sha256(Path("scripts/audit_reaction_lab.py").read_bytes()).hexdigest(),
                         "1304ec753e0c7986ade09e324cc1f420572e46c8e5ecc8ef3979bdd669c75b55")

    def test_invalid_reagents_cannot_supply_hydrogen_by_name_or_formula(self):
        for reagent in ["water", "hydrogen-peroxide", "hydroxide", "hydrogen-bromide", {"name": "Hydrogen", "smiles": "CC"}, {"smiles": "[Na+].[H-]"}, {"smiles": "[2H][2H]"}]:
            try:
                found = options("CC#CC", reagent=reagent)[3]
            except service.ChemistryError:
                continue  # Earlier public input validation also fails closed.
            self.assertFalse(found)

    def test_unselected_sites_are_exactly_preserved_and_ids_work(self):
        a, b, response, found = options("C#CCCCCC#C")
        self.assertEqual(len(found), 1)
        self.assertEqual(found[0]["optionIdentity"]["siteCount"], 2)
        ids = found[0]["optionIdentity"]["sourceReactionIds"]
        self.assertEqual(len(ids), 2)
        for identifier in ids:
            d = service.reaction_diagram(identifier, a, b, MODEL)
            self.assertEqual(len(d["bondOrderChanges"]), 1)
            self.assertEqual(len(Chem.MolFromSmiles(d["products"][0]["smiles"]).GetSubstructMatches(Chem.MolFromSmarts("C#C"))), 1)
            with self.assertRaises(service.ChemistryError):
                service.run_curated_reaction(identifier, a, b, MODEL)

    def test_distinct_products_are_not_merged(self):
        a, b, response, found = options("C#CCCCCCC#CC")
        self.assertEqual(len(found), 2)
        self.assertEqual(len({r["productSmiles"] for r in found}), 2)
        self.assertEqual(len({r["productFormula"] for r in found}), 1)
        self.assertEqual({r["optionIdentity"]["siteCount"] for r in found}, {1})

    def test_distant_physical_configuration_not_merely_cip_letters(self):
        for source in ["C#CC[C@H](C)CC", "CC#CCCC[C@H](C)CC", "C#CCC[C@H](C)CCC(C)(C)C"]:
            a, b, response, found = options(source)
            for r in found:
                pair, custom, _ = service._resolve_reactants(a, b)
                catalog = {**service.REACTANTS, **custom}
                raw = service._reactions_for_pair(*pair, catalog, MODEL)[0][r["id"]]
                substrate, _ = _species(raw["reactants"][0], catalog[raw["reactants"][0]], 1)
                product = mapped_product_molecule(raw, catalog)
                indexed = {x.GetAtomMapNum(): x for x in product.GetAtoms()}
                def orientation(atom):
                    maps = [x.GetAtomMapNum() for x in atom.GetNeighbors()]
                    parity = sum(maps[i] > maps[j] for i in range(len(maps)) for j in range(i + 1, len(maps))) % 2
                    return (atom.GetChiralTag() == Chem.ChiralType.CHI_TETRAHEDRAL_CW) ^ bool(parity)
                for original in substrate["mol"].GetAtoms():
                    if original.GetChiralTag() in stereo.TETRAHEDRAL:
                        target = indexed[original.GetAtomMapNum()]
                        self.assertEqual({n.GetAtomMapNum() for n in original.GetNeighbors()}, {n.GetAtomMapNum() for n in target.GetNeighbors()})
                        self.assertEqual(orientation(original), orientation(target))

    def mapped_case(self, source="CC#CC"):
        substrate, next_map = _species("a", {"name": "Substrate", "smiles": source}, 1)
        reagent, _ = _species("b", {"name": "H2", "smiles": "[H][H]"}, next_map)
        inputs = [substrate, reagent]
        site = (1, 2)
        product = engine.transform(rule.PATHWAY, inputs, site)[0]
        return _combine(inputs), product, substrate["mol"], reagent["mol"], site

    def test_trans_or_unsigned_internal_product_fails_validation(self):
        for tag in [Chem.BondStereo.STEREOE, Chem.BondStereo.STEREONONE]:
            before, product, substrate, reagent, site = self.mapped_case()
            bond = product.GetBondBetweenAtoms(*site)
            bond.SetStereo(tag)
            for c in (bond.GetBeginAtom(), bond.GetEndAtom()):
                for adjacent in c.GetBonds(): adjacent.SetBondDir(Chem.BondDir.NONE)
            Chem.SetDoubleBondNeighborDirections(product)
            with self.assertRaisesRegex(ValueError, "cis/Z"):
                rule.validate(before, product, substrate, reagent, site)

    def test_corrupted_unaffected_bond_is_rejected(self):
        before, product, substrate, reagent, site = self.mapped_case()
        product.GetBondBetweenAtoms(0, 1).SetBondType(Chem.BondType.DOUBLE)
        with self.assertRaises(ValueError): rule.validate(before, product, substrate, reagent, site)

    def test_hydrogen_provenance_cannot_be_replaced(self):
        before, product, substrate, reagent, site = self.mapped_case()
        hydrogens = rule.participants(substrate, reagent, site)["hydrogens"]
        atom = next(a for a in product.GetAtoms() if a.GetAtomMapNum() == hydrogens[0])
        atom.SetAtomMapNum(999)
        with self.assertRaises((KeyError, ValueError)): rule.validate(before, product, substrate, reagent, site)

    def test_size_limits_fail_closed(self):
        a, b, response, found = options("C" * 27 + "#C")
        self.assertFalse(found)
        self.assertIn("80 explicit atoms", " ".join(response["unsupportedReasons"]))

    def test_raw_enhanced_or_invalid_stereo_is_not_erased_by_normalization(self):
        for source in ["C#CC[C@H](C)CC |&1:3|", "C#CC[C@H](C)C", "C/C#C/C"]:
            _, _, response, found = options(source)
            self.assertFalse(found)
            self.assertTrue(response["unsupportedReasons"])
            self.assertRegex(" ".join(response["unsupportedReasons"]), "stereo|specified center|annotation")

    def test_cip_letter_change_does_not_mean_physical_inversion(self):
        r = options("C#CCC[C@H](C)CCC(C)(C)C")[3][0]
        self.assertEqual([c["assignment"] for c in r["stereochemistry"]["reactant"]["chiralCenters"]], ["R"])
        self.assertEqual([c["assignment"] for c in r["stereochemistry"]["product"]["chiralCenters"]], ["S"])

    def test_dissolving_metal_conditions_are_not_aliases_for_lindlar(self):
        with self.assertRaises(service.ChemistryError):
            options("CC#CC", conditions={"catalyst": "sodium-ammonia"})

    def test_dry_and_ambient_settings_do_not_certify_a_complete_protocol(self):
        r = options("CC#CC", conditions={"catalyst": "lindlar", "solvent": "dry", "temperature": "ambient"})[3][0]
        self.assertTrue(r["assessment"]["canRun"])
        self.assertEqual(r["assessment"]["evidence"]["conditionCompleteness"], "model-assumptions-only")
        self.assertIn("solvent", r["assessment"]["evidence"]["unknownConditions"])
        self.assertIn("pressure", r["assessment"]["evidence"]["unknownConditions"])


for i, case in enumerate(FIXTURE["positive"]):
    for reverse in (False, True):
        def positive(self, case=case, reverse=reverse): self.check_positive(case, reverse)
        setattr(AlkynePartialTests, f"test_positive_{i:02d}_{'reverse' if reverse else 'forward'}", positive)

for i, case in enumerate(FIXTURE["negative"]):
    def negative(self, case=case):
        try:
            a, b, response, found = options(case["substrate"])
        except service.ChemistryError as exc:
            self.assertEqual(case["label"], "isotope")
            self.assertIn("supported neutral", str(exc))
            return
        self.assertFalse(found, case["label"])
        if case["reason"] != "no triple bond":
            self.assertIn(case["reason"].lower(), " ".join(response["unsupportedReasons"]).lower())
    setattr(AlkynePartialTests, f"test_negative_{i:02d}", negative)

for label, condition in [("missing", {}), ("none", {"catalyst": "none"}), ("ordinary-metal", {"catalyst": "metal"}),
                         ("acid", {"catalyst": "acid"}), ("osmium", {"catalyst": "osmium"}), ("radical", {"catalyst": "radical"}),
                         ("aqueous", {"catalyst": "lindlar", "solvent": "aqueous-protic"}),
                         ("alcohol-medium", {"catalyst": "lindlar", "solvent": "ethanolic-protic"}),
                         ("generic-aprotic", {"catalyst": "lindlar", "solvent": "polar-aprotic"}),
                         ("heated", {"catalyst": "lindlar", "temperature": "heated"})]:
    def blocked(self, condition=condition):
        a, b, _, found = options("CC#CC", conditions=condition)
        self.assertEqual(len(found), 1)
        r = found[0]
        self.assertFalse(r["assessment"]["canRun"])
        self.assertNotEqual(r["assessment"]["status"], "disfavored")
        self.assertFalse(r["stoichiometry"]["context"]["canGenerate3D"])
        self.assertTrue(r["assessment"]["evidence"]["canPreview2D"])
        self.assertIsNone(service.reaction_diagram(r["id"], a, b, condition)["mechanism"])
        with self.assertRaises(service.ChemistryError): service.run_curated_reaction(r["id"], a, b, condition)
    setattr(AlkynePartialTests, "test_conditions_" + label.replace("-", "_"), blocked)

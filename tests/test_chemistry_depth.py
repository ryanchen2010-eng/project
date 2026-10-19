"""Independent structural products, stereo invariants and mapped mechanisms."""
import math
import unittest
from unittest.mock import patch
from rdkit import Chem
from rdkit.Geometry import Point3D
from server import chemistry_server as service
from server.stereochemistry import inspect_stereochemistry, anti_periplanar, invert_sn2, validate_retained_stereo
from server.reaction_diagrams import _species, _combine, _remove, _add, _charge, _finish, _identity


def canonical(smiles):
    return Chem.MolToSmiles(Chem.MolFromSmiles(smiles))


class ExtendedReactionTests(unittest.TestCase):
    def options(self, substrate, reagent, mechanism, conditions=None):
        a = {"name": "Arbitrary substrate", "smiles": substrate}
        b = reagent if reagent in service.REACTANTS else {"name": "Arbitrary reagent", "smiles": reagent}
        result = service.match_reactions(a, b, conditions)
        return a, b, [r for r in result["reactions"] if r["mechanism"] == mechanism]

    def check(self, substrate, reagent, mechanism, expected, conditions=None):
        a, b, options = self.options(substrate, reagent, mechanism, conditions)
        self.assertEqual({r["productSmiles"] for r in options}, {canonical(s) for s in expected})
        self.assertTrue(options)
        for r in options:
            self.assertTrue(r["stoichiometry"]["balanced"])
            diagram = service.reaction_diagram(r["id"], a, b, conditions)
            before = {atom["mapId"]: (atom["element"], atom["formalCharge"]) for atom in diagram["atoms"] if atom["side"] == "reactants"}
            after = {atom["mapId"]: (atom["element"], atom["formalCharge"]) for atom in diagram["atoms"] if atom["side"] == "products"}
            self.assertEqual({m: e for m, (e, _) in before.items()}, {m: e for m, (e, _) in after.items()})
            self.assertEqual(sum(c for _, c in before.values()), sum(c for _, c in after.values()))
            self.assertEqual(len(diagram["atomMap"]), len(before))
            self.assertEqual(diagram["products"][0]["smiles"], r["productSmiles"])
            self.assertTrue(diagram["changes"])
        return a, b, options

    def test_aldehyde_oxidation_multiple_chain_and_aromatic_structures(self):
        for a, p in [("C=O", "O=CO"), ("CC=O", "CC(=O)O"), ("CCC=O", "CCC(=O)O"), ("CC(C)C=O", "CC(C)C(=O)O"), ("O=Cc1ccccc1", "O=C(O)c1ccccc1")]:
            with self.subTest(a=a): self.check(a, "sodium-hypochlorite", "Aldehyde oxidation", [p], {"oxidationStage": "further", "solvent": "aqueous-protic"})

    def test_aldehyde_stage_and_medium_required_and_ketone_excluded(self):
        for c in ({}, {"oxidationStage": "further"}, {"solvent": "aqueous-protic"}):
            self.assertFalse(self.options("CCC=O", "sodium-hypochlorite", "Aldehyde oxidation", c)[2])
        self.assertFalse(self.options("CCC(=O)C", "sodium-hypochlorite", "Aldehyde oxidation", {"oxidationStage": "further", "solvent": "aqueous-protic"})[2])

    def test_dehydration_multiple_alcohols_and_independent_beta_sites(self):
        for a, p in [("CCO", ["C=C"]), ("CCCO", ["C=CC"]), ("CCC(O)C", ["C=CCC", "CC=CC"]), ("CCC(O)(C)C", ["C=C(C)CC", "CC=C(C)C"])]:
            with self.subTest(a=a): self.check(a, "OS(=O)(=O)O", "Alcohol dehydration", p)

    def test_dehydration_catalyst_not_consumed_and_water_maps_preserved(self):
        _, _, options = self.check("CCCO", "sulfuric-acid", "Alcohol dehydration", ["C=CC"])
        r = options[0]
        self.assertEqual(len(r["stoichiometry"]["reactants"]), 1)
        self.assertEqual(r["byproducts"], [{"name": "Water", "formula": "H2O"}])
        self.assertEqual(r["stoichiometry"]["excludedInputs"][0]["inputSlot"], 1)

    def test_dehydration_rearrangements_no_beta_h_and_false_alcohols_rejected(self):
        for a in ("CO", "CC(C)CO", "COC", "Oc1ccccc1", "OC1CCCCC1"):
            self.assertFalse(self.options(a, "sulfuric-acid", "Alcohol dehydration")[2])

    def test_alcohol_substitution_multiple_substrates_and_actual_halogen(self):
        for a, p in [("CO", "CBr"), ("CCO", "CCBr"), ("CCCO", "CCCBr"), ("CC(O)C", "CC(Br)C"), ("CC(O)(C)C", "CC(Br)(C)C")]:
            with self.subTest(a=a): self.check(a, "Br", "Alcohol substitution", [p])
        self.check("CCCO", "I", "Alcohol substitution", ["CCCI"])
        self.check("CC(O)(C)C", "Cl", "Alcohol substitution", ["CC(Cl)(C)C"])

    def test_alcohol_substitution_no_unactivated_chlorination_or_guessed_rearrangement(self):
        for a, b in [("CCO", "Cl"), ("CC(C)CO", "Br"), ("CCO", "hydroxide"), ("COC", "Br")]:
            self.assertFalse(self.options(a, b, "Alcohol substitution")[2])

    def test_saponification_multiple_esters_actual_alcohol_and_anion(self):
        for a, p, coproduct in [("CC(=O)OC", "CC(=O)[O-]", "CO"), ("CCC(=O)OCC", "CCC(=O)[O-]", "CCO"), ("O=C(OC)c1ccccc1", "O=C([O-])c1ccccc1", "CO")]:
            first, second, options = self.check(a, "hydroxide", "Ester saponification", [p])
            r = options[0]; diagram = service.reaction_diagram(r["id"], first, second)
            self.assertEqual(diagram["products"][1]["smiles"], canonical(coproduct))
            product = service.run_curated_reaction(r["id"], first, second)["product"]
            self.assertEqual(product["representation"], "2d-only"); self.assertNotIn("molfile", product)
            self.assertEqual(product["smiles"], canonical(p))

    def test_saponification_full_salt_mass_and_input_order(self):
        first, second, options = self.check("CC(=O)OCC", "[Na+].[OH-]", "Ester saponification", ["CC(=O)[O-]"])
        r = options[0]
        self.assertAlmostEqual(r["stoichiometry"]["reactants"][1]["molarMass"], 39.997, places=3)
        reverse = service.match_reactions(second, first)["reactions"][0]
        self.assertEqual(reverse["productSmiles"], r["productSmiles"])
        self.assertEqual(reverse["stoichiometry"]["reactants"][0]["inputSlot"], 0)
        self.assertAlmostEqual(reverse["stoichiometry"]["reactants"][0]["molarMass"], 39.997, places=3)

    def test_saponification_multiple_sites_and_false_esters(self):
        self.assertEqual(len(self.check("COC(=O)CCC(=O)OC", "hydroxide", "Ester saponification", ["COC(=O)CCC(=O)[O-]"])[2]), 2)
        for a in ("CC(=O)N", "O=C1OCCCCCC1", "COC(=O)OC"):
            self.assertFalse(self.options(a, "hydroxide", "Ester saponification")[2])

    def test_alkyne_full_hydrogenation_two_equivalents_and_internal_substrates(self):
        for a, p in [("C#C", "CC"), ("CC#C", "CCC"), ("CCC#C", "CCCC"), ("CC#CC", "CCCC"), ("CCC#CC", "CCCCC")]:
            _, _, options = self.check(a, "hydrogen", "Alkyne hydrogenation", [p])
            self.assertEqual([r["coefficient"] for r in options[0]["stoichiometry"]["reactants"]], [1, 2])

    def test_lindlar_terminal_and_validated_internal_cis_scope(self):
        for a, p in [("C#C", "C=C"), ("CC#C", "C=CC"), ("CCCC#C", "C=CCCC")]:
            self.check(a, "hydrogen", "Alkyne partial hydrogenation", [p], {"catalyst": "lindlar"})
        # Phase 4A replaces the old unimplemented-internal negative with a
        # stronger positive/activation test; no arbitrary 3D cis guess is used.
        a, b, options = self.check("CC#CC", "hydrogen", "Alkyne partial hydrogenation", ["C/C=C\\C"], {"catalyst": "lindlar"})
        missing = self.options("CC#CC", "hydrogen", "Alkyne partial hydrogenation")[2]
        self.assertTrue(missing)
        self.assertFalse(missing[0]["assessment"]["canRun"])
        with self.assertRaises(service.ChemistryError):
            service.run_curated_reaction(missing[0]["id"], a, b)

    def test_alkyne_halogenation_one_and_two_equivalents_multiple_substrates(self):
        for a, one, two in [("C#C", "BrC=CBr", "BrC(Br)C(Br)Br"), ("CC#C", "CC(Br)=CBr", "CC(Br)(Br)C(Br)Br"), ("CC#CC", "CC(Br)=C(Br)C", "CC(Br)(Br)C(Br)(Br)C")]:
            self.check(a, "bromine", "Alkyne halogenation", [one], {"additionStage": "one"})
            options = self.check(a, "bromine", "Alkyne halogenation", [two], {"additionStage": "two"})[2]
            self.assertEqual(options[0]["stoichiometry"]["reactants"][1]["coefficient"], 2)
        self.check("CCC#C", "chlorine", "Alkyne halogenation", ["CCC(Cl)=CCl"])

    def test_alkyne_hydrohalogenation_markovnikov_and_geminal_multiple_molecules(self):
        for a, one, two in [("CC#C", "CC(Br)=C", "CC(Br)(Br)C"), ("CCC#C", "CCC(Br)=C", "CCC(Br)(Br)C"), ("CC#CC", "CC(Br)=CC", "CC(Br)(Br)CC")]:
            self.check(a, "hydrogen-bromide", "Alkyne hydrohalogenation", [one], {"additionStage": "one"})
            self.check(a, "hydrogen-bromide", "Alkyne hydrohalogenation", [two], {"additionStage": "two"})
        self.check("CC#C", "hydrogen-chloride", "Alkyne hydrohalogenation", ["CC(Cl)=C"])

    def test_alkyne_ambiguous_and_conjugated_cases_do_not_guess(self):
        # Phase 4D: ambiguity means separate constitutional possibilities, not
        # blanket rejection. Original conditions remain incomplete/2D-only.
        alternatives = self.check("CC#CCC", "hydrogen-bromide", "Alkyne hydrohalogenation",
                                  ["CC(Br)=CCC", "CC=C(Br)CC"])[2]
        self.assertTrue(all(r["regioselectivity"]["ratios"] is None and not r["assessment"]["canRun"] for r in alternatives))
        for a in ("C#CC=C", "C#CC#C", "C1CCCCCC#C1"):
            self.assertFalse(self.options(a, "hydrogen", "Alkyne hydrogenation")[2])

    def test_dihydroxylation_multiple_substrates_and_catalyst_assessment(self):
        for a, products in [("C=C", ["OCCO"]), ("C=CC", ["C[C@H](O)CO","C[C@@H](O)CO"]),
                            ("C=CCC", ["CC[C@H](O)CO","CC[C@@H](O)CO"]),
                            ("CC=CC", ["CC(O)C(O)C"]), ("C1=CCCCC1", ["O[C@@H]1CCCC[C@@H]1O"])]:
            self.check(a, "hydrogen-peroxide", "Alkene dihydroxylation", products, {"catalyst": "osmium", "workup":"aqueous-release"})
        wrong = self.options("C=CC", "hydrogen-peroxide", "Alkene dihydroxylation", {"catalyst": "none"})[2][0]
        self.assertEqual(wrong["assessment"]["state"], "incomplete")
        self.assertFalse(wrong["assessment"]["canRun"])
        self.assertIn(wrong["information"]["stereochemistry"]["product"]["chiralCenters"][0]["assignment"], {"R","S"})

    def test_dihydroxylation_stereo_and_conjugation_not_silently_lost(self):
        _,_,options=self.options("C/C=C/C","hydrogen-peroxide","Alkene dihydroxylation",{"catalyst":"osmium","workup":"aqueous-release"})
        self.assertEqual({r["productSmiles"] for r in options},{canonical("C[C@H](O)[C@H](C)O"),canonical("C[C@@H](O)[C@@H](C)O")})
        for a in ("C=CC=C", "C=C(O)C"):
            self.assertFalse(self.options(a, "hydrogen-peroxide", "Alkene dihydroxylation")[2])

    def test_polymerization_multiple_monomers_counts_end_groups_co2_and_balance(self):
        for a in ("C=C", "C=CC", "C=CCC"):
            for n in (2, 4):
                first, second, options = self.options(a, "benzoyl-peroxide", "Polymerization model", {"polymerUnits": str(n)})
                self.assertEqual(len(options), 1)
                r = options[0]; self.assertTrue(r["stoichiometry"]["balanced"])
                self.assertEqual(r["stoichiometry"]["reactants"][0]["coefficient"], n)
                self.assertEqual(r["byproducts"], [{"name": "Carbon dioxide", "formula": "CO2"}] * 2)
                product = Chem.MolFromSmiles(r["productSmiles"])
                self.assertFalse(any(b.GetBondType() == Chem.BondType.DOUBLE and not b.GetIsAromatic() for b in product.GetBonds()))
                self.assertEqual(sum(a.GetIsAromatic() for a in product.GetAtoms()), 12)
                diagram = service.reaction_diagram(r["id"], first, second, {"polymerUnits": str(n)})
                self.assertEqual(len(diagram["reactants"]), n + 1)
                self.assertIn("not a bulk polymer", r["conditions"])

    def test_polymerization_bounds_and_non_vinyl_inputs_rejected(self):
        for a in ("CC=CC", "C=CC=C", "C1=CCCCC1"):
            self.assertFalse(self.options(a, "benzoyl-peroxide", "Polymerization model")[2])
        for value in ("3", "100", "bogus"):
            with self.assertRaises(service.ChemistryError): service.match_reactions("ethene", "benzoyl-peroxide", {"polymerUnits": value})

    def test_new_rules_are_available_without_examples_or_names(self):
        with patch.dict(service.REACTIONS, {}, clear=True):
            self.check("CCCCO", "I", "Alcohol substitution", ["CCCCI"])
            self.check("CCCCC#C", "BrBr", "Alkyne halogenation", ["CCCCC(Br)=CBr"])

    def test_model_variants_have_distinct_ids_and_stale_choices_fail(self):
        a, b, one = self.options("CC#C", "bromine", "Alkyne halogenation", {"additionStage": "one"})
        two = self.options("CC#C", "bromine", "Alkyne halogenation", {"additionStage": "two"})[2]
        self.assertNotEqual(one[0]["id"], two[0]["id"])
        with self.assertRaises(service.ChemistryError): service.reaction_diagram(one[0]["id"], a, b, {"additionStage": "two"})
        ids = [self.options("C=C", "benzoyl-peroxide", "Polymerization model", {"polymerUnits": n})[2][0]["id"] for n in ("2", "4", "6")]
        self.assertEqual(len(set(ids)), 3)

    def test_model_parameters_are_not_mislabeled_as_substrate_atom_indices(self):
        for a, b, name in [("C#C", "bromine", "Alkyne halogenation"), ("C=C", "benzoyl-peroxide", "Polymerization model")]:
            r = self.options(a, b, name)[2][0]
            self.assertTrue(all(0 <= i < Chem.MolFromSmiles(a).GetNumAtoms() for i in r["site"]["substrateAtoms"]))
            self.assertTrue(r["site"]["parameters"])

    def test_amidation_remains_absent_under_ordinary_and_heated_conditions(self):
        for c in ({}, {"temperature": "heated", "solvent": "dry", "catalyst": "acid"}):
            self.assertFalse(service.match_reactions({"smiles": "CC(=O)O"}, {"smiles": "CN"}, c)["reactions"])


class StereoFoundationTests(unittest.TestCase):
    def inspect(self, smiles):
        return service.inspect_reactant({"smiles": smiles})["stereochemistry"]

    def test_specified_and_potential_centers_are_distinguished(self):
        self.assertIsNone(self.inspect("CC(O)CC")["chiralCenters"][0]["assignment"])
        self.assertIn(self.inspect("C[C@H](O)CC")["chiralCenters"][0]["assignment"], {"R", "S"})
        self.assertEqual(self.inspect("CC(O)C")["chiralCenters"], [])

    def test_map_numbers_and_explicit_h_do_not_change_cip_assignment(self):
        molecule = Chem.MolFromSmiles("C[C@H](O)CC")
        expected = inspect_stereochemistry(molecule)["chiralCenters"][0]["assignment"]
        for i, a in enumerate(molecule.GetAtoms()): a.SetAtomMapNum(99 - i)
        self.assertEqual(inspect_stereochemistry(Chem.AddHs(molecule))["chiralCenters"][0]["assignment"], expected)

    def test_ez_and_cis_trans_common_h_reference_and_unassigned(self):
        for smiles, ez, relative in [("C/C=C/C", "E", "trans"), ("C/C=C\\C", "Z", "cis"), ("CC=CC", None, None)]:
            value = self.inspect(smiles)["alkenes"][0]
            self.assertEqual(value["assignment"], ez); self.assertEqual(value["cisTrans"], relative)
        self.assertEqual(self.inspect("C=CC")["alkenes"], [])

    def test_cis_trans_not_invented_for_no_common_h_reference(self):
        value = self.inspect("CC/C(C)=C(/Cl)Br")["alkenes"][0]
        self.assertIn(value["assignment"], {"E", "Z"}); self.assertIsNone(value["cisTrans"])

    def test_sn2_physical_inversion_both_enantiomers_and_multiple_atom_orders(self):
        for substrate, product in [("C[C@H](Br)CC", "C[C@@H](O)CC"), ("C[C@@H](Br)CC", "C[C@H](O)CC"), ("Br[C@@H](C)CC", "O[C@H](C)CC")]:
            options = [r for r in service.match_reactions({"smiles": substrate}, "hydroxide")["reactions"] if r["mechanism"] == "SN2"]
            self.assertEqual(len(options), 1); self.assertEqual(options[0]["productSmiles"], canonical(product))
            mechanism = service.reaction_diagram(options[0]["id"], {"smiles": substrate}, "hydroxide")["mechanism"]
            self.assertEqual(len(mechanism["steps"]), 1)

    def test_sn2_inversion_is_not_blind_r_s_letter_swap(self):
        # This priority-changing graph is a stereochemistry utility test, not
        # evidence validating hydroxide chemistry on a geminal trihalide.
        a, n = _species("a", {"name": "Priority test", "smiles": "C[C@](Cl)(Br)I"}, 1)
        b, _ = _species("b", {"name": "Hydroxide", "smiles": "[OH-]"}, n)
        before = _combine([a, b]); editor = Chem.RWMol(before)
        leaving = next(x for x in before.GetAtoms() if x.GetSymbol() == "Br")
        carbon = leaving.GetNeighbors()[0].GetAtomMapNum()
        bromine = leaving.GetAtomMapNum()
        oxygen = next(x.GetAtomMapNum() for x in before.GetAtoms() if x.GetSymbol() == "O")
        _remove(editor, carbon, bromine); _add(editor, carbon, oxygen)
        _charge(editor, bromine, -1); _charge(editor, oxygen, 0)
        invert_sn2(before, editor, carbon, bromine, oxygen)
        after = _finish(editor)
        validate_retained_stereo(before, after, inverted_substitutions=[{"center": carbon, "leaving": bromine, "incoming": oxygen}])
        main = next(f for f in Chem.GetMolFrags(after, asMols=True) if any(x.GetAtomMapNum() == carbon for x in f.GetAtoms()))
        self.assertEqual(_identity(main), canonical("C[C@@](Cl)(O)I"))
        self.assertEqual(inspect_stereochemistry(before)["chiralCenters"][0]["assignment"], inspect_stereochemistry(after)["chiralCenters"][0]["assignment"])
        self.assertFalse(any(r["mechanism"] == "SN2" for r in service.match_reactions({"smiles": "C[C@](Cl)(Br)I"}, "hydroxide")["reactions"]))

    def test_sn2_unspecified_stays_unspecified_other_stereo_reactions_rejected(self):
        r = next(r for r in service.match_reactions({"smiles": "CCC(Br)C"}, "hydroxide")["reactions"] if r["mechanism"] == "SN2")
        self.assertIsNone(r["information"]["stereochemistry"]["product"]["chiralCenters"][0]["assignment"])
        self.assertFalse(service.match_reactions({"smiles": "CC[C@H](C)C(Br)(C)C"}, "water")["reactions"])

    def conformer(self, angle):
        molecule = Chem.AddHs(Chem.MolFromSmiles("CCBr"))
        for i, a in enumerate(molecule.GetAtoms(), 1): a.SetAtomMapNum(i)
        h = next(a.GetIdx() for a in molecule.GetAtomWithIdx(0).GetNeighbors() if a.GetSymbol() == "H")
        conformer = Chem.Conformer(molecule.GetNumAtoms()); conformer.Set3D(True)
        for i, p in [(h, (0, 1, 0)), (0, (0, 0, 0)), (1, (1, 0, 0)), (2, (1, math.cos(math.radians(angle)), math.sin(math.radians(angle))))]:
            conformer.SetAtomPosition(i, Point3D(*p))
        molecule.AddConformer(conformer)
        return molecule, [molecule.GetAtomWithIdx(i).GetAtomMapNum() for i in (h, 0, 1, 2)]

    def test_e2_anti_syn_gauche_and_signed_torsions(self):
        for angle, anti in [(180, True), (-180, True), (170, True), (160, False), (60, False), (0, False)]:
            molecule, maps = self.conformer(angle); result = anti_periplanar(molecule, *maps)
            self.assertEqual(result["antiPeriplanar"], anti)
            self.assertAlmostEqual(abs(result["dihedralDegrees"]), abs(angle), places=3)

    def test_e2_geometry_rejects_absent_invalid_2d_degenerate_and_bad_tolerance(self):
        m, maps = self.conformer(180)
        with self.assertRaises(ValueError): anti_periplanar(m, maps[0], maps[0], maps[2], maps[3])
        with self.assertRaises(ValueError): anti_periplanar(m, *maps, tolerance=100)
        m.GetConformer().Set3D(False)
        with self.assertRaises(ValueError): anti_periplanar(m, *maps)
        m.GetConformer().Set3D(True); m.GetConformer().SetAtomPosition(1, Point3D(0, 0, 0))
        with self.assertRaises(ValueError): anti_periplanar(m, *maps)

    def test_inspection_geometry_reports_actual_conformer_and_maps(self):
        result = service.inspect_reactant({"smiles": "CCCBr"}, include_3d=True)
        self.assertTrue(result["e2Geometry"])
        maps = {a["mapId"] for a in result["model"]["atomLinks"]}
        for site in result["e2Geometry"]:
            self.assertTrue(set(site["atomMaps"]) <= maps); self.assertIn("One supplied conformer", site["note"])


class MechanismCompletionTests(unittest.TestCase):
    def test_all_four_mechanisms_have_conserved_before_after_and_real_electron_sources(self):
        for a, b in [("CCBr", "hydroxide"), ("CC(C)(C)Cl", "water"), ("CCC(C)(Br)C", "water")]:
            for r in service.match_reactions({"smiles": a}, b)["reactions"]:
                mechanism = service.reaction_diagram(r["id"], {"smiles": a}, b)["mechanism"]
                self.assertIsNotNone(mechanism)
                for step in mechanism["steps"]:
                    before, after = step["beforeState"], step["state"]
                    self.assertEqual({x["mapId"]: x["element"] for x in before["atoms"]}, {x["mapId"]: x["element"] for x in after["atoms"]})
                    self.assertEqual(sum(x["formalCharge"] for x in before["atoms"]), sum(x["formalCharge"] for x in after["atoms"]))
                    bonds = {frozenset(x["atomMaps"]) for x in before["bonds"]}
                    for move in step["electronMoves"]:
                        if move["source"]["type"] == "bond": self.assertIn(frozenset(move["source"]["atomMaps"]), bonds)
                    self.assertTrue(step["bondsFormed"] or step["bondsBroken"] or step["bondOrderChanges"])

    def test_sn1_proton_transfer_and_e2_concerted_state_not_fictitious_intermediates(self):
        for a, b, name, steps in [("CBr", "hydroxide", "SN2", 1), ("CCBr", "hydroxide", "E2", 1), ("CC(C)(C)Cl", "water", "SN1", 3), ("CC(C)(C)Cl", "water", "E1", 2)]:
            r = next(r for r in service.match_reactions({"smiles": a}, b)["reactions"] if r["mechanism"] == name)
            m = service.reaction_diagram(r["id"], {"smiles": a}, b)["mechanism"]
            self.assertEqual(len(m["steps"]), steps)
            if name in {"SN2", "E2"}: self.assertIsNone(m["steps"][0]["intermediate"])
            if name in {"SN1", "E1", "E2"}: self.assertTrue(m["steps"][-1]["protonTransfers"])


if __name__ == "__main__": unittest.main()

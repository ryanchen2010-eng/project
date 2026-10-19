"""Independent product expectations across structural families and graph sites."""
import json
from pathlib import Path
import unittest
from unittest.mock import patch
from rdkit import Chem

from server import molecular_graph as graph
from server import reaction_engine as engine
from server import chemistry_server as service


def canonical(smiles):
    return Chem.MolToSmiles(Chem.MolFromSmiles(smiles), canonical=True)


class StructuralReactionEngineTests(unittest.TestCase):
    def options(self, substrate, partner, mechanism):
        return [r for r in service.match_reactions({"smiles": substrate},
                partner if partner in service.REACTANTS else {"smiles": partner})["reactions"]
                if r["mechanism"] == mechanism]

    def check(self, substrate, partner, mechanism, expected):
        options = self.options(substrate, partner, mechanism)
        self.assertEqual({r["productSmiles"] for r in options}, {canonical(s) for s in expected})
        self.assertTrue(options)
        for option in options:
            self.assertTrue(option["stoichiometry"]["balanced"])
            partner_ref = partner if partner in service.REACTANTS else {"smiles": partner}
            preview = service.reaction_diagram(option["id"], {"smiles": substrate}, partner_ref)
            self.assertTrue(preview["highlightsAvailable"])
            self.assertTrue(preview["changes"])
            before = {a["mapId"]: a["element"] for a in preview["atoms"] if a["side"] == "reactants"}
            after = {a["mapId"]: a["element"] for a in preview["atoms"] if a["side"] == "products"}
            self.assertEqual(before, after)
            self.assertEqual(len(preview["atomMap"]), len(before))
            self.assertTrue(all(a.get("reactantId") for a in preview["atomMap"]))
            self.assertEqual(preview["products"][0]["smiles"], option["productSmiles"])
            self.assertTrue(set(option["site"]["atomMaps"]) <= set(before))
            self.assertIn('class="reaction-site"', preview["svg"])
        return options

    def test_all_seventeen_pre_refactor_pathways_preserve_exact_products(self):
        baseline = json.loads((Path(__file__).parent / "fixtures/reaction-baseline.json").read_text())
        current = service._all_reactions()
        for identifier, old in baseline.items():
            with self.subTest(pathway=identifier):
                if identifier == "bromination-propene":
                    # Phase 3C replaces one unsigned product with both faces.
                    options = [r for r in service.match_reactions(*old["reactants"], {"solvent":"dry"})["reactions"] if r["mechanism"] == "Bromination"]
                    self.assertEqual({r["productSmiles"] for r in options}, {canonical("C[C@H](Br)CBr"),canonical("C[C@@H](Br)CBr")})
                    for r in options:
                        self.assertEqual(r["byproducts"], [])
                        self.assertTrue(service.run_curated_reaction(r["id"], *old["reactants"], {"solvent":"dry"})["balanced"])
                    continue
                self.assertIn(identifier, current)
                new = current[identifier]
                self.assertEqual(canonical(new["productSmiles"]), canonical(old["productSmiles"]))
                self.assertEqual([canonical(item["smiles"]) for item in new["byproducts"]],
                                 [canonical(item["smiles"]) for item in old["byproducts"]])
                service.reaction_diagram(identifier, *old["reactants"])
                conditions = {"catalyst": "acid"} if new["mechanism"] == "Hydration" else {"solvent": "dry"} if new["mechanism"] == "Bromination" else None
                if new.get("secondaryOxidationModel"):
                    with self.assertRaises(service.ChemistryError):service.run_curated_reaction(identifier,*old["reactants"],conditions)
                    conditions={"solvent":"aqueous-protic","temperature":"ambient","catalyst":"none","oxidationStage":"first","secondaryOxidationProfile":"naocl-acetic-ketone-v1"}
                self.assertTrue(service.run_curated_reaction(identifier, *old["reactants"], conditions)["balanced"])

    def test_hydrogenation_chain_size_position_branching_ring_and_ez(self):
        for substrate, product in (("C=C", "CC"), ("C=CC", "CCC"), ("C=CCC", "CCCC"),
                ("CC=CC", "CCCC"), ("C/C=C/C", "CCCC"), ("C=CCCCCCCC", "CCCCCCCCC"),
                ("CC(C)=CC", "CC(C)CC"), ("C1=CCCCC1", "C1CCCCC1")):
            with self.subTest(substrate=substrate): self.check(substrate, "hydrogen", "Hydrogenation", [product])

    def test_bromine_and_chlorine_addition_are_reagent_graph_rules(self):
        for reagent, symbol, mechanism in (("bromine", "Br", "Bromination"), ("chlorine", "Cl", "Chlorination")):
            for substrate, product in (("C=C", f"{symbol}CC{symbol}"), ("C=CC", f"CC({symbol})C{symbol}"),
                                       ("CC=CC", f"CC({symbol})C({symbol})C"), ("C=CCCCCC", f"{symbol}CC({symbol})CCCCC")):
                with self.subTest(reagent=reagent, substrate=substrate):
                    if mechanism == "Bromination" and substrate in {"C=CC", "C=CCCCCC"}:
                        self.check(substrate, reagent, mechanism, ["C[C@H](Br)CBr", "C[C@@H](Br)CBr"] if substrate == "C=CC" else ["CCCCC[C@H](Br)CBr", "CCCCC[C@@H](Br)CBr"])
                    elif mechanism == "Chlorination" and substrate in {"C=CC", "C=CCCCCC"}:
                        self.check(substrate, reagent, mechanism, ["C[C@H](Cl)CCl", "C[C@@H](Cl)CCl"] if substrate == "C=CC" else ["CCCCC[C@H](Cl)CCl", "CCCCC[C@@H](Cl)CCl"])
                    else:
                        self.check(substrate, reagent, mechanism, [product])

    def test_hydration_uses_substitution_and_graph_symmetry(self):
        for substrate, product in (("C=C", "CCO"), ("C=CC", "CC(O)C"), ("C=CCC", "CCC(O)C"),
                ("CC=CC", "CCC(O)C"), ("C=C(C)C", "CC(O)(C)C"), ("C=CCCCCC", "CCCCCC(O)C")):
            with self.subTest(substrate=substrate): self.check(substrate, "water", "Hydration", [product])

    def test_hydrohalogenation_uses_the_actual_halogen(self):
        for reagent, symbol in (("hydrogen-chloride", "Cl"), ("hydrogen-bromide", "Br"), ("hydrogen-iodide", "I")):
            self.check("C=CC", reagent, "Hydrohalogenation", [f"CC({symbol})C"])
            self.check("CC=CC", reagent, "Hydrohalogenation", [f"CCC({symbol})C"])

    def test_ambiguous_orientation_and_rearrangement_are_not_guessed(self):
        for substrate in ("CC=CCC", "C=CC(C)C"):
            for reagent in ("water", "hydrogen-bromide"):
                result = service.match_reactions({"smiles": substrate}, reagent)
                if substrate == "CC=CCC":
                    # Both independently validated consumers now represent
                    # constitutional alternatives, not a guessed orientation.
                    group = "O" if reagent == "water" else "Br"
                    self.assertEqual({r["productSmiles"] for r in result["reactions"]}, {canonical(f"CC({group})CCC"), canonical(f"CCC({group})CC")})
                    self.assertTrue(all(r["regioselectivity"]["ratios"] is None for r in result["reactions"]))
                else:
                    self.assertFalse(result["reactions"])
                    self.assertTrue(result["unsupportedReasons"])

    def test_separated_multiple_double_bonds_are_separate_site_options(self):
        result = self.check("C=CCCC=C", "hydrogen", "Hydrogenation", ["C=CCCCC"])
        self.assertEqual(len(result), 2)
        self.assertTrue(all(r["productName"] == "Partially hydrogenated product" for r in result))
        self.assertNotEqual(result[0]["site"]["atomMaps"], result[1]["site"]["atomMaps"])
        self.assertNotEqual(result[0]["id"], result[1]["id"])
        for option in result:
            preview = service.reaction_diagram(option["id"], {"smiles": "C=CCCC=C"}, "hydrogen")
            self.assertEqual(len(preview["bondOrderChanges"]), 1)

    def test_primary_secondary_and_tertiary_alcohol_classification(self):
        for substrate, product in (("CCO", "CC=O"), ("CCCO", "CCC=O"), ("CCCCO", "CCCC=O"),
                ("CC(O)C", "CC(=O)C"), ("CCC(O)C", "CCC(=O)C"), ("CCCC(O)C", "CCCC(=O)C"),
                ("OC1CCCCC1", "O=C1CCCCC1")):
            with self.subTest(substrate=substrate): self.check(substrate, "sodium-hypochlorite", "Alcohol oxidation", [product])
        rejected = service.match_reactions({"smiles": "CC(O)(C)C"}, "sodium-hypochlorite")
        self.assertFalse(rejected["reactions"])
        self.assertTrue(any("Tertiary" in note for note in rejected["unsupportedReasons"]))
        self.assertFalse(self.options("Oc1ccccc1", "sodium-hypochlorite", "Alcohol oxidation"))

    def test_primary_oxidation_is_labelled_a_stage_not_guaranteed_aldehyde_isolation(self):
        option = self.options("CCO", "sodium-hypochlorite", "Alcohol oxidation")[0]
        self.assertIn("further oxidation", option["explanation"])
        self.assertIn("not a claim of an isolated product", option["conditions"])

    def test_carbonyl_reduction_aldehydes_ketones_and_ring(self):
        for substrate, product in (("CC=O", "CCO"), ("CCC=O", "CCCO"), ("CCCC=O", "CCCCO"),
                ("CC(=O)C", "CC(O)C"), ("CCC(=O)C", "CCC(O)C"), ("O=C1CCCCC1", "OC1CCCCC1"),
                ("O=Cc1ccccc1", "OCc1ccccc1")):
            with self.subTest(substrate=substrate): self.check(substrate, "hydrogen", "Carbonyl hydrogenation", [product])
        for substrate in ("CC(=O)O", "CC(=O)OC", "CC(=O)N", "C=CC=O"):
            self.assertFalse(self.options(substrate, "hydrogen", "Carbonyl hydrogenation"))

    def test_esterification_builds_actual_acid_and_alcohol_fragments(self):
        for acid, alcohol, product in (("CC(=O)O", "CO", "CC(=O)OC"), ("CC(=O)O", "CCO", "CC(=O)OCC"),
                ("CCC(=O)O", "CO", "CCC(=O)OC"), ("CCC(=O)O", "CCO", "CCC(=O)OCC"),
                ("CCCC(=O)O", "CCCO", "CCCC(=O)OCCC"), ("O=C(O)c1ccccc1", "CO", "O=C(OC)c1ccccc1")):
            with self.subTest(acid=acid, alcohol=alcohol):
                self.check(acid, alcohol, "Esterification", [product])
                reverse = service.match_reactions({"smiles": alcohol}, {"smiles": acid})["reactions"]
                self.assertEqual({r["productSmiles"] for r in reverse}, {canonical(product)})

    def test_ester_hydrolysis_splits_actual_fragments(self):
        for ester, acid, alcohol in (("CC(=O)OC", "CC(=O)O", "CO"), ("CC(=O)OCC", "CC(=O)O", "CCO"),
                ("CCC(=O)OC", "CCC(=O)O", "CO"), ("CCC(=O)OCC", "CCC(=O)O", "CCO"),
                ("CCCC(=O)OCCC", "CCCC(=O)O", "CCCO")):
            option = self.check(ester, "water", "Ester hydrolysis", [acid])[0]
            preview = service.reaction_diagram(option["id"], {"smiles": ester}, "water")
            self.assertEqual(preview["products"][1]["smiles"], canonical(alcohol))

    def test_multiple_alcohol_and_acid_sites_produce_independent_candidates(self):
        options = self.check("OCCC(O)C", "sodium-hypochlorite", "Alcohol oxidation", ["O=CCC(O)C", "OCCC(=O)C"])
        self.assertEqual(len(options), 2)
        options = self.check("O=C(O)CC(=O)O", "CO", "Esterification", ["COC(=O)CC(=O)O"])
        self.assertEqual(len(options), 2)
        options = self.check("COC(=O)CCCC(=O)OC", "water", "Ester hydrolysis", ["COC(=O)CCCC(=O)O"])
        self.assertEqual(len(options), 2)
        options = self.check("CC(=O)O", "OCCO", "Esterification", ["CC(=O)OCCO"])
        self.assertEqual(len(options), 2)

    def test_sn2_multiple_primary_substrates_and_iodide(self):
        for substrate, product in (("CBr", "CO"), ("CCBr", "CCO"), ("CCCCl", "CCCO"), ("CCCCI", "CCCCO"),
                ("CCCCCCCCBr", "CCCCCCCCO"), ("BrCc1ccccc1", "OCc1ccccc1")):
            with self.subTest(substrate=substrate): self.check(substrate, "hydroxide", "SN2", [product])
        for substrate in ("CC(C)(C)Br", "CC(C)(C)CBr", "Brc1ccccc1", "C=CBr", "CCF"):
            self.assertFalse(self.options(substrate, "hydroxide", "SN2"))

    def test_secondary_substitution_is_an_option_not_a_rate_prediction(self):
        self.check("CCC(C)Br", "hydroxide", "SN2", ["CCC(C)O"])

    def test_e2_beta_sites_preserve_all_distinct_constitutional_products(self):
        for substrate, products in (("CCBr", ["C=C"]), ("CCCBr", ["C=CC"]),
                ("CCC(C)Br", ["C=CCC", "CC=CC"]), ("CCCC(C)Br", ["C=CCCC", "CC=CCC"]),
                ("CCC(Br)(C)C", ["C=C(C)CC", "CC=C(C)C"])):
            with self.subTest(substrate=substrate): self.check(substrate, "hydroxide", "E2", products)
        for substrate in ("CBr", "CC(C)(C)CBr", "Brc1ccccc1"):
            self.assertFalse(self.options(substrate, "hydroxide", "E2"))

    def test_sn1_e1_restricted_carbocations_but_no_size_whitelist(self):
        self.check("CCC(Br)(C)C", "water", "SN1", ["CCC(O)(C)C"])
        self.check("CCC(Br)(C)C", "water", "E1", ["C=C(C)CC", "CC=C(C)C"])
        self.check("BrCc1ccccc1", "water", "SN1", ["OCc1ccccc1"])
        for substrate in ("CCBr", "CCC(C)Br", "C=CC(Br)C"):
            if substrate == "CCC(C)Br":
                self.assertEqual(self.options(substrate, "water", "SN1")[0]["productSmiles"], canonical("CCC(O)C"))
            else:
                self.assertFalse(self.options(substrate, "water", "SN1"))

    def test_false_functional_groups_and_unsupported_substrates_are_not_reacted(self):
        for substrate, partner in (("COC", "CCO"), ("O=C(O)O", "CCO"), ("COC(=O)OC", "water"),
                ("O=C1OCCCCCC1", "water"), ("CC(=O)O", "CC(O)(C)C"), ("C=CC=C", "hydrogen"),
                ("C1=CCC1", "hydrogen"), ("C#CC#C", "hydrogen"), ("C[Hg]C", "hydrogen")):
            with self.subTest(substrate=substrate):
                if "Hg" in substrate:
                    with self.assertRaises(service.ChemistryError): service.match_reactions({"smiles": substrate}, partner)
                else: self.assertFalse(service.match_reactions({"smiles": substrate},
                        partner if partner in service.REACTANTS else {"smiles": partner})["reactions"])

    def test_invalid_transformation_is_hidden_with_an_explanation(self):
        with patch.object(engine, "transform", side_effect=ValueError("Invalid product")):
            response = service.match_reactions("ethene", "hydrogen")
        self.assertFalse(response["reactions"])
        self.assertTrue(any("failed validation" in note for note in response["unsupportedReasons"]))

    def test_product_validation_rejects_duplicate_maps_changed_atoms_and_charge(self):
        before = Chem.AddHs(Chem.MolFromSmiles("CCO"))
        for i, a in enumerate(before.GetAtoms(), 1): a.SetAtomMapNum(i)
        for mutation in ("map", "element", "charge"):
            after = Chem.Mol(before)
            if mutation == "map": after.GetAtomWithIdx(1).SetAtomMapNum(1)
            elif mutation == "element": after.GetAtomWithIdx(0).SetAtomicNum(14)
            else: after.GetAtomWithIdx(2).SetFormalCharge(1)
            with self.subTest(mutation=mutation), self.assertRaises((ValueError, RuntimeError)):
                engine.validate_products(before, after, 1)

    def test_identity_labels_and_cids_do_not_decide_eligibility(self):
        result = service.match_reactions({"name": "Ethanoic acid", "smiles": "COC", "cid": 176}, {"smiles": "CCO"})
        self.assertFalse(result["reactions"])
        renamed = {**service.REACTANTS["ethene"], "name": "Something else", "formula": "NaCl", "cid": 0}
        with patch.dict(service.REACTANTS, {"ethene": renamed}):
            self.assertEqual(service.match_reactions("ethene", "hydrogen")["reactions"][0]["productSmiles"], "CC")

    def test_removing_every_hardcoded_example_does_not_remove_structural_rules(self):
        with patch.dict(service.REACTIONS, {}, clear=True):
            self.check("CC(=O)O", "CCO", "Esterification", ["CC(=O)OCC"])
            self.check("CC(C)=O", "hydrogen", "Carbonyl hydrogenation", ["CC(O)C"])
            self.check("C=CC", "water", "Hydration", ["CC(O)C"])

    def test_searched_counterion_oxidant_is_recognized_by_graph_not_catalog_name(self):
        option = self.check("CCCCO", "[K+].[O-]Cl", "Alcohol oxidation", ["CCCC=O"])[0]
        self.assertIn({"name": "Potassium chloride", "formula": "KCl"}, option["byproducts"])

    def test_atom_maps_survive_actual_3d_for_nonpreset_reactions(self):
        for substrate, reagent, mechanism in (("CCC(=O)O", "CCCO", "Esterification"),
                ("CCC(=O)OC", "water", "Ester hydrolysis"), ("CCC(C)Br", "hydroxide", "E2"),
                ("C=CCCC=C", "hydrogen", "Hydrogenation"), ("CCCCO", "sodium-hypochlorite", "Alcohol oxidation")):
            for option in self.options(substrate, reagent, mechanism):
                first, second = {"smiles": substrate}, reagent if reagent in service.REACTANTS else {"smiles": reagent}
                preview = service.reaction_diagram(option["id"], first, second)
                if option.get("primaryOxidationModel"):
                    # An aldehyde net-stage preview is not a qualified endpoint.
                    self.assertTrue(preview["atoms"])
                    self.assertFalse(option["assessment"]["evidence"]["canGenerate3D"])
                    with self.assertRaises(service.ChemistryError):
                        service.run_curated_reaction(option["id"], first, second)
                    continue
                product = service.run_curated_reaction(option["id"], first, second)["product"]
                maps = [(a["atomIndex"], a["mapId"], a["element"]) for a in preview["atoms"]
                        if a["side"] == "products" and a["speciesIndex"] == 0]
                self.assertEqual(maps, [(a["index"], a["mapId"], a["element"]) for a in product["atomLinks"]])

    def test_reusable_group_helpers_do_not_confuse_acid_oh_with_alcohol(self):
        self.assertFalse(graph.find_alcohols(Chem.MolFromSmiles("CC(=O)O")))
        self.assertEqual(len(graph.find_carboxylic_acids(Chem.MolFromSmiles("CC(=O)O"))), 1)
        self.assertEqual(len(graph.find_esters(Chem.MolFromSmiles("CC(=O)OCC"))), 1)
        for smiles, degree in (("CCO", 1), ("CC(O)C", 2), ("CC(O)(C)C", 3)):
            mol = Chem.MolFromSmiles(smiles); c, _ = graph.find_alcohols(mol)[0]
            self.assertEqual(graph.substitution_degree(mol.GetAtomWithIdx(c)), degree)

    def test_supplied_original_atom_maps_remain_in_source_provenance(self):
        reference = {"smiles": "[CH3:42][CH2:9][Br:77]"}
        option = next(r for r in service.match_reactions(reference, "hydroxide")["reactions"] if r["mechanism"] == "SN2")
        preview = service.reaction_diagram(option["id"], reference, "hydroxide")
        originals = {a["originalAtomMap"]: a for a in preview["atomMap"] if "originalAtomMap" in a}
        self.assertEqual(set(originals), {42, 9, 77})
        self.assertEqual(originals[77]["element"], "Br")
        self.assertEqual(originals[77]["productIndex"], 1)
        self.assertEqual(originals[42]["productIndex"], 0)


if __name__ == "__main__":
    unittest.main()

"""Graph facts, exact elementary-step mapping and staged oxidation regressions."""
import unittest
from rdkit import Chem
from server import chemistry_server as service
from server.reaction_reasoning import compare_pathways


def canonical(smiles):
    return Chem.MolToSmiles(Chem.MolFromSmiles(smiles))


class PathwayInsightsTests(unittest.TestCase):
    def options(self, substrate, reagent, conditions=None):
        return service.match_reactions({"smiles": substrate}, reagent, conditions)

    def mechanism(self, substrate, reagent, pathway, conditions=None):
        options = self.options(substrate, reagent, conditions)["reactions"]
        option = next(r for r in options if r["mechanism"] == pathway)
        diagram = service.reaction_diagram(option["id"], {"smiles": substrate}, reagent, conditions)
        return option, diagram, diagram["mechanism"]

    def test_reasoning_is_deterministic_graph_based_and_has_no_probabilities(self):
        a = service.match_reactions({"smiles": "CCBr", "name": "Water"}, "hydroxide")
        b = service.match_reactions({"smiles": "CCBr", "name": "Anything"}, "hydroxide")
        self.assertEqual([(r["id"], r["productSmiles"], r["reasoning"]) for r in a["reactions"]],
                         [(r["id"], r["productSmiles"], r["reasoning"]) for r in b["reactions"]])
        for option in a["reactions"]:
            self.assertTrue(option["reasoning"]["factors"])
            self.assertNotIn("probability", option["reasoning"])
            self.assertTrue(all(f["pathway"] == option["mechanism"] for f in option["reasoning"]["factors"]))

    def test_primary_secondary_and_tertiary_sn2_reasoning(self):
        primary = self.mechanism("CCBr", "hydroxide", "SN2", {"solvent": "polar-aprotic"})[0]
        secondary = self.mechanism("CC(Br)CC", "hydroxide", "SN2", {"solvent": "polar-aprotic"})[0]
        self.assertEqual(primary["reasoning"]["label"], "Strong match")
        self.assertEqual(secondary["reasoning"]["label"], "Possible")
        self.assertIn("disfavors", [f["effect"] for f in secondary["reasoning"]["factors"] if f["factor"] == "steric-hindrance"])
        self.assertFalse(any(r["mechanism"] == "SN2" for r in self.options("CC(C)(C)Br", "hydroxide")["reactions"]))

    def test_conditions_change_facts_and_label_not_product_identity(self):
        a = self.mechanism("CCBr", "hydroxide", "SN2", {"solvent": "polar-aprotic"})[0]
        b = self.mechanism("CCBr", "hydroxide", "SN2", {"solvent": "ethanolic-protic", "temperature": "heated"})[0]
        self.assertEqual(a["productSmiles"], b["productSmiles"])
        self.assertEqual(b["reasoning"]["label"], "Disfavored factors")
        self.assertNotEqual(a["reasoning"], b["reasoning"])

    def test_missing_conditions_and_unknown_catalyst_are_not_strong_matches(self):
        for conditions in ({}, {"solvent": "polar-aprotic", "catalyst": "acid"}):
            r = self.mechanism("CBr", "hydroxide", "SN2", conditions)[0]
            self.assertEqual(r["reasoning"]["label"], "Not evaluated" if conditions.get("catalyst") else "Conditions incomplete")

    def test_comparison_is_exactly_the_same_rule_facts(self):
        result = self.options("CC(Br)CC", "hydroxide", {"solvent": "ethanolic-protic", "temperature": "heated"})
        self.assertEqual(result["comparison"], compare_pathways(result["reactions"]))
        for row in result["comparison"]["rows"]:
            for cell in row["cells"]:
                r = next(r for r in result["reactions"] if r["id"] == cell["reactionId"])
                fact = next((f for f in r["reasoning"]["factors"] if f["factor"] == row["factor"]), None)
                if fact:
                    self.assertEqual((cell["value"], cell["effect"], cell["explanation"]), (fact["value"], fact["effect"], fact["explanation"]))

    def test_unsupported_pairs_have_no_comparison_or_fake_options(self):
        result = self.options("CC(=O)O", {"smiles": "CN"})
        self.assertEqual(result["supportState"], "Unsupported")
        self.assertIsNone(result["comparison"])
        self.assertEqual(result["reactions"], [])
        self.assertIn("amidation", " ".join(result["unsupportedReasons"]))

    def check_steps(self, diagram, mechanism):
        identity = {a["mapId"]: a["element"] for a in diagram["atoms"] if a["side"] == "reactants"}
        for solvent in mechanism["solventSpecies"]:
            for map_id in solvent["atomMaps"]:
                self.assertNotIn(map_id, identity)
        initial_charge = sum(a["formalCharge"] for a in diagram["atoms"] if a["side"] == "reactants")
        previous_maps = None
        for step in mechanism["steps"]:
            state = step["state"]
            maps = {a["mapId"]: a["element"] for a in state["atoms"]}
            self.assertEqual(sum(a["formalCharge"] for a in state["atoms"]), initial_charge)
            for map_id, element in identity.items(): self.assertEqual(maps[map_id], element)
            if previous_maps is not None: self.assertEqual(maps, previous_maps)
            previous_maps = maps
            for move in step["electronMoves"]:
                for end in (move["source"], move["destination"]): self.assertTrue(set(end["atomMaps"]) <= maps.keys())
            parser = Chem.SmilesParserParams(); parser.removeHs = False
            mol = Chem.MolFromSmiles(state["mappedSmiles"], parser)
            self.assertIsNotNone(mol)
            self.assertFalse(any(a.GetNumRadicalElectrons() or a.GetNumImplicitHs() for a in mol.GetAtoms()))
        self.assertIsNone(mechanism["energyProfile"]["activationEnergies"])
        self.assertTrue(mechanism["energyProfile"]["qualitative"])

    def test_sn2_has_one_concerted_step_and_exact_roles(self):
        for substrate in ("CBr", "CCCl", "CC(Br)CC"):
            _, diagram, mechanism = self.mechanism(substrate, "hydroxide", "SN2")
            self.check_steps(diagram, mechanism)
            self.assertEqual(len(mechanism["steps"]), 1)
            step = mechanism["steps"][0]
            self.assertTrue(step["concerted"]); self.assertIsNone(step["intermediate"])
            atoms = {a["mapId"]: a for a in diagram["atoms"] if a["side"] == "reactants"}
            roles = mechanism["roles"]
            self.assertEqual(atoms[roles["nucleophile"]]["element"], "O")
            self.assertEqual(atoms[roles["electrophilic-carbon"]]["element"], "C")
            self.assertIn(atoms[roles["leaving-group"]]["element"], ("Br", "Cl"))
            self.assertEqual(len(step["electronMoves"]), 2)

    def test_e2_requires_beta_h(self):
        self.assertFalse(any(r["mechanism"] == "E2" for r in self.options("CBr", "hydroxide")["reactions"]))

    def test_each_e2_constitutional_product_has_its_actual_beta_h(self):
        options = [r for r in self.options("CC(Br)CC", "hydroxide")["reactions"] if r["mechanism"] == "E2"]
        self.assertEqual({r["productSmiles"] for r in options}, {canonical("C=CCC"), canonical("CC=CC")})
        beta_maps = set()
        for option in options:
            diagram = service.reaction_diagram(option["id"], {"smiles": "CC(Br)CC"}, "hydroxide")
            m = diagram["mechanism"]; self.check_steps(diagram, m)
            roles = m["roles"]; beta_maps.add(roles["beta-carbon"])
            broken = {frozenset(c["atomMaps"]) for c in m["steps"][0]["bondsBroken"]}
            self.assertIn(frozenset([roles["beta-carbon"], roles["beta-hydrogen"]]), broken)
            formed_pi = [c for c in m["steps"][0]["bondOrderChanges"] if set(c["atomMaps"]) == {roles["alpha-carbon"], roles["beta-carbon"]}]
            self.assertEqual(formed_pi[0]["after"], 2)
            self.assertEqual(len(m["steps"]), 1); self.assertEqual(len(m["steps"][0]["electronMoves"]), 3)
        self.assertEqual(len(beta_maps), 2)

    def test_sn1_has_mapped_carbocation_oxonium_and_explicit_proton_transfer(self):
        _, diagram, m = self.mechanism("CC(C)(C)Cl", "water", "SN1")
        self.check_steps(diagram, m)
        self.assertEqual(len(m["steps"]), 3)
        c = m["roles"]["electrophilic-carbon"]; o = m["roles"]["nucleophile"]
        charges = [{a["mapId"]: a["formalCharge"] for a in s["state"]["atoms"]} for s in m["steps"]]
        self.assertEqual(charges[0][c], 1); self.assertEqual(charges[1][o], 1); self.assertEqual(charges[2][o], 0)
        self.assertEqual(m["steps"][0]["intermediate"]["kind"], "Intermediate")
        self.assertIn("Proton transfer", m["steps"][2]["title"])

    def test_e1_elimination_couples_h_removal_and_pi_formation(self):
        _, diagram, m = self.mechanism("CCC(Cl)(C)CC", "water", "E1")
        self.check_steps(diagram, m)
        self.assertEqual(len(m["steps"]), 2)
        self.assertIsNotNone(m["steps"][0]["intermediate"])
        self.assertIsNone(m["steps"][1]["intermediate"])
        self.assertTrue(m["steps"][1]["concerted"])
        self.assertEqual(m["energyProfile"]["intermediates"], 1)
        options = [r for r in self.options("CCC(Cl)(C)CC", "water")["reactions"] if r["mechanism"] == "E1"]
        self.assertEqual(len(options), 2)
        for option in options:
            mechanism = service.reaction_diagram(option["id"], {"smiles": "CCC(Cl)(C)CC"}, "water")["mechanism"]
            roles = mechanism["roles"]; step = mechanism["steps"][1]
            self.assertTrue(any(set(c["atomMaps"]) == {roles["beta-carbon"], roles["beta-hydrogen"]} for c in step["bondsBroken"]))
            self.assertTrue(any(set(c["atomMaps"]) == {roles["alpha-carbon"], roles["beta-carbon"]} and c["after"] == 2 for c in step["bondOrderChanges"]))

    def test_other_families_have_no_invented_mechanism(self):
        option = self.options("C=C", "hydrogen")["reactions"][0]
        self.assertIsNone(service.reaction_diagram(option["id"], {"smiles": "C=C"}, "hydrogen")["mechanism"])

    def test_oxidation_requires_explicit_stage_and_water(self):
        for conditions in (None, {"oxidationStage": "first", "solvent": "aqueous-protic"}, {"oxidationStage": "further", "solvent": "dry"}):
            self.assertFalse(self.options("CCC=O", "sodium-hypochlorite", conditions)["reactions"])

    def test_further_oxidation_generalizes_and_is_mapped_balanced(self):
        context = {"oxidationStage": "further", "solvent": "aqueous-protic"}
        for substrate, product in (("CC=O", "CC(=O)O"), ("CCC=O", "CCC(=O)O"), ("O=Cc1ccccc1", "O=C(O)c1ccccc1"), ("C=O", "O=CO")):
            result = self.options(substrate, "sodium-hypochlorite", context)["reactions"]
            self.assertEqual(result[0]["productSmiles"], canonical(product))
            self.assertTrue(result[0]["stoichiometry"]["balanced"])
            self.assertEqual(result[0]["reasoning"]["label"], "Possible")
            self.assertIn("neutral reporting form", next(f["explanation"] for f in result[0]["reasoning"]["factors"] if f["factor"] == "oxidation-stage"))
            diagram = service.reaction_diagram(result[0]["id"], {"smiles": substrate}, "sodium-hypochlorite", context)
            before = {a["mapId"]: a["element"] for a in diagram["atoms"] if a["side"] == "reactants"}
            after = {a["mapId"]: a["element"] for a in diagram["atoms"] if a["side"] == "products"}
            self.assertEqual(before, after)
            self.assertEqual(result[0]["byproducts"][0]["formula"], "NaCl")

    def test_alcohol_stages_primary_secondary_tertiary_and_no_automatic_acid(self):
        first = {"oxidationStage": "first", "solvent": "aqueous-protic"}
        further = {"oxidationStage": "further", "solvent": "aqueous-protic"}
        self.assertEqual(self.options("CCO", "sodium-hypochlorite", first)["reactions"][0]["productSmiles"], "CC=O")
        self.assertEqual(self.options("CC(O)C", "sodium-hypochlorite", first)["reactions"][0]["productSmiles"], "CC(C)=O")
        self.assertFalse(self.options("CC(C)(C)O", "sodium-hypochlorite", first)["reactions"])
        self.assertFalse(self.options("CCO", "sodium-hypochlorite", further)["reactions"])
        self.assertFalse(self.options("CC(C)=O", "sodium-hypochlorite", further)["reactions"])

    def test_stale_further_oxidation_cannot_run_after_condition_change(self):
        first = {"oxidationStage": "further", "solvent": "aqueous-protic"}
        option = self.options("CC=O", "sodium-hypochlorite", first)["reactions"][0]
        with self.assertRaises(service.ChemistryError): service.reaction_diagram(option["id"], {"smiles": "CC=O"}, "sodium-hypochlorite", {})
        with self.assertRaises(service.ChemistryError): service.run_curated_reaction(option["id"], {"smiles": "CC=O"}, "sodium-hypochlorite", {})

    def test_further_oxidation_run_reuses_exact_product_and_full_salt_mass(self):
        context = {"oxidationStage": "further", "solvent": "aqueous-protic"}
        option = self.options("CCC=O", "sodium-hypochlorite", context)["reactions"][0]
        result = service.run_curated_reaction(option["id"], {"smiles": "CCC=O"}, "sodium-hypochlorite", context)
        self.assertTrue(result["balanced"])
        self.assertEqual(result["product"]["smiles"], canonical("CCC(=O)O"))
        self.assertEqual(result["product"]["formula"], "C3H6O2")
        oxidant = next(r for r in option["stoichiometry"]["reactants"] if r["inputSlot"] == 1)
        self.assertAlmostEqual(oxidant["molarMass"], 74.442, places=2)

    def test_solvent_water_does_not_change_net_calculator_amounts(self):
        option, _, m = self.mechanism("CC(C)(C)Cl", "water", "E1")
        self.assertEqual(list(option["equationReactants"]), ["tert-butyl-chloride"])
        self.assertTrue(m["solventSpecies"])
        self.assertEqual(len(option["stoichiometry"]["reactants"]), 1)


if __name__ == "__main__": unittest.main()

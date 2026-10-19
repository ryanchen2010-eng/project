"""Phase 1: independent ester expectations through public match/diagram/run.

No preset identities or internal-only transform success can satisfy coverage.
Tests include the production HTTP gateway, exact map/balance invariants, stereo
serialization/3D boundaries, and fail-closed controls for scope and corruption.
"""
import unittest
from unittest.mock import patch
from rdkit import Chem
from rdkit.Chem import Descriptors, rdMolDescriptors
from server import chemistry_server as service, ester_rules, molecular_graph as graph, reaction_engine as engine
from server.reaction_diagrams import _species, _combine, _identity


def canonical(smiles):
    return Chem.MolToSmiles(Chem.MolFromSmiles(smiles))


def deprotonated_acid(smiles):
    # Independent expected acid ionization, not the production ester edit.
    mol = Chem.MolFromSmiles(smiles)
    matches = mol.GetSubstructMatches(Chem.MolFromSmarts("[CX3](=[OX1])[OX2H1]"))
    if len(matches) != 1:
        raise AssertionError("This expectation must contain exactly one acid OH.")
    oxygen = mol.GetAtomWithIdx(matches[0][2])
    oxygen.SetFormalCharge(-1)
    oxygen.SetNumExplicitHs(0)
    oxygen.SetNoImplicit(True)
    Chem.SanitizeMol(mol)
    return Chem.MolToSmiles(mol)


ACID = {"solvent": "aqueous-protic", "catalyst": "acid"}
BASE = {"solvent": "aqueous-protic", "catalyst": "none"}


class EsterPhase1Tests(unittest.TestCase):
    def options(self, substrate, basic=False, reagent=None, conditions=None):
        a = {"name": "Independent ester input", "smiles": substrate}
        b = reagent or ("hydroxide" if basic else "water")
        cond = conditions if conditions is not None else BASE if basic else ACID
        mechanism = "Ester saponification" if basic else "Ester hydrolysis"
        match = service.match_reactions(a, b, cond)
        return a, b, cond, [r for r in match["reactions"] if r["mechanism"] == mechanism]

    def check(self, substrate, acid, alcohol=None, basic=False, reagent=None):
        expected = deprotonated_acid(acid) if basic else acid
        a, b, cond, options = self.options(substrate, basic, reagent)
        self.assertEqual(len(options), 1)
        r = options[0]
        self.assertEqual(r["productSmiles"], canonical(expected))
        self.assertTrue(r["stoichiometry"]["balanced"])
        self.assertEqual(r["assessment"]["state"], "aligned")
        d = service.reaction_diagram(r["id"], a, b, cond)
        self.assertIn("<svg", d["svg"])
        self.assertTrue(d["highlightsAvailable"])
        self.assertEqual(d["products"][0]["smiles"], canonical(expected))
        self.assertEqual([p["smiles"] for p in d["products"][1:]], [] if alcohol is None else [canonical(alcohol)])
        before = {v["mapId"]: v for v in d["atoms"] if v["side"] == "reactants"}
        after = {v["mapId"]: v for v in d["atoms"] if v["side"] == "products"}
        self.assertEqual(len(before), len([v for v in d["atoms"] if v["side"] == "reactants"]))
        self.assertEqual({m: a["element"] for m, a in before.items()}, {m: a["element"] for m, a in after.items()})
        self.assertEqual(sum(a["formalCharge"] for a in before.values()), sum(a["formalCharge"] for a in after.values()))
        self.assertEqual(sum(a["formalCharge"] for a in after.values()), -1 if basic else 0)
        self.assertEqual(len(d["atomMap"]), len(before))
        self.assertEqual(len(d["bondsBroken"]), 2)
        self.assertEqual(len(d["bondsFormed"]), 2)
        self.assertEqual(d["bondOrderChanges"], [])
        acyl, leaving, incoming = r["site"]["atomMaps"]
        self.assertEqual(after[incoming]["formalCharge"], -1 if basic else 0)
        self.assertEqual(after[leaving]["formalCharge"], 0)
        self.assertTrue(any(set(c["atomMaps"]) == {acyl, leaving} for c in d["bondsBroken"]))
        self.assertTrue(any(set(c["atomMaps"]) == {acyl, incoming} for c in d["bondsFormed"]))
        if alcohol is None:
            self.assertEqual({m["productIndex"] for m in d["atomMap"]}, {0})
        mass = Descriptors.MolWt(Chem.MolFromSmiles(expected))
        self.assertAlmostEqual(r["stoichiometry"]["product"]["molarMass"], mass, places=6)
        self.assertEqual(r["productFormula"], rdMolDescriptors.CalcMolFormula(Chem.MolFromSmiles(expected)))
        self.assertEqual([x["coefficient"] for x in r["stoichiometry"]["reactants"]], [1, 1])
        self.assertEqual(r["stoichiometry"]["product"]["coefficient"], 1)
        result = service.run_curated_reaction(r["id"], a, b, cond)
        p = result["product"]
        self.assertEqual(p["smiles"], canonical(expected))
        if basic:
            self.assertEqual(p["representation"], "2d-only")
            self.assertNotIn("molfile", p)
            self.assertIn("charged", p["reason"])
        else:
            self.assertEqual(p["representation"], "3d")
            shape = Chem.MolFromMolBlock(p["molfile"], removeHs=False)
            # A 3D conformer depicts one possible shape, not an assignment of
            # previously unspecified stereochemistry. Require exact specified
            # features, and connectivity for genuinely unspecified examples.
            if any(i.specified == Chem.StereoSpecified.Unspecified for i in Chem.FindPotentialStereo(Chem.MolFromSmiles(expected))):
                shape_identity = Chem.MolFromSmiles(_identity(shape))
                self.assertEqual(Chem.MolToSmiles(shape_identity, isomericSmiles=False), Chem.MolToSmiles(Chem.MolFromSmiles(expected), isomericSmiles=False))
            else:
                self.assertEqual(_identity(shape), canonical(expected))
            self.assertEqual([(v["atomIndex"], v["mapId"], v["element"]) for v in d["atoms"] if v["side"] == "products" and v["speciesIndex"] == 0],
                             [(v["index"], v["mapId"], v["element"]) for v in p["atomLinks"]])
        return r, d, result

    def test_five_six_membered_and_branched_lactones_connected(self):
        rows = [("O=C1OCCC1", "O=C(O)CCCO"), ("O=C1OCCCC1", "O=C(O)CCCCO"),
                ("O=C1OC(C)CC1", "O=C(O)CCC(O)C"), ("O=C1OCC(C)C1", "O=C(O)CC(C)CO")]
        for substrate, acid in rows:
            for basic in (False, True):
                with self.subTest(substrate=substrate, basic=basic):
                    self.check(substrate, acid, basic=basic)

    def test_phenyl_substituted_aryl_and_aromatic_acyl_esters(self):
        rows = [("CC(=O)Oc1ccccc1", "CC(=O)O", "Oc1ccccc1"),
                ("CCC(=O)Oc1ccc(C)cc1", "CCC(=O)O", "Oc1ccc(C)cc1"),
                ("CC(=O)Oc1ccc(OC)cc1", "CC(=O)O", "Oc1ccc(OC)cc1"),
                ("O=C(Oc1ccccc1)c1ccccc1", "O=C(O)c1ccccc1", "Oc1ccccc1"),
                ("CC(=O)Oc1cccc2ccccc12", "CC(=O)O", "Oc1cccc2ccccc12")]
        for substrate, acid, phenol in rows:
            for basic in (False, True):
                with self.subTest(substrate=substrate, basic=basic):
                    r, d, _ = self.check(substrate, acid, phenol, basic)
                    if phenol == "Oc1ccccc1":
                        self.assertEqual(r["byproducts"][0]["name"], "Phenol")
                    self.assertEqual(d["products"][1]["formula"], rdMolDescriptors.CalcMolFormula(Chem.MolFromSmiles(phenol)))

    def test_existing_branched_cyclic_alkoxy_and_other_spectators(self):
        rows = [("CC(C)C(=O)OCC(C)C", "CC(C)C(=O)O", "CC(C)CO"),
                ("CCCC(=O)OC1CCCCC1", "CCCC(=O)O", "OC1CCCCC1"),
                ("COc1ccc(C(=O)OCC)cc1", "COc1ccc(C(=O)O)cc1", "CCO"),
                ("OCCCC(=O)OCC", "OCCCC(=O)O", "CCO")]
        for substrate, acid, alcohol in rows:
            for basic in (False, True):
                with self.subTest(substrate=substrate, basic=basic):
                    self.check(substrate, acid, alcohol, basic)

    def test_specified_tetrahedral_stereo_and_alkene_retained_in_both_fragments(self):
        rows = [("CC[C@H](C)CC(=O)OCC", "CC[C@H](C)CC(=O)O", "CCO"),
                ("CC[C@@H](C)CC(=O)OCC", "CC[C@@H](C)CC(=O)O", "CCO"),
                ("CC(=O)O[C@H](C)CC", "CC(=O)O", "O[C@H](C)CC"),
                ("O=C1OC[C@H](C)C1", "O=C(O)C[C@@H](C)CO", None),
                ("O=C1O[C@H](C)CC1", "O=C(O)CC[C@H](O)C", None),
                ("C/C=C/CC(=O)OCC", "C/C=C/CC(=O)O", "CCO"),
                ("CC(=O)OC/C=C\\C", "CC(=O)O", "OC/C=C\\C")]
        for substrate, acid, alcohol in rows:
            for basic in (False, True):
                with self.subTest(substrate=substrate, basic=basic):
                    r, _, _ = self.check(substrate, acid, alcohol, basic)
                    self.assertIn("validated acyl-cleavage edit", r["information"]["stereochemistry"]["effect"])
                    self.assertIn("retention", r["information"]["capabilities"]["stereochemistry"])

    def test_unspecified_stereo_is_not_invented(self):
        for substrate in ("O=C1OC(C)CC1", "CC(C)CC(=O)OC(C)CC", "CC=CCC(=O)OCC"):
            for basic in (False, True):
                a, b, cond, options = self.options(substrate, basic)
                self.assertTrue(options)
                d = service.reaction_diagram(options[0]["id"], a, b, cond)
                for p in d["products"]:
                    mol = Chem.MolFromSmiles(p["smiles"])
                    self.assertFalse(any(a.GetChiralTag() != Chem.ChiralType.CHI_UNSPECIFIED for a in mol.GetAtoms()))
                    self.assertFalse(any(b.GetStereo() != Chem.BondStereo.STEREONONE for b in mol.GetBonds()))

    def test_retention_can_change_cip_letter_without_physical_inversion(self):
        # Hydrolyzing the ethyl-ester arm swaps the relative CIP priorities of
        # the two carbon chains. A retained center becomes S, not R.
        substrate = "CCOC(=O)C[C@H](C)CC(=O)OC"
        for basic in (False, True):
            a, b, cond, options = self.options(substrate, basic)
            expectations = ["O=C(O)C[C@H](C)CC(=O)OC", "CCOC(=O)C[C@H](C)CC(=O)O"]
            if basic:
                expectations = [deprotonated_acid(s) for s in expectations]
            self.assertEqual({r["productSmiles"] for r in options}, {canonical(s) for s in expectations})
            self.assertEqual(len(options), 2)
            for r in options:
                stereo = r["information"]["stereochemistry"]
                self.assertEqual(stereo["reactant"]["chiralCenters"][0]["assignment"], "R")
                if r["productSmiles"] == canonical(expectations[0]):
                    self.assertEqual(stereo["product"]["chiralCenters"][0]["assignment"], "S")
                diagram = service.reaction_diagram(r["id"], a, b, cond)
                self.assertEqual(diagram["products"][0]["smiles"], r["productSmiles"])

    def test_asymmetric_diester_is_one_site_per_option_not_complete_hydrolysis(self):
        substrate = "COC(=O)CCC(=O)OCC"
        for basic in (False, True):
            a, b, cond, options = self.options(substrate, basic)
            ending = "[O-]" if basic else "O"
            expected = {canonical(f"COC(=O)CCC(=O){ending}"): canonical("CCO"),
                        canonical(f"O=C({ending})CCC(=O)OCC"): canonical("CO")}
            self.assertEqual({r["productSmiles"] for r in options}, set(expected))
            self.assertEqual(len(options), 2)
            self.assertEqual(len({r["id"] for r in options}), 2)
            for r in options:
                d = service.reaction_diagram(r["id"], a, b, cond)
                self.assertEqual(d["products"][1]["smiles"], expected[r["productSmiles"]])
                self.assertEqual(len(graph.find_esters(Chem.MolFromSmiles(r["productSmiles"]))), 1)
                self.assertTrue(r["stoichiometry"]["balanced"])
                self.assertEqual(r["stoichiometry"]["reactants"][1]["coefficient"], 1)

    def test_di_aryl_ester_sites_preserve_the_unselected_ester(self):
        substrate = "CC(=O)Oc1ccc(OC(=O)CC)cc1"
        for basic in (False, True):
            a, b, cond, options = self.options(substrate, basic)
            self.assertEqual(len(options), 2)
            acids = {canonical(x) for x in ("CC(=O)[O-]", "CCC(=O)[O-]")} if basic else {canonical(x) for x in ("CC(=O)O", "CCC(=O)O")}
            self.assertEqual({r["productSmiles"] for r in options}, acids)
            for r in options:
                d = service.reaction_diagram(r["id"], a, b, cond)
                self.assertEqual(len(graph.find_esters(Chem.MolFromSmiles(d["products"][1]["smiles"]))), 1)
                self.assertTrue(r["stoichiometry"]["balanced"])

    def test_unsupported_rings_false_esters_and_unrelated_scope_guards(self):
        controls = ["O=C1OCC1", "O=C1OCCCCC1", "O=C1OCCCCCC1", "O=C1OCC=CC1",
                    "O=C1OCOC1", "O=C1OC2CCCC2C1", "O=C1OCC2(CCCCC2)C1",
                    "CC(=O)Oc1ccoc1", "CC(=O)OC=C", "COC(=O)OC", "CC(=O)OC(=O)C",
                    "CC(=O)N", "COC", "CC(=O)O", "NCCCC(=O)OCC", "FCCCC(=O)OCC"]
        for substrate in controls:
            self.assertIsNotNone(Chem.MolFromSmiles(substrate))
            for basic in (False, True):
                with self.subTest(substrate=substrate, basic=basic):
                    self.assertEqual(self.options(substrate, basic)[3], [])
        # Each later consumer needs its own policy. Phase 2C alcohol oxidation
        # is opted in; the separate aldehyde-oxidation policy is not.
        result = service.match_reactions({"smiles": "CC[C@H](C)CC=O"}, "sodium-hypochlorite", {"solvent": "aqueous-protic", "oxidationStage": "further"})
        self.assertFalse(result["reactions"])
        self.assertFalse(service.match_reactions({"smiles": "CC(=O)O"}, {"smiles": "CN"})["reactions"])

    def test_wrong_reagents_invalid_structures_and_enhanced_stereo_rejected(self):
        for reagent in ("hydrogen", "sodium-hypochlorite"):
            r = service.match_reactions({"smiles": "O=C1OCCC1"}, reagent)
            self.assertFalse(any(x["mechanism"] in ester_rules.PATHWAYS for x in r["reactions"]))
        for substrate in ("not-smiles", "CC(=O)(OCC)C", "CC(=O)[O-]", "CC(=O)OCC.O",
                          "CC[C@H](C)CC(=O)OCC |&1:2|", "CC[C@H](C)CC(=O)OCC |o1:2|"):
            with self.subTest(substrate=substrate), self.assertRaises(service.ChemistryError):
                service.match_reactions({"smiles": substrate}, "water", ACID)

    def test_map_parity_validator_rejects_inversion_loss_and_new_assignments(self):
        item, _ = _species("a", {"name": "Mapped stereo", "smiles": "CC[C@H](C)CC(=O)OCC"}, 1)
        before = item["mol"]
        ester_rules.validate_retained_stereo(before, Chem.Mol(before))
        center = next(a.GetIdx() for a in before.GetAtoms() if a.GetChiralTag() in ester_rules.TETRAHEDRAL)
        for mutation in ("invert", "erase"):
            after = Chem.Mol(before)
            if mutation == "invert": after.GetAtomWithIdx(center).InvertChirality()
            else: after.GetAtomWithIdx(center).SetChiralTag(Chem.ChiralType.CHI_UNSPECIFIED)
            with self.assertRaises(ValueError): ester_rules.validate_retained_stereo(before, after)
        unassigned = Chem.Mol(before)
        unassigned.GetAtomWithIdx(center).SetChiralTag(Chem.ChiralType.CHI_UNSPECIFIED)
        with self.assertRaises(ValueError): ester_rules.validate_retained_stereo(unassigned, before)
        renumbered = Chem.RenumberAtoms(before, list(reversed(range(before.GetNumAtoms()))))
        ester_rules.validate_retained_stereo(before, renumbered)
        item, _ = _species("a", {"name": "Mapped alkene", "smiles": "C/C=C/CC(=O)OCC"}, 1)
        altered = Chem.Mol(item["mol"])
        double = next(b for b in altered.GetBonds() if b.GetStereo() in ester_rules.DOUBLE_STEREO)
        double.SetStereo(Chem.BondStereo.STEREOZ)
        with self.assertRaises(ValueError): ester_rules.validate_retained_stereo(item["mol"], altered)

    def test_validation_failures_are_not_public_reaction_options(self):
        with patch("server.ester_rules.validate_retained_stereo", side_effect=ValueError("Invalid retention")):
            self.assertFalse(self.options("CC[C@H](C)CC(=O)OCC")[3])
        with patch("server.ester_rules.validate_cleavage", side_effect=ValueError("Invalid protonation")):
            self.assertFalse(self.options("O=C1OCCC1", basic=True)[3])

    def test_validation_rejects_changes_outside_the_selected_site(self):
        substrate, next_map = _species("a", {"name": "Ordinary ester", "smiles": "CCCCC(=O)OCC"}, 1)
        water, _ = _species("b", {"name": "Water", "smiles": "O"}, next_map)
        site = graph.find_esters(substrate["mol"])[0]
        before = _combine([substrate, water])
        fragments = engine.transform("Ester hydrolysis", [substrate, water], site)
        after = _combine([{"mol": f} for f in fragments])
        ester_rules.validate_cleavage(before, after, substrate["mol"], site, water["mol"], "Ester hydrolysis")
        altered = Chem.Mol(after)
        unselected = next(b for b in altered.GetBonds() if b.GetBeginAtom().GetSymbol() == b.GetEndAtom().GetSymbol() == "C")
        unselected.SetBondType(Chem.BondType.DOUBLE)
        with self.assertRaisesRegex(ValueError, "unselected bond"):
            ester_rules.validate_cleavage(before, altered, substrate["mol"], site, water["mol"], "Ester hydrolysis")

    def test_full_salt_and_reverse_order_keep_charge_and_calculation_mass(self):
        for symbol in ("Na", "K"):
            for substrate in ("O=C1OCCC1", "CC(=O)Oc1ccccc1"):
                salt = {"name": "Entered full salt", "smiles": f"[{symbol}+].[OH-]"}
                a, b, cond, options = self.options(substrate, True, salt)
                r = options[0]
                self.assertEqual(r["productFormula"][-1], "-")
                self.assertAlmostEqual(r["stoichiometry"]["reactants"][1]["molarMass"], Descriptors.MolWt(Chem.MolFromSmiles(salt["smiles"])), places=6)
                reverse = next(x for x in service.match_reactions(b, a, cond)["reactions"] if x["mechanism"] == "Ester saponification")
                self.assertEqual(reverse["productSmiles"], r["productSmiles"])
                self.assertEqual(reverse["stoichiometry"]["reactants"][0]["inputSlot"], 0)
                self.assertAlmostEqual(reverse["stoichiometry"]["reactants"][0]["molarMass"], r["stoichiometry"]["reactants"][1]["molarMass"], places=6)
                self.assertEqual(service.reaction_diagram(r["id"], a, b, cond)["svg"], service.reaction_diagram(reverse["id"], b, a, cond)["svg"])

    def test_acid_catalyst_setting_does_not_invent_post_saponification_workup(self):
        a, b, cond, options = self.options("O=C1OCCC1", True, conditions=ACID)
        r = options[0]
        self.assertNotEqual(r["assessment"]["state"], "aligned")
        self.assertEqual(r["productSmiles"], canonical("O=C([O-])CCCO"))
        self.assertIn("No neutral acid work-up", r["explanation"])
        result = service.run_curated_reaction(r["id"], a, b, cond)
        self.assertEqual(result["product"]["representation"], "2d-only")

    def test_real_public_http_gateway_uses_the_same_match_diagram_run(self):
        from server.production_app import create_app
        origin = "https://ester-phase1.example.test"
        password = "Ester-phase1-synthetic-password"
        app = create_app({"TRIAL_PASSWORD": password,
                          "SESSION_SECRET": "5a793bc832adc647a5f382190dead01d19f58f6fa0c9246eb8b2b31f0f419b60",
                          "PUBLIC_ORIGIN": origin, "FRAME_ANCESTORS": "https://site.example.test",
                          "DIST_DIR": "/private/tmp/ester-phase1-no-static-needed", "TESTING": True}, chemistry_backend=service)
        client = app.test_client()
        login = client.post("/login", base_url=origin, headers={"Origin": origin}, data={"password": password})
        self.assertEqual(login.status_code, 303)
        for substrate in ("O=C1OCCC1", "CC(=O)Oc1ccccc1"):
            for basic in (False, True):
                body = {"reactantA": {"name": "Public entered ester", "smiles": substrate},
                        "reactantB": "hydroxide" if basic else "water", "conditions": BASE if basic else ACID}
                match = client.post("/api/reactions/match", base_url=origin, headers={"Origin": origin}, json=body)
                self.assertEqual(match.status_code, 200)
                options = match.get_json()["reactions"]
                self.assertEqual(len(options), 1)
                body["reactionId"] = options[0]["id"]
                diagram = client.post("/api/reactions/diagram", base_url=origin, headers={"Origin": origin}, json=body)
                result = client.post("/api/reactions/run", base_url=origin, headers={"Origin": origin}, json=body)
                self.assertEqual(diagram.status_code, 200)
                self.assertEqual(result.status_code, 200)
                self.assertEqual(result.get_json()["product"]["smiles"], diagram.get_json()["products"][0]["smiles"])
                self.assertEqual(result.get_json()["product"]["representation"], "2d-only" if basic else "3d")


if __name__ == "__main__":
    unittest.main()

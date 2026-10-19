"""Phase 2: independent expectations through public match -> diagram -> run.

Only alkene hydrogenation adopts the new policy. Structure identities below
are explicit expectations, not products computed by the production edit.
"""
import unittest
from unittest.mock import patch
from rdkit import Chem
from rdkit.Chem import Descriptors, rdMolDescriptors
from server import chemistry_server as service, hydrogenation_rule as rule
from server import reaction_compatibility as compatibility, molecular_graph as graph, reaction_engine as engine
from server.reaction_diagrams import _species, _combine, _identity


METAL = {"catalyst": "metal"}


def canonical(smiles):
    return Chem.MolToSmiles(Chem.MolFromSmiles(smiles))


def bond_states(molecule):
    # Independent map-pair comparison, not the production contract helper.
    return {tuple(sorted((b.GetBeginAtom().GetAtomMapNum(), b.GetEndAtom().GetAtomMapNum()))): b.GetBondTypeAsDouble()
            for b in molecule.GetBonds()}


class HydrogenationCompatibilityTests(unittest.TestCase):
    def options(self, smiles, reagent="hydrogen", conditions=None):
        a = {"name": "Independent substrate", "smiles": smiles}
        result = service.match_reactions(a, reagent, METAL if conditions is None else conditions)
        return a, [r for r in result["reactions"] if r["mechanism"] == "Hydrogenation"], result

    def check_option(self, a, option, expected, *, reagent="hydrogen", conditions=METAL):
        self.assertEqual(option["productSmiles"], canonical(expected))
        self.assertEqual(option["byproducts"], [])
        self.assertTrue(option["stoichiometry"]["balanced"])
        self.assertEqual(option["assessment"]["state"], "aligned")
        self.assertEqual(option["productFormula"], rdMolDescriptors.CalcMolFormula(Chem.MolFromSmiles(expected)))
        self.assertAlmostEqual(option["stoichiometry"]["product"]["molarMass"], Descriptors.MolWt(Chem.MolFromSmiles(expected)), places=6)
        self.assertEqual([v["coefficient"] for v in option["stoichiometry"]["reactants"]], [1, 1])
        self.assertEqual(option["stoichiometry"]["product"]["coefficient"], 1)
        d = service.reaction_diagram(option["id"], a, reagent, conditions)
        self.assertEqual([p["smiles"] for p in d["products"]], [canonical(expected)])
        self.assertIn("<svg", d["svg"])
        self.assertTrue(d["highlightsAvailable"])
        before_rows = [v for v in d["atoms"] if v["side"] == "reactants"]
        after_rows = [v for v in d["atoms"] if v["side"] == "products"]
        before = {v["mapId"]: (v["element"], v["formalCharge"]) for v in before_rows}
        after = {v["mapId"]: (v["element"], v["formalCharge"]) for v in after_rows}
        self.assertEqual(len(before_rows), len(before))
        self.assertEqual(len(after_rows), len(after))
        self.assertEqual(before, after)
        self.assertEqual(sum(v[1] for v in after.values()), 0)
        self.assertEqual(len(d["atomMap"]), len(before))
        self.assertEqual(len(d["bondsBroken"]), 1)
        self.assertEqual(d["bondsBroken"][0]["atoms"], ["H", "H"])
        self.assertEqual(len(d["bondsFormed"]), 2)
        self.assertTrue(all(set(v["atoms"]) == {"C", "H"} for v in d["bondsFormed"]))
        self.assertEqual(len(d["bondOrderChanges"]), 1)
        change = d["bondOrderChanges"][0]
        self.assertEqual((change["before"], change["after"]), (2, 1))
        self.assertEqual(set(change["atomMaps"]), set(option["site"]["atomMaps"]))
        report = option["compatibility"]
        self.assertTrue(report["eligible"])
        self.assertEqual(report["substrateSiteMaps"], option["site"]["atomMaps"])
        self.assertEqual(set(report["reactiveAtomMaps"]), {m for e in report["editContract"] for m in e["atomMaps"]})
        self.assertTrue(set(report["reactiveAtomMaps"]) <= before.keys())
        self.assertTrue(all(set(g["atomMaps"]) <= before.keys() for g in report["groups"]))
        self.assertEqual(set(report["validation"].values()), {"verified"})
        self.assertEqual({(tuple(sorted(e["atomMaps"])), e["before"], e["after"]) for e in report["editContract"]},
                         {(tuple(sorted(e["atomMaps"])), e["before"], e["after"]) for e in d["changes"]})
        result = service.run_curated_reaction(option["id"], a, reagent, conditions)
        p = result["product"]
        self.assertEqual(p["smiles"], canonical(expected))
        self.assertEqual(p["representation"], "3d")
        self.assertEqual([(v["atomIndex"], v["mapId"], v["element"]) for v in after_rows],
                         [(v["index"], v["mapId"], v["element"]) for v in p["atomLinks"]])
        shape = Chem.MolFromMolBlock(p["molfile"], removeHs=False)
        expected_mol = Chem.MolFromSmiles(expected)
        if any(i.specified == Chem.StereoSpecified.Unspecified for i in Chem.FindPotentialStereo(expected_mol)):
            # One rendered conformer isn't an assignment of an unspecified
            # stereochemical outcome. The exact net SMILES above stays unsigned.
            self.assertEqual(Chem.MolToSmiles(Chem.MolFromSmiles(_identity(shape)), isomericSmiles=False),
                             Chem.MolToSmiles(expected_mol, isomericSmiles=False))
        else:
            self.assertEqual(_identity(shape), canonical(expected))
        return d, result

    def check(self, substrate, product):
        a, options, _ = self.options(substrate)
        self.assertEqual(len(options), 1)
        self.check_option(a, options[0], product)
        return options[0]

    def test_simple_branched_and_cyclic_regressions(self):
        for a, p in [("C=C", "CC"), ("C=CCCC", "CCCCC"), ("C=C(C)CCC", "CC(C)CCC"),
                     ("CC=C(C)C", "CCC(C)C"), ("C1=CCCC1", "C1CCCC1"), ("C1=CCCCCC1", "C1CCCCCC1")]:
            with self.subTest(substrate=a): self.check(a, p)

    def test_screened_remote_alcohols_branched_polyols_and_cyclic(self):
        for a, p in [("C=CCCCO", "CCCCCO"), ("C=CCCO", "CCCCO"), ("C=C(C)CCCO", "CC(C)CCCO"),
                     ("C=CCCC(O)C", "CCCCC(O)C"), ("C=CCC(C)(O)C", "CCCC(C)(O)C"),
                     ("C=CCCC(O)CO", "CCCCC(O)CO"), ("C1=CCC(O)CC1", "OC1CCCCC1")]:
            with self.subTest(substrate=a):
                r = self.check(a, p)
                preserved = [g for g in r["compatibility"]["groups"] if g["disposition"] == "preserved"]
                self.assertTrue(preserved)
                self.assertTrue(all(g["type"] == "alcohol" and g["distance"] >= 2 for g in preserved))
                self.assertIn("preserved", " ".join(g["explanation"] for g in preserved))
                self.assertNotEqual(r["productName"], "Alkane product")

    def test_distant_absolute_centers_and_combined_remote_alcohol_retained(self):
        for a, p in [("C=CC[C@H](C)CC", "CCC[C@H](C)CC"), ("C=CC[C@@H](C)CC", "CCC[C@@H](C)CC"),
                     ("C=CCCC[C@H](O)C", "CCCCC[C@H](O)C"),
                     ("C=CC[C@H](C)C[C@@H](O)C", "CCC[C@H](C)C[C@@H](O)C")]:
            with self.subTest(substrate=a):
                r = self.check(a, p)
                self.assertIn("validated retention", r["information"]["stereochemistry"]["effect"])
                centers = r["information"]["stereochemistry"]["product"]["chiralCenters"]
                self.assertTrue(centers)
                self.assertTrue(all(c["specified"] for c in centers))

    def test_retention_can_change_cip_letter_not_physical_configuration(self):
        for tag, before, after in [("@", "R", "S"), ("@@", "S", "R")]:
            a = f"C=CC[C{tag}H](CC)CC(C)C"
            r = self.check(a, f"CCC[C{tag}H](CC)CC(C)C")
            stereo = r["information"]["stereochemistry"]
            self.assertEqual(stereo["reactant"]["chiralCenters"][0]["assignment"], before)
            self.assertEqual(stereo["product"]["chiralCenters"][0]["assignment"], after)

    def test_multiple_isolated_sites_are_distinct_one_h2_options(self):
        for a, expected in [("C=CCCCCC=C", ["C=CCCCCCC", "C=CCCCCCC"]),
                            ("C=CCCCC(O)CCC=C", ["CCCCCC(O)CCC=C", "C=CCCCC(O)CCCC"])]:
            ref, options, _ = self.options(a)
            self.assertEqual(len(options), 2)
            self.assertEqual(len({r["id"] for r in options}), 2)
            self.assertEqual(len({tuple(r["site"]["atomMaps"]) for r in options}), 2)
            self.assertEqual(sorted(r["productSmiles"] for r in options), sorted(canonical(p) for p in expected))
            for r in options:
                self.check_option(ref, r, r["productSmiles"])
                self.assertEqual(len(graph.find_alkenes(Chem.MolFromSmiles(r["productSmiles"]))), 1)
                other = [g for g in r["compatibility"]["groups"] if g["disposition"] == "alternative-site"]
                self.assertEqual(len(other), 1)
                self.assertIn("not predict selective", other[0]["explanation"])

    def test_selected_ez_consumed_unselected_ez_preserved(self):
        self.check("CC/C=C/CC", "CCCCCC")
        substrate = "C/C=C/CC/C=C\\C"
        a, options, _ = self.options(substrate)
        expected = {canonical(p) for p in ("CCCCC/C=C\\C", "C/C=C/CCCCC")}
        self.assertEqual({r["productSmiles"] for r in options}, expected)
        self.assertEqual(len(options), 2)
        for r in options:
            self.check_option(a, r, r["productSmiles"])
            alkene = r["information"]["stereochemistry"]["product"]["alkenes"]
            self.assertEqual(len(alkene), 1)
            self.assertTrue(alkene[0]["specified"])

    def test_new_or_originally_unspecified_centers_remain_unassigned(self):
        for substrate in ("C=C(C)CC", "CC=C(C)CCC", "C=CCCC(O)C"):
            _, options, _ = self.options(substrate)
            self.assertTrue(options)
            for r in options:
                mol = Chem.MolFromSmiles(r["productSmiles"])
                self.assertFalse(any(a.GetChiralTag() != Chem.ChiralType.CHI_UNSPECIFIED for a in mol.GetAtoms()))
                if substrate == "CC=C(C)CCC":
                    self.assertEqual(r["productSmiles"], canonical("CCC(C)CCC"))
                    self.assertTrue(Chem.FindPotentialStereo(mol))  # An actual newly created, unassigned center.
                self.assertIn("new centers unassigned", r["information"]["capabilities"]["stereochemistry"])
                self.assertTrue(any("syn face" in x for x in r["information"]["limitations"]))

    def test_precise_competing_and_unvalidated_group_rejections(self):
        rows = [("C=CCO", "allylic/benzylic"), ("C=CC=C", "conjugated"), ("C=C=C", "cumulated"),
                ("C=CCCC=CC=C", "non-isolated C=C"), ("C=CCCC#C", "alkyne"),
                ("C=CCCC=O", "aldehyde"), ("C=CCC(=O)C", "ketone"),
                ("C=CCCC(=O)OCC", "ester"), ("C=CCCC(=O)O", "carboxylic acid"),
                ("C=CCCC(=O)N", "amide"), ("C=CCCCOC", "ether"), ("C=CCCC(OO)C", "peroxide"),
                ("C=CCCC(O)O", "multiple-oxygen"), ("C=CCC(OC)O", "hemiacetal"),
                ("C=Cc1ccccc1", "aromatic"), ("C=CCCCc1ccccc1", "Aromatic-containing"),
                ("C=CCCc1ccc(O)cc1", "phenol"), ("C=CCCCF", "F at substrate atom"),
                ("C=CCCCCl", "Cl at substrate atom"), ("C=CCCCN", "N at substrate atom"),
                ("C=CCCCS", "S at substrate atom"), ("C1=CCC1", "4-membered"),
                ("C=CCCC1CC1", "3-membered"), ("C=C[C@H](C)CC", "at/adjacent")]
        for substrate, text in rows:
            with self.subTest(substrate=substrate):
                _, options, result = self.options(substrate)
                self.assertEqual(options, [])
                self.assertIn(text, " ".join(result["unsupportedReasons"]))
                mol = Chem.MolFromSmiles(substrate)
                reports = [rule.assess(mol, site) for site in graph.find_alkenes(mol)]
                self.assertTrue(all(not r["eligible"] for r in reports))
                self.assertTrue(all(r["rejections"] for r in reports))
                self.assertTrue(all(v["code"] and v["category"] and v["message"] for r in reports for v in r["rejections"]))

    def test_center_that_ceases_to_be_stereogenic_is_not_silently_erased(self):
        # Reduction makes the two four-carbon arms identical. Retaining @ would
        # misrepresent a non-stereogenic atom; this increment rejects the option.
        _, options, result = self.options("C=CCC[C@H](C)CCCC")
        self.assertEqual(options, [])
        self.assertIn("no longer stereogenic", " ".join(result["unsupportedReasons"]))
        self.assertIn("not silently discarded", " ".join(result["unsupportedReasons"]))

    def test_wrong_reagents_and_invalid_electronic_or_stereo_inputs(self):
        for reagent in ("water", "hydroxide", "bromine"):
            self.assertEqual(self.options("C=CCCCO", reagent)[1], [])
        for substrate in ("not-smiles", "C=C.O", "C=CCCC[O-]", "C=CCC[CH2]", "C=CC[13CH2]CO",
                          "C=CC[C@H](C)CC |&1:3|", "C=CC[C@H](C)CC |o1:3|"):
            with self.subTest(substrate=substrate), self.assertRaises(service.ChemistryError):
                self.options(substrate)

    def test_explicit_atom_limit_includes_two_added_hydrogens(self):
        _, options, _ = self.options("C=" + "C" * 25)
        self.assertEqual(len(options), 1)
        self.assertEqual(Chem.AddHs(Chem.MolFromSmiles(options[0]["productSmiles"])).GetNumAtoms(), 80)
        _, options, result = self.options("C=" + "C" * 26)
        self.assertEqual(options, [])
        self.assertIn("exceed 80 explicit atoms", " ".join(result["unsupportedReasons"]))

    def test_no_cid_formula_or_preset_lookup_decides_eligibility(self):
        a = {"smiles": "C=CCCCO", "name": "Misleading benzene name", "formula": "C6H6", "cid": 241}
        r = next(x for x in service.match_reactions(a, "hydrogen", METAL)["reactions"] if x["mechanism"] == "Hydrogenation")
        self.assertEqual(r["productSmiles"], canonical("CCCCCO"))
        self.check_option(a, r, "CCCCCO")
        b = {"smiles": "[H][H]", "name": "Entered H2"}
        with patch.dict(service.REACTIONS, {}, clear=True):
            self.assertTrue(any(r["mechanism"] == "Hydrogenation" for r in service.match_reactions(a, b, METAL)["reactions"]))

    def test_reverse_order_and_source_map_numbers_keep_exact_correspondence(self):
        a = {"smiles": "[CH2:42]=[CH:3][CH2:25][CH2:11][CH2:7][OH:88]", "name": "Entered mapped alcohol"}
        forward = next(r for r in service.match_reactions(a, "hydrogen", METAL)["reactions"] if r["mechanism"] == "Hydrogenation")
        reverse = next(r for r in service.match_reactions("hydrogen", a, METAL)["reactions"] if r["mechanism"] == "Hydrogenation")
        self.assertEqual(forward["productSmiles"], reverse["productSmiles"])
        d, result = self.check_option(a, forward, "CCCCCO")
        reverse_d = service.reaction_diagram(reverse["id"], "hydrogen", a, METAL)
        self.assertEqual(d["svg"], reverse_d["svg"])
        self.assertEqual({r["formula"]: r["inputSlot"] for r in reverse["stoichiometry"]["reactants"]}, {"H2": 0, "C5H10O": 1})
        item, _ = _species("source", a, 1)
        provenance = {atom.GetIntProp("sourceAtomMap") for atom in item["mol"].GetAtoms() if atom.HasProp("sourceAtomMap")}
        self.assertEqual(provenance, {42, 3, 25, 11, 7, 88})
        self.assertEqual(len(result["product"]["atomLinks"]), len({v["mapId"] for v in result["product"]["atomLinks"]}))

    def test_missing_catalyst_is_not_reported_as_aligned_or_certain(self):
        _, options, _ = self.options("C=CCCCO", conditions={"catalyst": "none"})
        self.assertTrue(options)
        self.assertNotEqual(options[0]["assessment"]["state"], "aligned")
        self.assertIn("not a guarantee", options[0]["conditions"])
        self.assertTrue(any("No rates" in s for s in options[0]["information"]["limitations"]))

    def test_other_pathways_do_not_automatically_adopt_the_policy(self):
        for reagent, mechanism in [("bromine", "Bromination"), ("water", "Hydration"), ("hydrogen-chloride", "Hydrohalogenation")]:
            for substrate in ("C=CCCCO", "C=CC[C@H](C)CC"):
                result = service.match_reactions({"smiles": substrate}, reagent)
                options = [r for r in result["reactions"] if r["mechanism"] == mechanism]
                if mechanism == "Hydration" and substrate == "C=CC[C@H](C)CC":
                    # Phase 3A separately validates hydration; it does not
                    # inherit hydrogenation's oxygen/condition policy.
                    self.assertEqual(len(options), 1)
                    self.assertEqual(options[0]["compatibility"]["policy"], "acid-catalyzed alkene hydration")
                    self.assertFalse(options[0]["assessment"]["canRun"])
                elif mechanism == "Hydrohalogenation" and substrate == "C=CC[C@H](C)CC":
                    # Phase 3B independently validates HX, without adopting
                    # hydrogenation's or hydration's oxygen spectator scope.
                    self.assertEqual(len(options), 1)
                    self.assertEqual(options[0]["productSmiles"], canonical("CC(Cl)C[C@H](C)CC"))
                    self.assertEqual(options[0]["compatibility"]["policy"], "ionic HCl alkene addition")
                elif mechanism == "Bromination" and substrate == "C=CC[C@H](C)CC":
                    self.assertEqual(len(options), 2)
                    self.assertTrue(all(o["compatibility"]["policy"] == "selected-site Br2 addition" for o in options))
                    self.assertTrue(all(not o["assessment"]["canRun"] for o in options))
                else:
                    self.assertFalse(options)
        # The Phase 1 ester consumers retain their own bounded policy.
        for substrate in ("O=C1OCCC1", "CC(=O)Oc1ccccc1"):
            for reagent, mechanism in [("water", "Ester hydrolysis"), ("hydroxide", "Ester saponification")]:
                result = service.match_reactions({"smiles": substrate}, reagent, {"solvent": "aqueous-protic", "catalyst": "acid" if reagent == "water" else "none"})
                r = next(r for r in result["reactions"] if r["mechanism"] == mechanism)
                self.assertTrue(r["stoichiometry"]["balanced"])
                self.assertNotIn("compatibility", r)

    def valid_edit(self, substrate="C=CC[C@H](C)CCO"):
        a, n = _species("a", {"name": "Mapped substrate", "smiles": substrate}, 1)
        b, _ = _species("b", {"name": "H2", "smiles": "[H][H]"}, n)
        site = graph.find_alkenes(a["mol"])[0]
        before = _combine([a, b])
        after = _combine([{"mol": m} for m in engine.transform("Hydrogenation", [a, b], site)])
        return a, b, site, before, after, rule.edit_contract(a["mol"], b["mol"], site)

    def test_contract_independently_preserves_every_unaffected_bond(self):
        a, b, site, before, after, edits = self.valid_edit()
        initial, final = bond_states(before), bond_states(after)
        changed = {pair for pair in initial.keys() | final.keys() if initial.get(pair) != final.get(pair)}
        declared = {tuple(sorted(e["atomMaps"])) for e in edits}
        self.assertEqual(changed, declared)
        oxygen = next(atom for atom in a["mol"].GetAtoms() if atom.GetAtomicNum() == 8)
        for bond in oxygen.GetBonds():
            pair = tuple(sorted((bond.GetBeginAtom().GetAtomMapNum(), bond.GetEndAtom().GetAtomMapNum())))
            self.assertNotIn(pair, changed)
            self.assertEqual(initial[pair], final[pair])
        rule.validate(before, after, a["mol"], b["mol"], site)

    def test_contract_rejects_unselected_bond_atom_charge_map_and_missing_edits(self):
        _, _, _, before, after, edits = self.valid_edit()
        for mutation in ("bond", "element", "charge", "map"):
            altered = Chem.Mol(after)
            if mutation == "bond":
                declared = {tuple(sorted(e["atomMaps"])) for e in edits}
                bond = next(b for b in altered.GetBonds() if b.GetBeginAtom().GetAtomicNum() == b.GetEndAtom().GetAtomicNum() == 6
                            and tuple(sorted((b.GetBeginAtom().GetAtomMapNum(), b.GetEndAtom().GetAtomMapNum()))) not in declared)
                bond.SetBondType(Chem.BondType.DOUBLE)
            elif mutation == "element": altered.GetAtomWithIdx(0).SetAtomicNum(7)
            elif mutation == "charge": altered.GetAtomWithIdx(0).SetFormalCharge(1)
            else: altered.GetAtomWithIdx(0).SetAtomMapNum(0)
            with self.subTest(mutation=mutation), self.assertRaises(ValueError):
                compatibility.validate_edit_contract(before, altered, edits)
        for contract in (edits[:-1], edits + [edits[0]], [{**edits[0], "before": 1.0}, *edits[1:]]):
            with self.assertRaises(ValueError): compatibility.validate_edit_contract(before, after, contract)
        with self.assertRaises(ValueError):
            compatibility.validate_edit_contract(before, after, edits, consumed_double_bonds=[edits[1]["atomMaps"]])
        with self.assertRaises(ValueError):
            compatibility.validate_edit_contract(before, after, edits, expected_fragments=2)

    def test_contract_rejects_inverted_erased_and_invented_stereochemistry(self):
        _, _, _, before, after, edits = self.valid_edit()
        center = next(a.GetIdx() for a in after.GetAtoms() if a.GetChiralTag() != Chem.ChiralType.CHI_UNSPECIFIED)
        for mutation in ("invert", "erase"):
            altered = Chem.Mol(after)
            if mutation == "invert": altered.GetAtomWithIdx(center).InvertChirality()
            else: altered.GetAtomWithIdx(center).SetChiralTag(Chem.ChiralType.CHI_UNSPECIFIED)
            with self.assertRaises(ValueError): compatibility.validate_edit_contract(before, altered, edits, consumed_double_bonds=[edits[0]["atomMaps"]])
        unassigned = Chem.Mol(before)
        unassigned.GetAtomWithIdx(center).SetChiralTag(Chem.ChiralType.CHI_UNSPECIFIED)
        with self.assertRaises(ValueError): compatibility.validate_edit_contract(unassigned, after, edits, consumed_double_bonds=[edits[0]["atomMaps"]])
        renumbered = Chem.RenumberAtoms(after, list(reversed(range(after.GetNumAtoms()))))
        compatibility.validate_edit_contract(before, renumbered, edits, consumed_double_bonds=[edits[0]["atomMaps"]])

    def test_contract_rejects_inversion_or_loss_of_unselected_alkene_geometry(self):
        _, _, _, before, after, edits = self.valid_edit("C/C=C/CC/C=C\\C")
        selected = frozenset(edits[0]["atomMaps"])
        bond = next(b for b in after.GetBonds() if b.GetBondType() == Chem.BondType.DOUBLE)
        for mutation in ("invert", "erase"):
            altered = Chem.Mol(after)
            changed = altered.GetBondWithIdx(bond.GetIdx())
            changed.SetStereo(Chem.BondStereo.STEREOE if mutation == "invert" else Chem.BondStereo.STEREONONE)
            if mutation == "erase":
                for b in altered.GetBonds(): b.SetBondDir(Chem.BondDir.NONE)
            with self.assertRaises(ValueError):
                compatibility.validate_edit_contract(before, altered, edits, consumed_double_bonds=[selected])

    def test_reusable_policy_invalid_sites_unknown_groups_and_bad_reagent_fail_closed(self):
        mol = Chem.MolFromSmiles("C=CCCCO")
        for site in ((), (0, 0), (0, 999), (True, 1)):
            r = rule.assess(mol, site)
            self.assertFalse(r["eligible"])
            self.assertEqual(r["rejections"][0]["code"], "invalid-site")
        self.assertFalse(rule.assess(mol, (2, 3))["eligible"])
        self.assertFalse(rule.assess(Chem.MolFromSmiles("C=C.O"), (0, 1))["eligible"])
        disposition, category, explanation = rule.group_check(mol, (0, 1), {"type": "unknown group", "atomIndices": [5]})
        self.assertEqual((disposition, category), ("rejected", "unvalidated"))
        self.assertIn("no validated spectator policy", explanation)
        a, b, site, _, _, _ = self.valid_edit()
        water, _ = _species("wrong", {"name": "Not H2", "smiles": "O"}, 100)
        with self.assertRaises(ValueError): rule.edit_contract(a["mol"], water["mol"], site)

    def test_public_options_fail_closed_if_retention_or_contract_validation_fails(self):
        for target in ("server.reaction_compatibility.validate_edit_contract", "server.stereochemistry.validate_retained_stereo"):
            with patch(target, side_effect=ValueError("Independent validation failure")):
                _, options, result = self.options("C=CCCCO")
                self.assertEqual(options, [])
                self.assertIn("Independent validation failure", " ".join(result["unsupportedReasons"]))

    def test_public_authenticated_http_match_diagram_run_and_rejection(self):
        from server.production_app import create_app
        origin = "https://hydrogenation-phase2.example.test"
        password = "Phase2-synthetic-password"
        app = create_app({"TRIAL_PASSWORD": password,
                          "SESSION_SECRET": "5a793bc832adc647a5f382190dead01d19f58f6fa0c9246eb8b2b31f0f419b60",
                          "PUBLIC_ORIGIN": origin, "FRAME_ANCESTORS": "https://site.example.test",
                          "DIST_DIR": "/private/tmp/hydrogenation-phase2-no-static-needed", "TESTING": True}, chemistry_backend=service)
        client = app.test_client()
        self.assertEqual(client.post("/login", base_url=origin, headers={"Origin": origin}, data={"password": password}).status_code, 303)
        for substrate, expected in [("C=CCCCO", "CCCCCO"), ("C=CC[C@H](C)CC", "CCC[C@H](C)CC")]:
            body = {"reactantA": {"smiles": substrate}, "reactantB": "hydrogen", "conditions": METAL}
            response = client.post("/api/reactions/match", base_url=origin, headers={"Origin": origin}, json=body)
            self.assertEqual(response.status_code, 200)
            option = next(r for r in response.get_json()["reactions"] if r["mechanism"] == "Hydrogenation")
            self.assertTrue(option["compatibility"]["eligible"])
            self.assertEqual(option["productSmiles"], canonical(expected))
            body["reactionId"] = option["id"]
            d = client.post("/api/reactions/diagram", base_url=origin, headers={"Origin": origin}, json=body)
            p = client.post("/api/reactions/run", base_url=origin, headers={"Origin": origin}, json=body)
            self.assertEqual((d.status_code, p.status_code), (200, 200))
            self.assertEqual(d.get_json()["products"][0]["smiles"], p.get_json()["product"]["smiles"])
        response = client.post("/api/reactions/match", base_url=origin, headers={"Origin": origin},
                               json={"reactantA": {"smiles": "C=CCO"}, "reactantB": "hydrogen", "conditions": METAL})
        self.assertEqual(response.status_code, 200)
        self.assertFalse(any(r["mechanism"] == "Hydrogenation" for r in response.get_json()["reactions"]))
        self.assertIn("allylic/benzylic", " ".join(response.get_json()["unsupportedReasons"]))


if __name__ == "__main__":
    unittest.main()

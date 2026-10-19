"""Independent E2 net products, exact proton maps and bounded anti stereochemistry."""
import math
import unittest
from unittest.mock import patch
from rdkit import Chem
from rdkit.Chem import Descriptors, rdMolDescriptors, rdCIPLabeler
from rdkit.Geometry import Point3D
from server import chemistry_server as service, e2_rule as rule, stereochemistry as stereo
from server import reaction_engine as engine, reaction_compatibility as compatibility
from server.reaction_diagrams import _species, _combine, _identity

CONDITIONS = {"solvent": "ethanolic-protic", "temperature": "heated"}


def canonical(smiles):
    return Chem.MolToSmiles(Chem.MolFromSmiles(smiles))


def mapped(smiles):
    a, n = _species("substrate", {"name": "Independent E2 structure", "smiles": smiles}, 1)
    b, _ = _species("base", {"name": "Hydroxide", "smiles": "[OH-]"}, n)
    return a, b


class E2CompatibilityTests(unittest.TestCase):
    def options(self, smiles, reagent="hydroxide", conditions=CONDITIONS):
        ref = {"name": "Independent E2 test input", "smiles": smiles}
        result = service.match_reactions(ref, reagent, conditions)
        return ref, [r for r in result["reactions"] if r["mechanism"] == "E2"], result

    def check_option(self, ref, option, expected, reagent="hydroxide"):
        expected = canonical(expected)
        self.assertEqual(option["productSmiles"], expected)
        self.assertEqual(option["productFormula"], rdMolDescriptors.CalcMolFormula(Chem.MolFromSmiles(expected)))
        data = option["stoichiometry"]
        self.assertTrue(data["balanced"])
        self.assertEqual([x["coefficient"] for x in data["reactants"]], [1, 1])
        self.assertEqual(data["product"]["coefficient"], 1)
        self.assertAlmostEqual(data["product"]["molarMass"], Descriptors.MolWt(Chem.MolFromSmiles(expected)), places=6)
        d = service.reaction_diagram(option["id"], ref, reagent, CONDITIONS)
        self.assertTrue(d["highlightsAvailable"])
        self.assertEqual(d["products"][0]["smiles"], expected)
        self.assertEqual(d["products"][1]["smiles"], "O")
        source = {a["mapId"]: (a["element"], a["formalCharge"]) for a in d["atoms"] if a["side"] == "reactants"}
        product = {a["mapId"]: (a["element"], a["formalCharge"]) for a in d["atoms"] if a["side"] == "products"}
        self.assertEqual({m: x[0] for m, x in source.items()}, {m: x[0] for m, x in product.items()})
        self.assertEqual(sum(x[1] for x in source.values()), -1)
        self.assertEqual(sum(x[1] for x in product.values()), -1)
        report = option["compatibility"]
        self.assertEqual(report["policy"], "hydroxide E2 elimination")
        self.assertTrue(report["eligible"])
        self.assertEqual(set(report["validation"].values()), {"verified"})
        self.assertEqual(report["substrateSiteMaps"], option["site"]["atomMaps"])
        s = report["eliminations"][0]
        alpha, beta, hydrogen, leaving, base = (s[k] for k in ("alpha", "beta", "hydrogen", "leaving", "base"))
        self.assertEqual((source[hydrogen][0], source[base]), ("H", ("O", -1)))
        self.assertEqual(option["site"]["parameters"]["betaHydrogenMap"], hydrogen)
        self.assertIn(hydrogen, option["site"]["parameters"]["betaHydrogenMaps"])
        self.assertEqual((product[base][1], product[leaving][1]), (0, -1))
        self.assertEqual(d["products"][2]["smiles"], f"[{source[leaving][0]}-]")
        self.assertEqual({frozenset(c["atomMaps"]) for c in d["bondsBroken"]}, {frozenset((alpha, leaving)), frozenset((beta, hydrogen))})
        self.assertEqual({frozenset(c["atomMaps"]) for c in d["bondsFormed"]}, {frozenset((base, hydrogen))})
        self.assertEqual(len(d["bondOrderChanges"]), 1)
        self.assertEqual(set(d["bondOrderChanges"][0]["atomMaps"]), {alpha, beta})
        self.assertEqual({(frozenset(e["atomMaps"]), e["before"], e["after"]) for e in report["editContract"]},
                         {(frozenset(e["atomMaps"]), e["before"], e["after"]) for e in d["changes"]})
        self.assertEqual(set(report["reactiveAtomMaps"]), set(s.values()))
        mechanism = d["mechanism"]
        self.assertEqual(mechanism["roles"], {"alpha-carbon": alpha, "leaving-group": leaving, "base": base, "beta-carbon": beta, "beta-hydrogen": hydrogen})
        self.assertEqual(len(mechanism["steps"]), 1)
        step = mechanism["steps"][0]
        self.assertTrue(step["concerted"])
        self.assertIsNone(step["intermediate"])
        self.assertEqual([(x["source"], x["destination"]) for x in step["electronMoves"]], [
            ({"type": "lone-pair", "atomMaps": [base]}, {"type": "atom", "atomMaps": [hydrogen]}),
            ({"type": "bond", "atomMaps": [beta, hydrogen]}, {"type": "bond", "atomMaps": [beta, alpha]}),
            ({"type": "bond", "atomMaps": [alpha, leaving]}, {"type": "atom", "atomMaps": [leaving]})])
        self.assertEqual({frozenset(c["atomMaps"]) for c in step["protonTransfers"]}, {frozenset((beta, hydrogen)), frozenset((base, hydrogen))})
        params = Chem.SmilesParserParams(); params.removeHs = False
        state = Chem.MolFromSmiles(step["state"]["mappedSmiles"], params)
        main = next(m for m in Chem.GetMolFrags(state, asMols=True) if any(a.GetAtomMapNum() == alpha for a in m.GetAtoms()))
        self.assertEqual(_identity(main), expected)
        self.assertEqual(mechanism["energyProfile"]["intermediates"], 0)
        self.assertIsNone(mechanism["energyProfile"]["activationEnergies"])
        product3d = service.run_curated_reaction(option["id"], ref, reagent, CONDITIONS)["product"]
        self.assertEqual(product3d["smiles"], expected)
        self.assertEqual(product3d["representation"], "3d")
        main_rows = [a for a in d["atoms"] if a["side"] == "products" and a["speciesIndex"] == 0]
        self.assertEqual([(a["atomIndex"], a["mapId"], a["element"]) for a in main_rows],
                         [(a["index"], a["mapId"], a["element"]) for a in product3d["atomLinks"]])
        self.assertNotIn(hydrogen, {a["mapId"] for a in product3d["atomLinks"]})
        self.assertNotIn(leaving, {a["mapId"] for a in product3d["atomLinks"]})
        self.assertTrue({alpha, beta} <= {a["mapId"] for a in product3d["atomLinks"]})
        shape = Chem.MolFromMolBlock(product3d["molfile"], removeHs=False)
        for atom in shape.GetAtoms(): atom.SetAtomMapNum(0)
        Chem.AssignStereochemistryFrom3D(shape, replaceExistingTags=True)
        rdCIPLabeler.AssignCIPLabels(shape)
        links = {a["mapId"]: a["index"] for a in product3d["atomLinks"]}
        for c in option["information"]["stereochemistry"]["product"]["chiralCenters"]:
            if c["specified"]:
                self.assertEqual(shape.GetAtomWithIdx(links[c["atomMap"]]).GetProp("_CIPCode"), c["assignment"])
        for alkene in option["information"]["stereochemistry"]["product"]["alkenes"]:
            if alkene["specified"]:
                self.assertEqual(shape.GetBondBetweenAtoms(*(links[m] for m in alkene["atomMaps"])).GetProp("_CIPCode"), alkene["assignment"])
        self.assertEqual(option["reasoning"]["label"], "Possible")
        return option

    def check(self, substrate, products, count=None):
        ref, options, result = self.options(substrate)
        self.assertTrue(options, result["unsupportedReasons"])
        self.assertEqual({r["productSmiles"] for r in options}, {canonical(p) for p in products})
        if count is not None:
            self.assertEqual(len(options), count)
        for r in options:
            self.check_option(ref, r, r["productSmiles"])
        return options

    def test_primary_long_and_all_existing_leaving_groups(self):
        for x in ("Cl", "Br", "I"):
            with self.subTest(leaving=x): self.check("CCCCCCC" + x, ["C=CCCCCC"], 1)

    def test_branched_primary_secondary_and_tertiary_constitutional_products(self):
        for a, products, count in [("BrCC(C)C", ["C=C(C)C"], 1), ("CCC(Br)CC", ["CC=CCC"], 1),
                                   ("CCCC(Br)CC", ["CCC=CCC", "CC=CCCC"], 2),
                                   ("CCCC(Br)(C)C", ["C=C(C)CCC", "CCC=C(C)C"], 2),
                                   ("CC(C)CC(Br)(C)C", ["C=C(C)CC(C)C", "CC(C)C=C(C)C"], 2)]:
            with self.subTest(substrate=a): self.check(a, products, count)

    def test_benzylic_and_remote_aromatic_skeletons(self):
        self.check("CCC(Br)c1ccccc1", ["CC=Cc1ccccc1"], 1)
        self.check("BrCCc1ccccc1", ["C=Cc1ccccc1"], 1)

    def test_remote_ethers_and_remote_oh_with_bounded_competition(self):
        for a, products in [("COCCC(Br)(C)C", ["COCC=C(C)C", "C=C(C)CCOC"]),
                             ("COCCCBr", ["COCC=C"]), ("OCCCCCCCBr", ["C=CCCCCCO"]),
                             ("BrCCCCOC1CCCC1", ["C=CCCOC1CCCC1"])]:
            with self.subTest(substrate=a): self.check(a, products)

    def test_distant_centers_physically_retained_and_cip_recomputed(self):
        self.check("CC[C@H](C)CCC(Br)(C)C", ["CC[C@H](C)CC=C(C)C", "CC[C@H](C)CCC(C)=C"], 2)
        self.check("CC[C@H](C)COCCCBr", ["CC[C@H](C)COCC=C"], 1)

    def test_reacting_specified_center_becomes_planar_without_invented_ez(self):
        for a in ("CC[C@H](Br)CCC", "CC[C@@H](Br)CCC", "Br[C@H](CC)CCC"):
            for r in self.check(a, ["CCC=CCC", "CC=CCCC"], 2):
                self.assertFalse(any(x["specified"] for x in r["information"]["stereochemistry"]["product"]["alkenes"]))
                self.assertFalse(r["information"]["stereochemistry"]["product"]["chiralCenters"])

    def test_two_specified_local_centers_give_bounded_anti_relationship(self):
        for a, expected in [("C[C@H](Br)[C@H](C)CC", "C/C=C(/C)CC"),
                             ("C[C@H](Br)[C@@H](C)CC", "C/C=C(\\C)CC"),
                             ("C[C@@H](Br)[C@@H](C)CC", "C/C=C(/C)CC"),
                             ("C[C@@H](Br)[C@H](C)CC", "C/C=C(\\C)CC")]:
            ref, options, result = self.options(a)
            selected = next((r for r in options if r["productSmiles"] == canonical(expected)), None)
            self.assertIsNotNone(selected, result)
            self.check_option(ref, selected, expected)
            self.assertEqual(len(selected["information"]["stereochemistry"]["product"]["alkenes"]), 1)
            self.assertTrue(selected["information"]["stereochemistry"]["product"]["alkenes"][0]["specified"])

    def test_unspecified_local_centers_never_receive_ez_or_rs(self):
        for a in ("CC(Br)C(C)CC", "C[C@H](Br)C(C)CC", "CC(Br)[C@H](C)CC"):
            _, opts, _ = self.options(a)
            for r in opts:
                self.assertFalse(any(x["specified"] for x in r["information"]["stereochemistry"]["product"]["alkenes"]))

    def test_multiple_halides_have_separate_exact_site_options(self):
        self.check("CC(Br)(C)CCC(Br)(C)C", ["C=C(C)CCC(Br)(C)C", "CC(C)=CCC(Br)(C)C"], 4)
        self.check("BrCCCCCBr", ["C=CCCCBr"], 2)

    def test_source_map_numbers_and_atom_order_cannot_split_equivalent_beta_sites(self):
        for substrate in ("CCC(Br)(C)C", "[CH3:77][CH2:2][C:9]([Br:33])([CH3:16])[CH3:3]"):
            self.check(substrate, ["CC=C(C)C", "C=C(C)CC"], 2)
            a, _ = mapped(substrate)
            self.assertEqual(len(rule.sites(a["mol"])), 2)
            self.assertEqual(len(rule.sites(Chem.RenumberAtoms(a["mol"], list(reversed(range(a["mol"].GetNumAtoms())))))), 2)

    def test_remote_chirality_is_preserved_while_local_two_center_stereo_is_used(self):
        a = "CC[C@H](C)COCCC[C@H](Br)[C@H](C)CC"
        ref, opts, _ = self.options(a)
        self.assertEqual(len(opts), 2)
        for r in opts:
            self.check_option(ref, r, r["productSmiles"])
            source = r["information"]["stereochemistry"]["reactant"]["chiralCenters"]
            target = r["information"]["stereochemistry"]["product"]["chiralCenters"]
            local = set(r["site"]["atomMaps"][::2])
            remote = [x for x in source if x["atomMap"] not in local]
            for center in remote:
                self.assertIn(center["atomMap"], [x["atomMap"] for x in target])

    def test_methyl_neopentyl_and_no_beta_h_controls(self):
        for a in ("CBr", "CC(C)(C)CBr", "CC(C)(C)C(Br)C(C)(C)C"):
            _, opts, result = self.options(a)
            self.assertFalse(opts)
            self.assertIn("beta", " ".join(result["unsupportedReasons"]).lower())

    def test_cyclic_and_allylic_cases_not_automatically_enabled(self):
        for a in ("BrC1CCCCC1", "CC1(Br)CCCCC1", "BrCC1CCCCC1", "C=CCBr", "C=CC(Br)C", "C#CCCBr"):
            _, opts, result = self.options(a)
            self.assertFalse(opts)
            self.assertTrue(result["unsupportedReasons"])

    def test_competing_oh_small_closure_and_near_ether_are_rejected(self):
        for a in ("OCCBr", "OCCCBr", "OCCCCBr", "OCCCCCBr", "COCCBr", "COC(Br)CC", "BrCC(O)C"):
            _, opts, result = self.options(a)
            self.assertFalse(opts)
            self.assertRegex(" ".join(result["unsupportedReasons"]), "intramolecular|ether|beta|Geminal")

    def test_unvalidated_elements_and_groups_are_not_spectators(self):
        for a in ("FCCC(Br)(C)C", "BrCCCCN", "BrCCCCS", "BrCCCC=O", "BrCCCC(=O)O", "BrCCCC(=O)OC", "BrCCCCOO", "BrCCCc1ccncc1", "BrCCCCc1ccc(Cl)cc1", "BrCCBr", "CC(Br)(Cl)CC"):
            _, opts, result = self.options(a)
            self.assertFalse(opts)
            self.assertTrue(result["unsupportedReasons"])

    def test_reagents_are_actual_hydroxide_not_names_and_no_new_base_family(self):
        for reagent in ("water", {"name": "Hydroxide", "smiles": "O"}):
            self.assertFalse(self.options("CCC(Br)C", reagent)[1])
        for reagent in ({"smiles": "[K+].[O-]C(C)(C)C"}, {"smiles": "[Na+].[O-]C"}, {"smiles": "[O-]C"}, {"smiles": "[NH2-]"}):
            with self.assertRaises(service.ChemistryError): self.options("CCC(Br)C", reagent)

    def test_actual_salts_reverse_inputs_and_source_maps(self):
        a = {"name": "Independent maps", "smiles": "[CH3:77][CH2:5][CH2:8][Br:19]"}
        for reagent, mass in (("hydroxide", 17.007), ("sodium-hydroxide", 39.997), ({"smiles": "[K+].[OH-]"}, 56.105)):
            forward = next(r for r in service.match_reactions(a, reagent, CONDITIONS)["reactions"] if r["mechanism"] == "E2")
            reverse = next(r for r in service.match_reactions(reagent, a, CONDITIONS)["reactions"] if r["mechanism"] == "E2")
            self.assertEqual(reverse["productSmiles"], canonical("C=CC"))
            self.assertEqual(service.reaction_diagram(forward["id"], a, reagent, CONDITIONS)["svg"], service.reaction_diagram(reverse["id"], reagent, a, CONDITIONS)["svg"])
            self.assertAlmostEqual(next(x["molarMass"] for x in reverse["stoichiometry"]["reactants"] if x["inputSlot"] == 0), mass)
            self.check_option(a, forward, "C=CC", reagent)
        item, _ = _species("source", a, 1)
        self.assertEqual({atom.GetIntProp("sourceAtomMap") for atom in item["mol"].GetAtoms() if atom.HasProp("sourceAtomMap")}, {77, 5, 8, 19})

    def test_condition_assessments_remain_qualitative(self):
        for conditions, state in [({}, "incomplete"), ({"solvent": "polar-aprotic", "temperature": "ambient"}, "alternative"), (CONDITIONS, "aligned")]:
            _, opts, _ = self.options("CCC(Br)C", conditions=conditions)
            self.assertTrue(opts)
            self.assertEqual(opts[0]["assessment"]["state"], state)
            self.assertEqual(opts[0]["reasoning"]["label"], {"alternative": "Reference differs", "incomplete": "Conditions incomplete", "aligned": "Possible"}[state])
            self.assertIn("not a", opts[0]["reasoning"]["note"])

    def test_enhanced_invalid_electronic_and_size_limits_fail_closed(self):
        for a in ("not-smiles", "CC(Br)(C)(C)C", "BrCCC[O-]", "BrCC[CH2]", "BrCC[13CH2]C", "CCBr.O", "CC[C@H](Br)CCC |&1:2|"):
            with self.assertRaises(service.ChemistryError): self.options(a)
        for a in ("BrCCCC1CC1", "C" * 27 + "Br"):
            self.assertFalse(self.options(a)[1])
        _, opts, _ = self.options("C" * 26 + "Br")
        self.assertEqual(len(opts), 1)
        self.assertEqual(Chem.AddHs(Chem.MolFromSmiles(opts[0]["productSmiles"])).GetNumAtoms(), 78)

    def valid_edit(self, a="CC[C@H](C)COCCCBr", selected=0):
        substrate, base = mapped(a)
        site = rule.sites(substrate["mol"])[selected]
        before = _combine([substrate, base])
        after = _combine([{"mol": m} for m in engine.transform("E2", [substrate, base], site)])
        return substrate, base, site, before, after

    def test_exact_contract_atom_renumbering_and_serialization(self):
        for a in ("CC[C@H](C)COCCCBr", "C[C@H](Br)[C@H](C)CC"):
            for index in range(len(rule.sites(Chem.MolFromSmiles(a)))):
                substrate, base, site, before, after = self.valid_edit(a, index)
                rule.validate(before, after, substrate["mol"], base["mol"], site)
                rule.validate(before, Chem.RenumberAtoms(after, list(reversed(range(after.GetNumAtoms())))), substrate["mol"], base["mol"], site)
                if any(substrate["mol"].GetAtomWithIdx(i).GetChiralTag() in stereo.TETRAHEDRAL for i in (site[0], site[2])):
                    with self.assertRaises(ValueError): compatibility.validate_edit_contract(before, after, rule.edit_contract(substrate["mol"], base["mol"], site), charge_changes=rule.charge_contract(substrate["mol"], base["mol"], site))
                else:
                    compatibility.validate_edit_contract(before, after, rule.edit_contract(substrate["mol"], base["mol"], site), charge_changes=rule.charge_contract(substrate["mol"], base["mol"], site))

    def test_changed_distant_configuration_or_charge_and_bond_are_rejected(self):
        a, b, site, before, after = self.valid_edit()
        edits = []
        inverted = Chem.Mol(after); next(x for x in inverted.GetAtoms() if x.GetChiralTag() in stereo.TETRAHEDRAL).InvertChirality(); edits.append(inverted)
        lost = Chem.Mol(after); next(x for x in lost.GetAtoms() if x.GetChiralTag() in stereo.TETRAHEDRAL).SetChiralTag(Chem.ChiralType.CHI_UNSPECIFIED); edits.append(lost)
        wrong_charge = Chem.Mol(after); next(x for x in wrong_charge.GetAtoms() if x.GetAtomicNum() == 35).SetFormalCharge(0); edits.append(wrong_charge)
        wrong_map = Chem.Mol(after); wrong_map.GetAtomWithIdx(0).SetAtomMapNum(999); edits.append(wrong_map)
        wrong_bond = Chem.Mol(after); wrong_bond.GetBondWithIdx(0).SetBondType(Chem.BondType.DOUBLE); edits.append(wrong_bond)
        for altered in edits:
            with self.assertRaises(ValueError): rule.validate(before, altered, a["mol"], b["mol"], site)

    def test_invalid_elimination_permissions_cannot_consume_distant_stereo(self):
        a, b, site, before, after = self.valid_edit()
        spec = rule.participants(a["mol"], b["mol"], site)
        for change in ({"alpha": 3}, {"beta": 3}, {"hydrogen": spec["alpha"]}, {"base": spec["leaving"]}):
            with self.assertRaises(ValueError): compatibility.validate_edit_contract(before, after, rule.edit_contract(a["mol"], b["mol"], site), charge_changes=rule.charge_contract(a["mol"], b["mol"], site), eliminations=[{**spec, **change}])
        with self.assertRaises(ValueError): compatibility.validate_edit_contract(before, after, rule.edit_contract(a["mol"], b["mol"], site), charge_changes=rule.charge_contract(a["mol"], b["mol"], site), eliminations=[spec, spec])

    def test_incorrect_or_lost_local_ez_and_invented_unsigned_geometry_fail(self):
        a, b, site, before, after = self.valid_edit("C[C@H](Br)[C@H](C)CC", 1)
        spec = rule.participants(a["mol"], b["mol"], site)
        atoms = {x.GetAtomMapNum(): x for x in after.GetAtoms()}
        bond_index = after.GetBondBetweenAtoms(atoms[spec["alpha"]].GetIdx(), atoms[spec["beta"]].GetIdx()).GetIdx()
        for tag in (Chem.BondStereo.STEREONONE, Chem.BondStereo.STEREOCIS if after.GetBondWithIdx(bond_index).GetStereo() == Chem.BondStereo.STEREOTRANS else Chem.BondStereo.STEREOTRANS):
            wrong = Chem.Mol(after); wrong.GetBondWithIdx(bond_index).SetStereo(tag)
            with self.assertRaises(ValueError): rule.validate(before, wrong, a["mol"], b["mol"], site)
        a, b, site, before, after = self.valid_edit("CCC(Br)CC")
        wrong = Chem.Mol(after); double = next(x for x in wrong.GetBonds() if x.GetBondType() == Chem.BondType.DOUBLE)
        refs = [next(x.GetIdx() for x in carbon.GetNeighbors() if x.GetIdx() != other.GetIdx()) for carbon, other in ((double.GetBeginAtom(), double.GetEndAtom()), (double.GetEndAtom(), double.GetBeginAtom()))]
        double.SetStereoAtoms(*refs); double.SetStereo(Chem.BondStereo.STEREOTRANS)
        with self.assertRaises(ValueError): rule.validate(before, wrong, a["mol"], b["mol"], site)

    def test_injected_validation_failure_cannot_publish_candidate(self):
        with patch.object(rule, "validate", side_effect=ValueError("Independent E2 validation blocked")):
            _, opts, result = self.options("CCBr")
        self.assertFalse(opts)
        self.assertIn("Independent E2 validation blocked", " ".join(result["unsupportedReasons"]))

    def test_wrong_proton_destination_and_wrong_beta_bond_fail(self):
        a, b, site, before, after = self.valid_edit()
        spec = rule.participants(a["mol"], b["mol"], site)
        from server.reaction_diagrams import _remove, _add, _order
        wrong_proton = Chem.RWMol(after)
        _remove(wrong_proton, spec["base"], spec["hydrogen"])
        _add(wrong_proton, spec["leaving"], spec["hydrogen"])
        with self.assertRaises(ValueError): rule.validate(before, wrong_proton.GetMol(), a["mol"], b["mol"], site)
        wrong_pi = Chem.RWMol(after); _order(wrong_pi, spec["alpha"], spec["beta"], 1)
        with self.assertRaises(ValueError): rule.validate(before, wrong_pi.GetMol(), a["mol"], b["mol"], site)

    def test_invalid_actual_hydroxide_electronic_graphs_fail(self):
        a, b = mapped("CCCBr"); site = rule.sites(a["mol"])[0]
        for mutate in (lambda m: m.GetAtomWithIdx(0).SetFormalCharge(0),
                       lambda m: m.GetAtomWithIdx(1).SetFormalCharge(1),
                       lambda m: m.GetAtomWithIdx(1).SetIsotope(2),
                       lambda m: m.GetAtomWithIdx(0).SetNumRadicalElectrons(1)):
            wrong = Chem.Mol(b["mol"]); mutate(wrong)
            with self.assertRaises(ValueError): rule.participants(a["mol"], wrong, site)

    def test_mechanism_must_pass_same_stereo_contract(self):
        ref, opts, _ = self.options("C[C@H](Br)[C@H](C)CC")
        selected = next(r for r in opts if "/" in r["productSmiles"])
        original = rule.apply_stereo
        def corrupt(before, editor, spec):
            original(before, editor, spec)
            atoms = {x.GetAtomMapNum(): x for x in editor.GetAtoms()}
            editor.GetBondBetweenAtoms(atoms[spec["alpha"]].GetIdx(), atoms[spec["beta"]].GetIdx()).SetStereo(Chem.BondStereo.STEREONONE)
        # Public candidate is regenerated before the mechanism: corrupt only
        # after that exact graph has already been validated by the net engine.
        from server import reaction_mechanisms
        ids, custom, _ = service._resolve_reactants(ref, "hydroxide")
        catalog = {**service.REACTANTS, **custom}
        generated, _ = engine.generate_pair(*ids, catalog, conditions=CONDITIONS)
        with patch.object(rule, "apply_stereo", side_effect=corrupt), self.assertRaises(ValueError):
            reaction_mechanisms.build_mechanism(generated[selected["id"]], catalog)

    def test_unknown_groups_wrong_sites_and_base_graphs_fail_closed(self):
        molecule = Chem.MolFromSmiles("CCCBr")
        for site in ((), (1, 2), (0, 0, 1), (True, 2, 1), (1, 3, 999), (0, 1, 2)):
            self.assertFalse(rule.assess(molecule, site)["eligible"])
        self.assertEqual(rule.group_check(molecule, (2, 3), {"type": "unknown", "atomIndices": [0]})[0], "rejected")
        a, b = mapped("CCCBr")
        wrong, _ = _species("water", {"name": "False base", "smiles": "O"}, 100)
        with self.assertRaises(ValueError): rule.participants(a["mol"], wrong["mol"], rule.sites(a["mol"])[0])

    def test_sn1_sn2_e1_remain_independently_bounded(self):
        for smiles, reagent, expected in [("COCCC(Br)(C)C", "hydroxide", {"E2"}), ("COCCC(Br)(C)C", "water", set()),
                                         ("CC[C@H](Br)CCC", "water", set()), ("OCCCCCCCBr", "hydroxide", {"SN2", "E2"})]:
            result = service.match_reactions({"smiles": smiles}, reagent)
            self.assertEqual({r["mechanism"] for r in result["reactions"]}, expected)
        self.assertTrue(any(x["mechanism"] == "SN1" for x in service.match_reactions({"smiles": "CC(C)(C)Cl"}, "water")["reactions"]))

    def test_authenticated_public_match_diagram_and_run(self):
        from server.production_app import create_app
        origin = "https://e2-increment.example.test"
        app = create_app({"TRIAL_PASSWORD": "E2-synthetic-test-password", "SESSION_SECRET": "5a793bc832adc647a5f382190dead01d19f58f6fa0c9246eb8b2b31f0f419b60", "PUBLIC_ORIGIN": origin,
                          "FRAME_ANCESTORS": "https://site.example.test", "DIST_DIR": "/private/tmp/e2-no-static-needed", "TESTING": True}, chemistry_backend=service)
        client = app.test_client()
        self.assertEqual(client.post("/login", base_url=origin, headers={"Origin": origin}, data={"password": "E2-synthetic-test-password"}).status_code, 303)
        for smiles in ("COCCC(Br)(C)C", "CC[C@H](C)CCC(Br)(C)C", "C[C@H](Br)[C@H](C)CC"):
            body = {"reactantA": {"smiles": smiles}, "reactantB": "hydroxide", "conditions": CONDITIONS}
            response = client.post("/api/reactions/match", base_url=origin, headers={"Origin": origin}, json=body)
            self.assertEqual(response.status_code, 200)
            options = [x for x in response.get_json()["reactions"] if x["mechanism"] == "E2"]
            self.assertEqual(len(options), 2)
            for r in options:
                body["reactionId"] = r["id"]
                diagram = client.post("/api/reactions/diagram", base_url=origin, headers={"Origin": origin}, json=body)
                run = client.post("/api/reactions/run", base_url=origin, headers={"Origin": origin}, json=body)
                self.assertEqual((diagram.status_code, run.status_code), (200, 200))
                self.assertEqual(diagram.get_json()["products"][0]["smiles"], run.get_json()["product"]["smiles"])


class E2GeometryTests(unittest.TestCase):
    def test_reference_meso_and_enantiomeric_anti_outcomes_at_utility_level(self):
        # OpenStax 11.8: meso (R,S) -> E; (R,R)/(S,S) -> Z. This
        # independent local stereo reference does not enable public vicinal
        # dibromide chemistry, whose competing transformations are unvalidated.
        from server.reaction_diagrams import _remove, _order, _add, _charge, _finish
        for source, ez in [("Br[C@H](c1ccccc1)[C@@H](Br)c1ccccc1", "E"),
                           ("Br[C@H](c1ccccc1)[C@H](Br)c1ccccc1", "Z"),
                           ("Br[C@@H](c1ccccc1)[C@@H](Br)c1ccccc1", "Z")]:
            a, b = mapped(source); before = _combine([a, b])
            site = next(x for x in rule.sites(a["mol"]) if a["mol"].GetAtomWithIdx(x[2]).GetDegree() == 4)
            s = rule.participants(a["mol"], b["mol"], site)
            editor = Chem.RWMol(before)
            _remove(editor, s["alpha"], s["leaving"]); _remove(editor, s["beta"], s["hydrogen"])
            _order(editor, s["alpha"], s["beta"], 2); _add(editor, s["base"], s["hydrogen"])
            _charge(editor, s["base"], 0); _charge(editor, s["leaving"], -1)
            rule.apply_stereo(before, editor, s); after = _finish(editor)
            self.assertEqual(stereo.inspect_stereochemistry(after)["alkenes"][0]["assignment"], ez)
            self.assertFalse(any(x["mechanism"] == "E2" for x in service.match_reactions({"smiles": source}, "hydroxide")["reactions"]))

    def test_non_anti_supplied_conformer_rotates_without_becoming_rejection(self):
        from rdkit.Chem import AllChem, rdMolTransforms
        for source in ("CCCBr", "CC[C@H](C)CCCBr", "C[C@H](Br)[C@H](C)CC"):
            a, b = mapped(source); site = rule.sites(a["mol"])[-1]; s = rule.participants(a["mol"], b["mol"], site)
            settings = AllChem.ETKDGv3(); settings.randomSeed = 15
            self.assertEqual(AllChem.EmbedMolecule(a["mol"], settings), 0)
            indices = {x.GetAtomMapNum(): x.GetIdx() for x in a["mol"].GetAtoms()}
            torsion = [indices[s[k]] for k in ("hydrogen", "beta", "alpha", "leaving")]
            rdMolTransforms.SetDihedralDeg(a["mol"].GetConformer(), *torsion, 60.0)
            before_positions = [tuple(a["mol"].GetConformer().GetAtomPosition(i)) for i in range(a["mol"].GetNumAtoms())]
            report = rule.check_conformations(a["mol"], *(s[k] for k in ("hydrogen", "beta", "alpha", "leaving")))
            self.assertFalse(report["sampledConformer"]["antiPeriplanar"])
            self.assertTrue(report["antiCandidate"]["antiPeriplanar"])
            self.assertAlmostEqual(abs(report["antiCandidate"]["dihedralDegrees"]), 180)
            self.assertIn("not an energy", report["note"])
            self.assertEqual(before_positions, [tuple(a["mol"].GetConformer().GetAtomPosition(i)) for i in range(a["mol"].GetNumAtoms())])

    def test_all_actual_beta_hydrogens_can_be_measured_without_predicted_populations(self):
        a, b = mapped("CCCC(Br)CC")
        from rdkit.Chem import AllChem
        settings = AllChem.ETKDGv3(); settings.randomSeed = 4
        self.assertEqual(AllChem.EmbedMolecule(a["mol"], settings), 0)
        values = stereo.e2_geometry_sites(a["mol"])
        self.assertEqual(len(values), 4)  # two beta CH2 groups, two actual H each
        self.assertEqual(len({v["atomMaps"][0] for v in values}), 4)

    def test_geometry_failures_are_explicit_not_impossibility_claims(self):
        a, b = mapped("CCCBr"); site = rule.sites(a["mol"])[0]
        with patch.object(rule, "_geometry", side_effect=ValueError("No test conformer")):
            report = rule.geometry(a["mol"], b["mol"], site)
        self.assertEqual(report["status"], "unresolved")
        self.assertIn("not proof", report["note"])
        s = rule.participants(a["mol"], b["mol"], site)
        with self.assertRaises(ValueError): rule.check_conformations(a["mol"], *(s[k] for k in ("hydrogen", "beta", "alpha", "leaving")))

    def test_ring_conformer_cannot_use_acyclic_rotation_permission(self):
        from rdkit.Chem import AllChem
        a, b = mapped("BrC1CCCCC1"); site = rule.sites(a["mol"])[0]; s = rule.participants(a["mol"], b["mol"], site)
        settings = AllChem.ETKDGv3(); settings.randomSeed = 42
        self.assertEqual(AllChem.EmbedMolecule(a["mol"], settings), 0)
        with self.assertRaisesRegex(ValueError, "cyclic E2"):
            rule.check_conformations(a["mol"], *(s[k] for k in ("hydrogen", "beta", "alpha", "leaving")))

    def test_cached_geometry_cannot_be_corrupted_by_a_returned_payload(self):
        a, b = mapped("CCCBr"); site = rule.sites(a["mol"])[0]
        report = rule.geometry(a["mol"], b["mol"], site)
        report["status"] = "incorrect external mutation"
        self.assertEqual(rule.geometry(a["mol"], b["mol"], site)["status"], "anti candidate constructed")


if __name__ == "__main__": unittest.main()

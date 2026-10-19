"""Phase 3A independent structures through public match -> diagram -> run.

These cases are test fixtures only, not curated examples. Product expectations
are explicitly supplied, never manufactured using the production transform.
"""
import unittest
from unittest.mock import patch
from rdkit import Chem
from rdkit.Chem import Descriptors, rdMolDescriptors
from server import chemistry_server as service, hydration_rule as rule, reaction_engine as engine
from server import molecular_graph as graph, reaction_compatibility as compatibility
from server.reaction_diagrams import _species, _combine, _identity

ACID = {"catalyst": "acid", "solvent": "aqueous-protic"}


def canonical(smiles):
    return Chem.MolToSmiles(Chem.MolFromSmiles(smiles))


class HydrationCompatibilityTests(unittest.TestCase):
    def options(self, substrate, reagent="water", conditions=None):
        ref = {"name": "Independent hydration substrate", "smiles": substrate}
        result = service.match_reactions(ref, reagent, ACID if conditions is None else conditions)
        return ref, [r for r in result["reactions"] if r["mechanism"] == "Hydration"], result

    def check_option(self, ref, option, expected):
        self.assertEqual(option["productSmiles"], canonical(expected))
        self.assertEqual(option["byproducts"], [])
        self.assertEqual(option["assessment"]["status"], "model-match")
        self.assertTrue(option["assessment"]["canRun"])
        data = option["stoichiometry"]
        self.assertTrue(data["balanced"])
        self.assertEqual([r["coefficient"] for r in data["reactants"]], [1, 1])
        self.assertEqual(data["product"]["coefficient"], 1)
        self.assertEqual(option["productFormula"], rdMolDescriptors.CalcMolFormula(Chem.MolFromSmiles(expected)))
        self.assertAlmostEqual(data["product"]["molarMass"], Descriptors.MolWt(Chem.MolFromSmiles(expected)), places=6)
        self.assertTrue(any("Acid is regenerated" in v for v in data["notes"]))
        diagram = service.reaction_diagram(option["id"], ref, "water", ACID)
        self.assertEqual(diagram["products"][0]["smiles"], canonical(expected))
        self.assertTrue(diagram["highlightsAvailable"])
        self.assertIn('class="reaction-site"', diagram["svg"])
        before_rows = [a for a in diagram["atoms"] if a["side"] == "reactants"]
        after_rows = [a for a in diagram["atoms"] if a["side"] == "products"]
        before = {a["mapId"]: (a["element"], a["formalCharge"]) for a in before_rows}
        after = {a["mapId"]: (a["element"], a["formalCharge"]) for a in after_rows}
        self.assertEqual(len(before), len(before_rows)); self.assertEqual(len(after), len(after_rows))
        self.assertEqual(before, after); self.assertEqual(sum(a[1] for a in after.values()), 0)
        self.assertEqual(len(diagram["atomMap"]), len(before))
        self.assertEqual(len(diagram["bondsBroken"]), 1)
        self.assertEqual(set(diagram["bondsBroken"][0]["atoms"]), {"O", "H"})
        self.assertEqual(sorted(sorted(b["atoms"]) for b in diagram["bondsFormed"]), [["C", "H"], ["C", "O"]])
        self.assertEqual(len(diagram["bondOrderChanges"]), 1)
        change = diagram["bondOrderChanges"][0]
        self.assertEqual((change["before"], change["after"]), (2, 1))
        self.assertEqual(set(change["atomMaps"]), set(option["site"]["atomMaps"]))
        report = option["compatibility"]
        self.assertEqual(report["substrateSiteMaps"], option["site"]["atomMaps"])
        self.assertEqual(report["consumedDoubleBonds"], [option["site"]["atomMaps"]])
        self.assertEqual(set(report["validation"].values()), {"verified"})
        self.assertEqual({(tuple(sorted(e["atomMaps"])), e["before"], e["after"]) for e in report["editContract"]},
                         {(tuple(sorted(e["atomMaps"])), e["before"], e["after"]) for e in diagram["changes"]})
        p = option["site"]["parameters"]
        self.assertEqual(before[p["oxygen"]][0], "O"); self.assertEqual(before[p["hydrogen"]][0], "H")
        self.assertEqual(before[p["hydroxylHydrogen"]][0], "H")
        self.assertNotEqual(p["hydrogen"], p["hydroxylHydrogen"])
        self.assertEqual(set([p["oxygenCarbon"], p["hydrogenCarbon"]]), set(option["site"]["atomMaps"]))
        result = service.run_curated_reaction(option["id"], ref, "water", ACID)
        product = result["product"]
        self.assertEqual(product["smiles"], canonical(expected)); self.assertTrue(result["balanced"])
        self.assertEqual(product["representation"], "3d")
        self.assertEqual([(a["atomIndex"], a["mapId"], a["element"]) for a in after_rows],
                         [(a["index"], a["mapId"], a["element"]) for a in product["atomLinks"]])
        shape = Chem.MolFromMolBlock(product["molfile"], removeHs=False)
        self.assertTrue(shape.GetConformer().Is3D())
        # A 3D conformer can geometrically occupy either unsigned configuration.
        # The canonical net SMILES above, not that conformer, defines the outcome.
        self.assertEqual(Chem.MolToSmiles(Chem.MolFromSmiles(_identity(shape)), isomericSmiles=False),
                         Chem.MolToSmiles(Chem.MolFromSmiles(expected), isomericSmiles=False))
        # Independently derive configurations from the rendered coordinates.
        # Only net-specified distant centers are required to match; unsigned
        # newly formed centers remain unspecified in the authoritative result.
        geometry = Chem.Mol(shape)
        Chem.AssignStereochemistryFrom3D(geometry, replaceExistingTags=True)
        for atom in geometry.GetAtoms():
            atom.SetAtomMapNum(0)
        Chem.AssignCIPLabels(geometry)
        for center in option["stereochemistry"]["product"]["chiralCenters"]:
            if center["specified"]:
                atom = geometry.GetAtomWithIdx(center["atomIndex"])
                self.assertTrue(atom.HasProp('_CIPCode'))
                self.assertEqual(atom.GetProp('_CIPCode'), center["assignment"])
        self.assertIsNone(option["regioselectivity"]["ratios"])
        return diagram, result

    def check(self, substrate, products, count=None):
        ref, options, response = self.options(substrate)
        expected = {canonical(p) for p in products}
        self.assertEqual({r["productSmiles"] for r in options}, expected, response["unsupportedReasons"])
        self.assertEqual(len(options), len(expected) if count is None else count)
        for option in options:
            self.check_option(ref, option, option["productSmiles"])
        return options

    def reject(self, substrate, text):
        _, options, result = self.options(substrate)
        self.assertFalse(options)
        self.assertIn(text, " ".join(result["unsupportedReasons"]))

    def test_propene_markovnikov_is_propan_2_ol(self):
        r = self.check("C=CC", ["CC(O)C"])[0]
        self.assertIn("Markovnikov", r["regioselectivity"]["basis"])

    def test_ethylene_equivalent_ends(self):
        self.check("C=C", ["CCO"])

    def test_terminal_long_chains(self):
        for a, p in [("C=CCCC", "CC(O)CCC"), ("C=CCCCCCCCCCC", "CC(O)CCCCCCCCCC")]:
            with self.subTest(a=a): self.check(a, [p])

    def test_branched_terminal_tertiary_capture(self):
        self.check("C=C(C)CCC", ["CC(O)(C)CCC"])

    def test_unequal_substitution_internal_orientation(self):
        self.check("CCC=C(C)CCC", ["CCCC(O)(C)CCC"])

    def test_equivalent_symmetric_internal_single_option(self):
        r = self.check("CCC=CCC", ["CCC(O)CCC"])[0]
        self.assertIn("symmetry", r["regioselectivity"]["basis"])

    def test_inequivalent_internal_two_alcohols_without_ratios(self):
        for a, products in [("CC=CCC", ["CC(O)CCC", "CCC(O)CC"]), ("CC=CCCC", ["CC(O)CCCC", "CCC(O)CCC"])]:
            with self.subTest(a=a):
                rs = self.check(a, products)
                self.assertEqual(len({r["id"] for r in rs}), 2)
                self.assertTrue(all(r["regioselectivity"]["alternativeOrientations"] == 2 for r in rs))
                self.assertEqual({r["regioselectivity"]["oxygenCarbonMap"] for r in rs}, set(rs[0]["site"]["atomMaps"]))
                self.assertTrue(all("unresolved" in r["regioselectivity"]["basis"] for r in rs))

    def test_cyclic_5_to_8_membered_examples(self):
        for a, p in [("C1=CCCC1", "OC1CCCC1"), ("C1=CCCCC1", "OC1CCCCC1"),
                     ("C1=CCCCCC1", "OC1CCCCCC1"), ("C1=CCCCCCC1", "OC1CCCCCCC1")]:
            with self.subTest(a=a): self.check(a, [p])

    def test_methyl_substituted_cyclic_site(self):
        self.check("C1=C(C)CCCCC1", ["CC1(O)CCCCCC1"])

    def test_small_large_fused_and_exocyclic_rings_reject(self):
        for a, text in [("C1=CCC1", "4-membered"), ("C1=CCCCCCCC1", "5–8-membered"),
                        ("C1=C2CCCCC2CCC1", "Fused"), ("C=C1CCCCC1", "Exocyclic")]:
            with self.subTest(a=a): self.reject(a, text)

    def test_screened_styrene_benzylic_capture(self):
        r = self.check("C=Cc1ccccc1", ["CC(O)c1ccccc1"])[0]
        self.assertIn("benzylic", r["regioselectivity"]["basis"])

    def test_polyaryl_and_competing_conjugated_environments_reject(self):
        for a, text in [("C=C(c1ccccc1)c1ccccc1", "single screened"), ("C=CC=C", "Conjugated"),
                        ("C=C=C", "cumulated"), ("C=CC=O", "unsaturated"), ("C=CCc1ccccc1", "benzylic cation after a shift")]:
            with self.subTest(a=a): self.reject(a, text)

    def test_adjacent_hydride_and_alkyl_shift_risks_reject(self):
        for a in ["C=CC(C)C", "C=CC(C)(C)C", "C=C(C)C(C)C", "C=CC1CCCCC1"]:
            with self.subTest(a=a): self.reject(a, "shift" if "1" not in a else "ring migration")

    def test_screened_remote_primary_alcohol(self):
        rs = self.check("C=CCCCCCCCO", ["CC(O)CCCCCCCO"])
        self.assertTrue(any(g["type"] == "alcohol" and g["disposition"] == "preserved" for g in rs[0]["compatibility"]["groups"]))

    def test_screened_remote_secondary_alcohol(self):
        self.check("C=CCCCCCCC(O)C", ["CC(O)CCCCCCC(O)C"])

    def test_screened_remote_ether(self):
        r = self.check("C=CCCCCCCCOC", ["CC(O)CCCCCCCOC"])[0]
        self.assertTrue(any(g["type"] == "ether" and g["disposition"] == "preserved" for g in r["compatibility"]["groups"]))

    def test_screened_multiple_remote_alcohol_groups(self):
        self.check("C=CCCCCCCC(O)CO", ["CC(O)CCCCCCC(O)CO"])

    def test_short_intramolecular_oxygen_capture_screen(self):
        for a, size in [("C=CCCO", 4), ("C=CCCCO", 5), ("C=CCCCCO", 6), ("C=CCCCOC", 5)]:
            with self.subTest(a=a): self.reject(a, f"{size}-membered intramolecular oxygen capture")

    def test_acid_sensitive_oxygen_groups_reject(self):
        for a in ["C=CCO", "C=CCCCCCCC(O)(C)C", "C=CCCCCCCCOC(C)(C)C", "C=CCCCCCCC(O)O", "C=CCCCCCCCOCc1ccccc1"]:
            with self.subTest(a=a): self.reject(a, "Acid-sensitive")

    def test_other_competing_functional_groups_reject(self):
        for a, text in [("C=CCCCCCCC=O", "aldehyde"), ("C=CCCCCCCCC(=O)C", "ketone"),
                        ("C=CCCCCCCC(=O)OC", "ester"), ("C=CCCCCCCC(=O)O", "carboxylic acid"),
                        ("C=CCCCCCCC#C", "alkyne"), ("C=CCCCCCCCOO", "peroxide"), ("C=CCCCCCCCc1ccccc1", "Remote aromatic")]:
            with self.subTest(a=a): self.reject(a, text)

    def test_unvalidated_elements_have_precise_hydration_reasons(self):
        for symbol in ["F", "Cl", "Br", "N", "S"]:
            with self.subTest(symbol=symbol): self.reject("C=CCCC" + symbol, symbol + " at substrate atom")

    def test_distant_specified_centers_retained_both_enantiomers(self):
        for tag in ["@", "@@"]:
            a, p = f"C=CC[C{tag}H](C)CC", f"CC(O)C[C{tag}H](C)CC"
            r = self.check(a, [p])[0]
            specified = [c for c in r["stereochemistry"]["product"]["chiralCenters"] if c["specified"]]
            self.assertEqual(len(specified), 1)
            self.assertIn(specified[0]["assignment"], {"R", "S"})

    def test_remote_specified_alcohol_center_retained(self):
        self.check("C=CCCCCCC[C@H](O)C", ["CC(O)CCCCCC[C@H](O)C"])

    def test_cip_is_independently_recomputed_not_cached_from_maps(self):
        a = "C=CC[C@H](CC)CC(C)C"
        r = self.check(a, ["CC(O)C[C@H](CC)CC(C)C"])[0]
        for side in ["reactant", "product"]:
            # Independent RDKit CIP on unmapped structures, not production labels.
            smiles = a if side == "reactant" else r["productSmiles"]
            mol = Chem.MolFromSmiles(smiles)
            Chem.AssignCIPLabels(mol)
            expected = sorted(at.GetProp('_CIPCode') for at in mol.GetAtoms() if at.HasProp('_CIPCode'))
            actual = sorted(c["assignment"] for c in r["stereochemistry"][side]["chiralCenters"] if c["specified"])
            self.assertEqual(actual, expected)

    def test_near_site_specified_center_not_silently_dropped(self):
        self.reject("C=C[C@H](C)CC", "at/adjacent")

    def test_e_and_z_selected_geometry_consumed(self):
        for a, product in [("CC/C=C/CC", "CCC(O)CCC"), ("CC/C=C\\CC", "CCC(O)CCC"), ("C1/C=C/CCCCC1", "OC1CCCCCCC1")]:
            with self.subTest(a=a):
                r = self.check(a, [product])[0]
                self.assertTrue(r["stereochemistry"]["reactant"]["alkenes"][0]["specified"])
                self.assertEqual(r["stereochemistry"]["product"]["alkenes"], [])

    def test_normalization_does_not_silently_erase_directional_input(self):
        for a in ["C1/C=C/CCC1", "C1/C=C\\CCC1", "C/C=C"]:
            with self.subTest(a=a): self.reject(a, "directional C=C annotation")
        # The last input canonicalizes to the existing propene preset, but the
        # same hydration-only guard must apply. Other pathways keep old behavior.
        hydrogenation = service.match_reactions({"smiles": "C/C=C"}, "hydrogen", {"catalyst": "metal"})
        self.assertEqual([r["productSmiles"] for r in hydrogenation["reactions"] if r["mechanism"] == "Hydrogenation"], ["CCC"])

    def test_new_chiral_centers_and_faces_unassigned(self):
        r = self.check("C=CCC", ["CC(O)CC"])[0]
        centers = r["stereochemistry"]["product"]["chiralCenters"]
        self.assertTrue(centers); self.assertTrue(all(not c["specified"] and c["assignment"] is None for c in centers))
        self.assertIn("syn/anti", r["stereochemistry"]["effect"])
        self.assertTrue(any("3D conformer" in v for v in r["information"]["limitations"]))

    def test_widely_separated_sites_remain_independently_selectable(self):
        rs = self.check("C=CCCCCCCCCC=C", ["CC(O)CCCCCCCCC=C"], count=2)
        self.assertEqual(len({r["id"] for r in rs}), 2)
        self.assertEqual(len({tuple(r["site"]["atomMaps"]) for r in rs}), 2)
        self.assertTrue(all(len(graph.find_alkenes(Chem.MolFromSmiles(r["productSmiles"]))) == 1 for r in rs))

    def test_unselected_ez_preserved_with_four_site_orientation_options(self):
        a = "C/C=C/CCCCCCCC/C=C\\C"
        expected = ["CC(O)CCCCCCCCC/C=C\\C", "CCC(O)CCCCCCCC/C=C\\C",
                    "C/C=C/CCCCCCCCC(O)CC", "C/C=C/CCCCCCCCCC(C)O"]
        rs = self.check(a, expected)
        for r in rs:
            alkenes = r["stereochemistry"]["product"]["alkenes"]
            self.assertEqual(len(alkenes), 1); self.assertTrue(alkenes[0]["specified"])

    def test_short_diene_cationic_cyclization_risk_rejected(self):
        self.reject("C=CCCCCC=C", "6-membered intramolecular carbon capture")

    def test_wrong_reagents_do_not_create_hydration(self):
        for reagent in ["hydrogen", "hydroxide", "bromine", "hydrogen-bromide", "ethanol"]:
            with self.subTest(reagent=reagent): self.assertFalse(self.options("C=CC", reagent)[1])

    def test_invalid_electronic_relative_stereo_and_disconnected_inputs(self):
        for a in ["bad-smiles", "C=C.O", "C=CCCC[O-]", "C=CCC[CH2]", "C=CC[13CH2]CO", "C=CC[C@H](C)CC |&1:3|"]:
            with self.subTest(a=a), self.assertRaises(service.ChemistryError): self.options(a)

    def test_size_limit_counts_entire_added_water(self):
        # C25 alkene has 75 explicit atoms; hydrated C25H52O has 78.
        rs = self.check("C=" + "C" * 24, ["CC(O)" + "C" * 23])
        self.assertEqual(Chem.AddHs(Chem.MolFromSmiles(rs[0]["productSmiles"])).GetNumAtoms(), 78)
        self.reject("C=" + "C" * 25, "exceed 80 explicit atoms")

    def test_no_formula_cid_or_name_lookup_decides_eligibility(self):
        with patch.dict(service.REACTANTS, {}, clear=True):
            ref = {"smiles": "CC=CCCC", "name": "not a preset", "cid": 1}
            result = service.match_reactions(ref, {"smiles": "O", "name": "not called water"}, ACID)
        rs = [r for r in result["reactions"] if r["mechanism"] == "Hydration"]
        self.assertEqual({r["productSmiles"] for r in rs}, {canonical("CC(O)CCCC"), canonical("CCC(O)CCC")})

    def test_missing_and_none_acid_are_activation_gaps_not_reference_mismatch(self):
        for conditions in [{}, {"catalyst": "none"}]:
            ref, rs, _ = self.options("C=CC", conditions=conditions)
            self.assertEqual(len(rs), 1)
            self.assertEqual(rs[0]["assessment"]["status"], "activation-required")
            self.assertEqual(rs[0]["reasoning"]["label"], "Acid activation required")
            self.assertFalse(rs[0]["assessment"]["canRun"])
            preview = service.reaction_diagram(rs[0]["id"], ref, "water", conditions)
            self.assertIn("Conditional net hydration", preview["note"])
            with self.assertRaisesRegex(service.ChemistryError, "Acid activation is required"):
                service.run_curated_reaction(rs[0]["id"], ref, "water", conditions)

    def test_wrong_catalysts_not_claimed_chemically_unfavorable(self):
        for catalyst in ["metal", "lindlar", "osmium", "radical"]:
            conditions = {"catalyst": catalyst}
            ref, rs, _ = self.options("C=CC", conditions=conditions)
            self.assertEqual(rs[0]["assessment"]["status"], "unevaluated")
            self.assertFalse(rs[0]["assessment"]["canRun"])
            self.assertNotEqual(rs[0]["reasoning"]["label"], "Unfavorable")
            with self.assertRaisesRegex(service.ChemistryError, "not a validated acid"):
                service.run_curated_reaction(rs[0]["id"], ref, "water", conditions)

    def test_unknown_or_competing_medium_not_forced_to_a_product(self):
        for solvent, text in [("dry", "conflicts"), ("ethanolic-protic", "compete"), ("polar-aprotic", "not evaluated")]:
            conditions = {"catalyst": "acid", "solvent": solvent}
            ref, rs, _ = self.options("C=CC", conditions=conditions)
            self.assertEqual(rs[0]["assessment"]["status"], "unevaluated")
            with self.assertRaisesRegex(service.ChemistryError, text):
                service.run_curated_reaction(rs[0]["id"], ref, "water", conditions)

    def test_actual_water_and_acid_allow_qualitative_model_without_rates(self):
        for conditions in [{"catalyst": "acid"}, {**ACID, "temperature": "ambient"}, {**ACID, "temperature": "heated"}]:
            ref, rs, _ = self.options("C=CC", conditions=conditions)
            self.assertTrue(rs[0]["assessment"]["canRun"])
            self.assertEqual(rs[0]["reasoning"]["label"], "Possible")
            self.assertTrue(service.run_curated_reaction(rs[0]["id"], ref, "water", conditions)["balanced"])

    def test_reversed_input_slots_preserve_mapping_and_water_amounts(self):
        ref, rs, _ = self.options("CC=CCCC")
        reverse = [r for r in service.match_reactions("water", ref, ACID)["reactions"] if r["mechanism"] == "Hydration"]
        # Custom drawing IDs retain the public input-slot namespace; map
        # identities and selected net chemistry, not those IDs, must agree.
        self.assertEqual([r["productSmiles"] for r in rs], [r["productSmiles"] for r in reverse])
        for r, back in zip(rs, reverse):
            self.assertEqual(r["compatibility"], back["compatibility"])
            forward_d = service.reaction_diagram(r["id"], ref, "water", ACID)
            reverse_d = service.reaction_diagram(back["id"], "water", ref, ACID)
            self.assertEqual(forward_d["changes"], reverse_d["changes"])
            self.assertEqual([(a["side"], a["mapId"], a["element"], a["formalCharge"]) for a in forward_d["atoms"]],
                             [(a["side"], a["mapId"], a["element"], a["formalCharge"]) for a in reverse_d["atoms"]])
            self.assertEqual(back["stoichiometry"]["reactants"][0]["inputSlot"], 0)
            self.assertAlmostEqual(back["stoichiometry"]["reactants"][0]["molarMass"], 18.015, places=6)

    def valid_edit(self, source="C=CC[C@H](C)CC"):
        a, n = _species("a", {"name": "Source", "smiles": source}, 1)
        b, _ = _species("b", {"name": "Water", "smiles": "O"}, n)
        site = rule.sites(a["mol"])[0]
        product = engine.transform("Hydration", [a, b], site)[0]
        return a["mol"], b["mol"], site, _combine([a, b]), product

    def test_invalid_orientation_and_nonalkene_sites_fail_closed(self):
        mol = Chem.MolFromSmiles("C=CC")
        for site in [(0, 1, 0), (0, 1, 2), (0, 0, 0), (1, 2, 1)]:
            self.assertFalse(rule.assess(mol, site)["eligible"])

    def test_reagent_validator_rejects_hydroxide_and_nonwater_oxygen(self):
        substrate, _, site, _, _ = self.valid_edit()
        for smiles in ["[OH-]", "CO", "OO", "[OH2+]", "[18OH2]"]:
            reagent, _ = _species("b", {"name": "Not neutral water", "smiles": smiles}, 100)
            with self.subTest(smiles=smiles), self.assertRaisesRegex(ValueError, "actual neutral water"):
                rule.edit_contract(substrate, reagent["mol"], site)

    def test_exact_contract_rejects_unaffected_bond_changes(self):
        a, b, site, before, after = self.valid_edit()
        tampered = Chem.RWMol(after)
        reactive = {frozenset(e["atomMaps"]) for e in rule.edit_contract(a, b, site)}
        bond = next(x for x in tampered.GetBonds() if frozenset((x.GetBeginAtom().GetAtomMapNum(), x.GetEndAtom().GetAtomMapNum())) not in reactive and x.GetBeginAtom().GetAtomicNum() == x.GetEndAtom().GetAtomicNum() == 6)
        tampered.RemoveBond(bond.GetBeginAtomIdx(), bond.GetEndAtomIdx())
        with self.assertRaisesRegex(ValueError, "unaffected bond"):
            rule.validate(before, tampered.GetMol(), a, b, site)

    def test_exact_contract_rejects_remote_stereo_inversion(self):
        a, b, site, before, after = self.valid_edit()
        tampered = Chem.Mol(after)
        next(at for at in tampered.GetAtoms() if at.GetChiralTag() != Chem.ChiralType.CHI_UNSPECIFIED).InvertChirality()
        with self.assertRaisesRegex(ValueError, "configuration|stereo"):
            rule.validate(before, tampered, a, b, site)

    def test_exact_contract_rejects_swapped_water_hydrogen_identity(self):
        a, b, site, before, after = self.valid_edit()
        p = rule.participants(a, b, site)
        atoms = {at.GetAtomMapNum(): at for at in after.GetAtoms()}
        atoms[p["hydrogen"]].SetAtomMapNum(p["hydroxylHydrogen"])
        atoms[p["hydroxylHydrogen"]].SetAtomMapNum(p["hydrogen"])
        with self.assertRaisesRegex(ValueError, "unaffected bond|required reactive"):
            rule.validate(before, after, a, b, site)

    def test_exact_contract_rejects_invented_new_configuration(self):
        a, b, site, before, after = self.valid_edit("C=CCC")
        target = rule.participants(a, b, site)["oxygenCarbon"]
        atom = next(at for at in after.GetAtoms() if at.GetAtomMapNum() == target)
        atom.SetChiralTag(Chem.ChiralType.CHI_TETRAHEDRAL_CCW)
        with self.assertRaisesRegex(ValueError, "invented|introduced|unspecified|configuration"):
            rule.validate(before, after, a, b, site)

    def test_input_atom_maps_do_not_break_symmetry_or_namespace(self):
        a = {"smiles": "[CH3:42][CH:3]=[CH:25][CH3:11]"}
        rs = [r for r in service.match_reactions(a, "water", ACID)["reactions"] if r["mechanism"] == "Hydration"]
        self.assertEqual(len(rs), 1); self.assertEqual(rs[0]["productSmiles"], canonical("CC(O)CC"))
        self.check_option(a, rs[0], "CC(O)CC")

    def test_other_addition_paths_keep_old_scope_and_orientations(self):
        new_hx_expectations = {"CC=CCC": ["CC(Br)CCC", "CCC(Br)CC"], "CC/C=C/CC": ["CCC(Br)CCC"],
                               "C=CC[C@H](C)CC": ["CC(Br)C[C@H](C)CC"], "C=Cc1ccccc1": ["CC(Br)c1ccccc1"]}
        for source in ["CC=CCC", "CC/C=C/CC", "C=CC[C@H](C)CC", "C=Cc1ccccc1", "C=CCCCCCCCOC"]:
            r = service.match_reactions({"smiles": source}, "hydrogen-bromide")
            options = [v for v in r["reactions"] if v["mechanism"] == "Hydrohalogenation"]
            if source in new_hx_expectations:
                # Phase 3B is an explicitly separate HX consumer. Hydration
                # products/tests above stay unchanged; HBr ethers still reject.
                self.assertEqual({v["productSmiles"] for v in options}, {canonical(p) for p in new_hx_expectations[source]})
            else:
                self.assertFalse(options)
        self.assertEqual(next(r["productSmiles"] for r in service.match_reactions({"smiles": "C=CC"}, "hydrogen-bromide")["reactions"] if r["mechanism"] == "Hydrohalogenation"), canonical("CC(Br)C"))

    def test_hydration_mechanism_not_falsely_claimed_implemented(self):
        ref, rs, _ = self.options("C=CC")
        self.assertEqual(rs[0]["information"]["capabilities"]["mappedMechanism"], "unsupported")
        self.assertIsNone(service.reaction_diagram(rs[0]["id"], ref, "water", ACID)["mechanism"])

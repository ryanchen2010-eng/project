"""Phase 3B independent net expectations through public match/diagram/run.

Never added to the curated example collection. No expected product is generated
by the production edit, and no coordinate stereochemistry defines a net outcome.
"""
import unittest
from unittest.mock import patch
from rdkit import Chem
from rdkit.Chem import Descriptors, rdMolDescriptors
from server import chemistry_server as service, hydrohalogenation_rule as rule, reaction_engine as engine
from server import molecular_graph as graph
from server.reaction_diagrams import _species, _combine, _identity
from server.reaction_conditions import assess_conditions

IONIC = {"solvent": "dry", "catalyst": "none"}
AMBIENT_HCL = {**IONIC, "temperature": "ambient"}
REAGENTS = [("hydrogen-chloride", "Cl"), ("hydrogen-bromide", "Br"), ("hydrogen-iodide", "I")]


def canonical(smiles): return Chem.MolToSmiles(Chem.MolFromSmiles(smiles))


class HydrohalogenationCompatibilityTests(unittest.TestCase):
    def options(self, substrate, reagent="hydrogen-bromide", conditions=None):
        ref = {"name": "Independent HX substrate", "smiles": substrate}
        result = service.match_reactions(ref, reagent, IONIC if conditions is None else conditions)
        return ref, [r for r in result["reactions"] if r["mechanism"] == "Hydrohalogenation"], result

    def check_option(self, ref, option, expected, reagent, conditions):
        expected = canonical(expected)
        self.assertEqual(option["productSmiles"], expected)
        self.assertEqual(option["byproducts"], [])
        self.assertTrue(option["assessment"]["canRun"])
        self.assertEqual(option["hxModel"]["mode"], "ionic")
        self.assertTrue(option["hxModel"]["consumedReagent"])
        self.assertIsNone(option["regioselectivity"]["ratios"])
        amounts = option["stoichiometry"]
        self.assertTrue(amounts["balanced"])
        self.assertEqual([v["coefficient"] for v in amounts["reactants"]], [1, 1])
        self.assertEqual(amounts["product"]["coefficient"], 1)
        self.assertEqual(amounts["excludedInputs"], [])
        self.assertAlmostEqual(amounts["product"]["molarMass"], Descriptors.MolWt(Chem.MolFromSmiles(expected)), places=6)
        self.assertEqual(option["productFormula"], rdMolDescriptors.CalcMolFormula(Chem.MolFromSmiles(expected)))
        self.assertTrue(any("HX is not a regenerated acid catalyst" in v for v in amounts["notes"]))
        d = service.reaction_diagram(option["id"], ref, reagent, conditions)
        self.assertTrue(d["highlightsAvailable"]); self.assertIn('class="reaction-site"', d["svg"])
        self.assertEqual([p["smiles"] for p in d["products"]], [expected])
        before_rows = [a for a in d["atoms"] if a["side"] == "reactants"]
        after_rows = [a for a in d["atoms"] if a["side"] == "products"]
        before = {a["mapId"]: (a["element"], a["formalCharge"]) for a in before_rows}
        after = {a["mapId"]: (a["element"], a["formalCharge"]) for a in after_rows}
        self.assertEqual(len(before_rows), len(before)); self.assertEqual(len(after_rows), len(after))
        self.assertEqual(before, after); self.assertEqual(sum(v[1] for v in after.values()), 0)
        self.assertEqual(len(d["atomMap"]), len(before))
        params = option["site"]["parameters"]
        self.assertEqual(set(option["site"]["atomMaps"]), {params["hydrogenCarbon"], params["halogenCarbon"]})
        self.assertEqual(before[params["hydrogen"]][0], "H")
        self.assertEqual(before[params["halogen"]][0], params["halogenElement"])
        hx_maps = {a["mapId"] for a in before_rows if a["speciesIndex"] == 1}
        self.assertEqual(hx_maps, {params["hydrogen"], params["halogen"]})
        self.assertEqual(len(d["bondsBroken"]), 1)
        self.assertEqual(set(d["bondsBroken"][0]["atomMaps"]), hx_maps)
        formed = {frozenset(v["atomMaps"]) for v in d["bondsFormed"]}
        self.assertEqual(formed, {frozenset((params["hydrogen"], params["hydrogenCarbon"])),
                                 frozenset((params["halogen"], params["halogenCarbon"]))})
        self.assertEqual(len(d["bondOrderChanges"]), 1)
        change = d["bondOrderChanges"][0]
        self.assertEqual((change["before"], change["after"]), (2, 1))
        self.assertEqual(set(change["atomMaps"]), set(option["site"]["atomMaps"]))
        report = option["compatibility"]
        self.assertEqual(report["consumedDoubleBonds"], [option["site"]["atomMaps"]])
        self.assertEqual(set(report["validation"].values()), {"verified"})
        self.assertEqual({(tuple(sorted(v["atomMaps"])), v["before"], v["after"]) for v in report["editContract"]},
                         {(tuple(sorted(v["atomMaps"])), v["before"], v["after"]) for v in d["changes"]})
        p = service.run_curated_reaction(option["id"], ref, reagent, conditions)["product"]
        self.assertEqual(p["smiles"], expected); self.assertEqual(p["representation"], "3d")
        self.assertEqual([(a["atomIndex"], a["mapId"], a["element"]) for a in after_rows],
                         [(a["index"], a["mapId"], a["element"]) for a in p["atomLinks"]])
        shape = Chem.MolFromMolBlock(p["molfile"], removeHs=False)
        self.assertTrue(shape.GetConformer().Is3D())
        self.assertEqual(Chem.MolToSmiles(Chem.MolFromSmiles(_identity(shape)), isomericSmiles=False),
                         Chem.MolToSmiles(Chem.MolFromSmiles(expected), isomericSmiles=False))
        # Independently derive the specified distant configuration from actual
        # rendered coordinates. Newly unsigned centers may occupy either face.
        coordinates = Chem.Mol(shape)
        Chem.AssignStereochemistryFrom3D(coordinates, replaceExistingTags=True)
        for atom in coordinates.GetAtoms(): atom.SetAtomMapNum(0)
        Chem.AssignCIPLabels(coordinates)
        for center in option["stereochemistry"]["product"]["chiralCenters"]:
            if center["specified"]:
                atom = coordinates.GetAtomWithIdx(center["atomIndex"])
                self.assertTrue(atom.HasProp('_CIPCode'))
                self.assertEqual(atom.GetProp('_CIPCode'), center["assignment"])
        return d, p

    def check(self, source, products, reagent="hydrogen-bromide", conditions=IONIC, count=None):
        ref, rs, response = self.options(source, reagent, conditions)
        expected = {canonical(p) for p in products}
        self.assertEqual({r["productSmiles"] for r in rs}, expected, response["unsupportedReasons"])
        self.assertEqual(len(rs), len(expected) if count is None else count)
        for r in rs: self.check_option(ref, r, r["productSmiles"], reagent, conditions)
        return rs

    def reject(self, source, reason, reagent="hydrogen-bromide", conditions=None):
        _, rs, response = self.options(source, reagent, conditions)
        self.assertFalse(rs)
        self.assertIn(reason, " ".join(response["unsupportedReasons"]))

    def test_ethene_and_propene_all_three_actual_hx_reagents(self):
        for reagent, x in REAGENTS:
            self.check("C=C", ["CC" + x], reagent)
            r = self.check("C=CC", [f"CC({x})C"], reagent)[0]
            self.assertEqual(r["hxModel"]["hydrogenHalide"], "H" + x)
            self.assertIn("Markovnikov", r["regioselectivity"]["basis"])

    def test_long_terminal_chains_beyond_presets(self):
        for reagent, x in REAGENTS:
            for a, p in [("C=CCCC", f"CC({x})CCC"), ("C=CCCCCCCCCCC", f"CC({x})CCCCCCCCCC")]:
                with self.subTest(a=a, x=x): self.check(a, [p], reagent)

    def test_branched_terminal_tertiary_capture(self):
        for reagent, x in REAGENTS: self.check("C=C(C)CCC", [f"CC({x})(C)CCC"], reagent)

    def test_unequal_internal_substitution_justifies_orientation(self):
        for reagent, x in REAGENTS: self.check("CCC=C(C)CCC", [f"CCCC({x})(C)CCC"], reagent)

    def test_symmetric_internal_equivalence_not_duplicate_orientations(self):
        for reagent, x in REAGENTS:
            r = self.check("CCC=CCC", [f"CCC({x})CCC"], reagent)[0]
            self.assertIn("equivalent", r["regioselectivity"]["basis"])

    def test_unsymmetric_internal_all_hx_constitutional_alternatives(self):
        for reagent, x in REAGENTS:
            for a, expected in [("CC=CCC", [f"CC({x})CCC", f"CCC({x})CC"]),
                                ("CC=CCCC", [f"CC({x})CCCC", f"CCC({x})CCC"])]:
                with self.subTest(a=a, x=x):
                    rs = self.check(a, expected, reagent)
                    self.assertEqual(len({r["id"] for r in rs}), 2)
                    self.assertTrue(all(r["regioselectivity"]["alternativeOrientations"] == 2 for r in rs))
                    self.assertEqual({r["regioselectivity"]["halogenCarbonMap"] for r in rs}, set(rs[0]["site"]["atomMaps"]))

    def test_tetrasubstituted_inequivalent_tertiary_capture_alternatives(self):
        self.check("CC(C)=C(C)CC", ["CC(Br)(C)C(C)CC", "CC(C)C(Br)(C)CC"])

    def test_cyclic_five_to_eight_membered_bounded_examples(self):
        for a, p in [("C1=CCCC1", "BrC1CCCC1"), ("C1=CCCCC1", "BrC1CCCCC1"),
                     ("C1=CCCCCC1", "BrC1CCCCCC1"), ("C1=CCCCCCC1", "BrC1CCCCCCC1")]:
            with self.subTest(a=a): self.check(a, [p])
        for reagent, x in REAGENTS: self.check("C1=CCCCC1", [x + "C1CCCCC1"], reagent)

    def test_methyl_cycloalkene_markovnikov_capture(self):
        for reagent, x in REAGENTS: self.check("C1=C(C)CCCC1", [f"CC1({x})CCCCC1"], reagent)

    def test_unvalidated_ring_models_reject_not_declared_impossible(self):
        for a, reason in [("C1=CCC1", "4-membered"), ("C1=CCCCCCCC1", "5–8-membered"),
                          ("C1=C2CCCCC2CCC1", "fused"), ("C=C1CCCCC1", "Exocyclic"), ("C=CC1CCCCC1", "ring migration")]:
            with self.subTest(a=a): self.reject(a, reason)

    def test_styrene_all_hx_benzylic_capture(self):
        for reagent, x in REAGENTS:
            r = self.check("C=Cc1ccccc1", [f"CC({x})c1ccccc1"], reagent)[0]
            self.assertIn("benzylic", r["regioselectivity"]["basis"])

    def test_alpha_methyl_styrene_screened_resonance(self):
        self.check("C=C(C)c1ccccc1", ["CC(Br)(C)c1ccccc1"])

    def test_beta_methyl_styrene_valid_ez_consumption(self):
        for a in ["C/C=C/c1ccccc1", "C/C=C\\c1ccccc1"]:
            with self.subTest(a=a): self.check(a, ["CCC(Br)c1ccccc1"])

    def test_competing_resonance_and_conjugation_reject(self):
        for a, reason in [("C=C(c1ccccc1)c1ccccc1", "isolated carbocyclic phenyl"),
                          ("CC(C)=Cc1ccccc1", "Competing benzylic"), ("C=CC=C", "Conjugated"),
                          ("C=C=C", "cumulated"), ("C=CC=O", "adjacent unsaturated"), ("C=CCc1ccccc1", "benzylic cation")]:
            with self.subTest(a=a): self.reject(a, reason)

    def test_hydride_and_quaternary_alkyl_shift_risks_reject(self):
        for a in ["C=CC(C)C", "C=CC(C)(C)C", "C=C(C)C(C)C"]:
            with self.subTest(a=a): self.reject(a, "hydride/alkyl-shift")

    def test_screened_remote_primary_alcohol_hcl_only(self):
        r = self.check("C=CCCCCCCCO", ["CC(Cl)CCCCCCCO"], "hydrogen-chloride", AMBIENT_HCL)[0]
        self.assertTrue(r["hxModel"]["oxygenSpectators"])
        self.assertTrue(any(g["type"] == "alcohol" and g["disposition"] == "preserved" for g in r["compatibility"]["groups"]))

    def test_screened_remote_ordinary_ether_hcl_only(self):
        self.check("C=CCCCCCCCOC", ["CC(Cl)CCCCCCCOC"], "hydrogen-chloride", AMBIENT_HCL)

    def test_remote_secondary_ether_chiral_center_retained(self):
        self.check("C=CCCCCCCCO[C@H](C)CC", ["CC(Cl)CCCCCCCO[C@H](C)CC"], "hydrogen-chloride", AMBIENT_HCL)

    def test_multiple_screened_primary_alcohol_groups_hcl(self):
        self.check("C=CCCCCCCC(CO)CO", ["CC(Cl)CCCCCCC(CO)CO"], "hydrogen-chloride", AMBIENT_HCL)

    def test_hbr_hi_do_not_inherit_hcl_oxygen_permissions(self):
        for reagent in ["hydrogen-bromide", "hydrogen-iodide"]:
            for a in ["C=CCCCCCCCO", "C=CCCCCCCCOC", "C=CCCCCCCCO[C@H](C)CC"]:
                with self.subTest(a=a, reagent=reagent): self.reject(a, "C–O cleavage", reagent)

    def test_hcl_oxygen_capture_ring_sizes(self):
        for a, size in [("C=CCCO", 4), ("C=CCCCO", 5), ("C=CCCCCO", 6), ("C=CCCCOC", 5)]:
            with self.subTest(a=a): self.reject(a, f"{size}-membered intramolecular oxygen capture", "hydrogen-chloride", AMBIENT_HCL)

    def test_hcl_secondary_tertiary_and_labile_oxygen_groups_excluded(self):
        for a in ["C=CCCCCCCC(O)C", "C=CCCCCCCC(O)(C)C", "C=CCCCCCCCOC(C)(C)C", "C=CCO", "C=CCCCCCCC(O)O"]:
            with self.subTest(a=a): self.reject(a, "Only unactivated primary", "hydrogen-chloride", AMBIENT_HCL)

    def test_hcl_oxygen_model_requires_explicit_ambient_for_3d(self):
        ref, rs, _ = self.options("C=CCCCCCCCO", "hydrogen-chloride", {})
        self.assertEqual(len(rs), 1); self.assertFalse(rs[0]["assessment"]["canRun"])
        self.assertEqual(rs[0]["assessment"]["status"], "missing")
        self.assertIn("temperature", rs[0]["assessment"]["missingSettings"])
        with self.assertRaisesRegex(service.ChemistryError, "explicitly ambient"):
            service.run_curated_reaction(rs[0]["id"], ref, "hydrogen-chloride")
        self.assertIn("Conditional ionic HX", service.reaction_diagram(rs[0]["id"], ref, "hydrogen-chloride")["note"])

    def test_heated_hcl_oxygen_model_does_not_claim_selective_capture(self):
        self.reject("C=CCCCCCCCOC", "Heated HCl", "hydrogen-chloride", {**IONIC, "temperature": "heated"})

    def test_other_functional_groups_fail_closed(self):
        for a, reason in [("C=CCCCCCCC=O", "aldehyde"), ("C=CCCCCCCC(=O)C", "ketone"),
                          ("C=CCCCCCCC(=O)OC", "ester"), ("C=CCCCCCCC(=O)O", "carboxylic acid"),
                          ("C=CCCCCCCC#C", "alkyne"), ("C=CCCCCCCCOO", "Peroxide"), ("C=CCCCCCCCc1ccccc1", "Additional aromatic")]:
            with self.subTest(a=a): self.reject(a, reason)

    def test_unvalidated_substrate_elements_have_precise_messages(self):
        for symbol in ["F", "Cl", "Br", "I", "N", "S"]:
            with self.subTest(symbol=symbol): self.reject("C=CCCC" + symbol, symbol + " at substrate atom")

    def test_valid_e_and_z_all_hx_consumed_without_new_assignments(self):
        for reagent, x in REAGENTS:
            for a in ["CC/C=C/CC", "CC/C=C\\CC"]:
                r = self.check(a, [f"CCC({x})CCC"], reagent)[0]
                self.assertTrue(r["stereochemistry"]["reactant"]["alkenes"][0]["specified"])
                self.assertEqual(r["stereochemistry"]["product"]["alkenes"], [])
                self.assertTrue(all(not c["specified"] for c in r["stereochemistry"]["product"]["chiralCenters"]))

    def test_valid_trans_cyclooctene_ionic_net(self):
        self.check("C1/C=C/CCCCC1", ["BrC1CCCCCCC1"])

    def test_new_and_originally_unspecified_centers_not_invented(self):
        r = self.check("C=CCC", ["CC(Br)CC"])[0]
        cs = r["stereochemistry"]["product"]["chiralCenters"]
        self.assertTrue(cs); self.assertTrue(all(not c["specified"] and c["assignment"] is None for c in cs))
        self.assertIn("syn/anti", r["stereochemistry"]["effect"])

    def test_distant_specified_centers_both_enantiomers_all_hx(self):
        for reagent, x in REAGENTS:
            for tag in ["@", "@@"]:
                r = self.check(f"C=CC[C{tag}H](C)CC", [f"CC({x})C[C{tag}H](C)CC"], reagent)[0]
                self.assertEqual(sum(c["specified"] for c in r["stereochemistry"]["product"]["chiralCenters"]), 1)

    def test_physical_retention_can_change_cip_letter_after_chlorine_addition(self):
        for tag, before, after in [("@", "S", "R"), ("@@", "R", "S")]:
            a, expected = f"C=CCCC[C{tag}H](C)CCCCO", f"CC(Cl)CCC[C{tag}H](C)CCCCO"
            r = self.check(a, [expected], "hydrogen-chloride", AMBIENT_HCL)[0]
            for side, smiles, letter in [("reactant", a, before), ("product", expected, after)]:
                molecule = Chem.MolFromSmiles(smiles); Chem.AssignCIPLabels(molecule)
                independent = [at.GetProp('_CIPCode') for at in molecule.GetAtoms() if at.HasProp('_CIPCode')]
                self.assertEqual(independent, [letter])
                self.assertEqual([c["assignment"] for c in r["stereochemistry"][side]["chiralCenters"] if c["specified"]], independent)

    def test_at_adjacent_specified_center_rejected_without_stereo_loss(self):
        self.reject("C=C[C@H](C)CC", "at/adjacent")

    def test_distinct_multiple_sites_have_selectable_products(self):
        self.check("C=CCCCCCCCCC=CC", ["CC(Br)CCCCCCCCC=CC", "C=CCCCCCCCCC(Br)CC", "C=CCCCCCCCCCC(Br)C"])

    def test_proven_equivalent_sites_group_one_mapped_representative(self):
        for reagent, x in REAGENTS:
            r = self.check("C=CCCCCCCCCC=C", [f"CC({x})CCCCCCCCC=C"], reagent)[0]
            equivalents = r["site"]["parameters"]["equivalentSiteAtomMaps"]
            self.assertEqual(len(equivalents), 2); self.assertNotEqual(equivalents[0], equivalents[1])
            self.assertIn("2 graph-equivalent", r["site"]["label"])
            self.assertTrue(any(f["factor"] == "equivalent-sites" for f in r["reasoning"]["factors"]))
            self.assertEqual(len(graph.find_alkenes(Chem.MolFromSmiles(r["productSmiles"]))), 1)

    def test_unselected_ez_preserved_at_multiple_inequivalent_sites(self):
        expected = ["CC(Br)CCCCCCCCC/C=C\\C", "CCC(Br)CCCCCCCC/C=C\\C", "C/C=C/CCCCCCCCC(Br)CC", "C/C=C/CCCCCCCCCC(C)Br"]
        rs = self.check("C/C=C/CCCCCCCC/C=C\\C", expected)
        for r in rs:
            alkenes = r["stereochemistry"]["product"]["alkenes"]
            self.assertEqual(len(alkenes), 1); self.assertTrue(alkenes[0]["specified"])

    def test_automorphism_is_not_just_a_formula_or_rank_guess(self):
        a = Chem.MolFromSmiles("C=CCCCCCCCCC=CC")
        sites = rule.sites(a)
        self.assertFalse(rule.equivalent_sites(a, sites[0], sites[-1]))
        same = Chem.MolFromSmiles("C=CCCCCCCCCC=C"); sites = rule.sites(same)
        self.assertTrue(rule.equivalent_sites(same, sites[0], sites[1]))

    def test_short_pi_cyclization_case_newly_restricted(self):
        for reagent, _ in REAGENTS: self.reject("C=CCCCCC=C", "6-membered intramolecular carbon capture", reagent)

    def test_radical_conditions_do_not_return_an_ionic_or_anti_markovnikov_product(self):
        for reagent, _ in REAGENTS:
            self.reject("C=CC", "Radical initiation", reagent, {"catalyst": "radical"})
            with self.assertRaisesRegex(service.ChemistryError, "matches both"):
                service.run_curated_reaction("hydrohalogenation-propene", "propene", reagent, {"catalyst": "radical"})

    def test_wrong_reagents_and_hf_do_not_produce_hx_addition(self):
        for reagent in ["hydrogen", "water", "hydroxide", "bromine", "ethanol", {"smiles": "F"}]:
            with self.subTest(reagent=reagent): self.assertFalse(self.options("C=CC", reagent)[1])
        self.reject("C=CC", "HF is outside", {"smiles": "F"})

    def test_incomplete_direction_and_unvalidated_ring_annotation_fail_closed(self):
        for a in ["C1/C=C/CCC1", "C1/C=C\\CCC1", "C/C=C"]:
            with self.subTest(a=a): self.reject(a, "directional C=C annotation")

    def test_invalid_electronic_stereo_disconnected_inputs(self):
        for a in ["bad-smiles", "C=C.O", "C=CCCC[O-]", "C=CCC[CH2]", "C=CC[13CH2]CC", "C=CC[C@H](C)CC |&1:3|"]:
            with self.subTest(a=a), self.assertRaises(service.ChemistryError): self.options(a)

    def test_size_limit_includes_actual_h_and_halogen(self):
        r = self.check("C=" + "C" * 25, ["CC(Br)" + "C" * 24])[0]
        self.assertEqual(Chem.AddHs(Chem.MolFromSmiles(r["productSmiles"])).GetNumAtoms(), 80)
        self.reject("C=" + "C" * 26, "exceed 80 explicit atoms")

    def test_no_name_formula_cid_lookup_decides_products(self):
        with patch.dict(service.REACTANTS, {}, clear=True):
            a, b = {"smiles": "CC=CCC", "name": "Not a preset", "cid": 1}, {"smiles": "I", "name": "Unrelated name"}
            rs = service.match_reactions(a, b, IONIC)["reactions"]
        self.assertEqual({r["productSmiles"] for r in rs if r["mechanism"] == "Hydrohalogenation"}, {canonical("CC(I)CCC"), canonical("CCC(I)CC")})

    def test_actual_reagent_not_a_cached_halogen_from_previous_match(self):
        for reagent, x in REAGENTS:
            a, rs, _ = self.options("C=CC", reagent)
            p = service.run_curated_reaction(rs[0]["id"], a, reagent, IONIC)["product"]
            self.assertEqual(p["smiles"], canonical(f"CC({x})C"))

    def test_reversed_slots_preserve_provenance_and_amounts(self):
        ref, rs, _ = self.options("CC=CCCC")
        reverse = [r for r in service.match_reactions("hydrogen-bromide", ref, IONIC)["reactions"] if r["mechanism"] == "Hydrohalogenation"]
        self.assertEqual([r["productSmiles"] for r in rs], [r["productSmiles"] for r in reverse])
        for r, other in zip(rs, reverse):
            self.assertEqual(r["compatibility"], other["compatibility"])
            d = service.reaction_diagram(r["id"], ref, "hydrogen-bromide", IONIC)
            back = service.reaction_diagram(other["id"], "hydrogen-bromide", ref, IONIC)
            self.assertEqual(d["changes"], back["changes"])
            self.assertAlmostEqual(other["stoichiometry"]["reactants"][0]["molarMass"], 80.912, places=6)

    def test_default_missing_medium_is_a_conditional_ionic_assumption(self):
        a, rs, _ = self.options("C=CC", conditions={})
        self.assertEqual(rs[0]["assessment"]["status"], "missing")
        self.assertTrue(rs[0]["assessment"]["canRun"])
        self.assertIn("absence of water, alcohol or peroxide is not established", rs[0]["assessment"]["note"])
        self.assertTrue(service.run_curated_reaction(rs[0]["id"], a, "hydrogen-bromide")["balanced"])

    def test_polar_aprotic_medium_differs_without_declaring_disfavor(self):
        a, rs, _ = self.options("C=CC", conditions={"solvent": "polar-aprotic"})
        self.assertEqual(rs[0]["assessment"]["status"], "reference-difference")
        self.assertNotEqual(rs[0]["reasoning"]["label"], "Unfavorable")
        self.assertTrue(service.run_curated_reaction(rs[0]["id"], a, "hydrogen-bromide", {"solvent": "polar-aprotic"})["balanced"])

    def test_water_alcohol_media_need_competing_capture_model_for_3d(self):
        for solvent in ["aqueous-protic", "ethanolic-protic"]:
            conditions = {"solvent": solvent}
            ref, rs, _ = self.options("C=CC", conditions=conditions)
            self.assertEqual(rs[0]["assessment"]["status"], "unevaluated")
            self.assertFalse(rs[0]["assessment"]["canRun"])
            with self.assertRaisesRegex(service.ChemistryError, "compete in carbocation capture"):
                service.run_curated_reaction(rs[0]["id"], ref, "hydrogen-bromide", conditions)

    def test_added_catalyst_is_not_required_or_automatically_compatible(self):
        for catalyst in ["acid", "metal", "lindlar", "osmium"]:
            conditions = {"catalyst": catalyst}
            ref, rs, _ = self.options("C=CC", conditions=conditions)
            self.assertEqual(rs[0]["assessment"]["status"], "unevaluated")
            with self.assertRaisesRegex(service.ChemistryError, "already supplies the acidic H"):
                service.run_curated_reaction(rs[0]["id"], ref, "hydrogen-bromide", conditions)

    def test_direct_condition_assessment_cannot_enable_radical_model(self):
        _, rs, _ = self.options("C=CC")
        r = rs[0]
        assessment = assess_conditions({"mechanism": "Hydrohalogenation", "profile": {}, "hxModel": r["hxModel"]}, {"catalyst": "radical"})
        self.assertEqual(assessment["status"], "unsupported-pathway")
        self.assertFalse(assessment["canRun"])

    def valid_edit(self, source="C=CC[C@H](C)CC", reagent="Br"):
        a, n = _species("a", {"name": "Source", "smiles": source}, 1)
        b, _ = _species("b", {"name": "HX", "smiles": reagent}, n)
        site = rule.sites(a["mol"])[0]
        product = engine.transform("Hydrohalogenation", [a, b], site)[0]
        return a["mol"], b["mol"], site, _combine([a, b]), product

    def test_invalid_site_or_capture_carbon_fails_closed(self):
        m, r = Chem.MolFromSmiles("C=CC"), Chem.MolFromSmiles("Br")
        for site in [(0, 1, 0), (0, 1, 2), (0, 0, 0), (1, 2, 1), (0, 1, True), (0, 999, 0)]:
            self.assertFalse(rule.assess(m, r, site)["eligible"])

    def test_reagent_contract_rejects_non_hx_graphs(self):
        a, _, site, _, _ = self.valid_edit()
        for smi in ["F", "BrBr", "O", "[Br-]", "[H+].[Br-]", "[2H]Br", "[Br]"]:
            with self.subTest(smi=smi), self.assertRaises(ValueError):
                b, _ = _species("b", {"name": "Not supported HX", "smiles": smi}, 100)
                rule.edit_contract(a, b["mol"], site)

    def test_exact_validator_rejects_spectator_bond_change(self):
        a, b, site, before, after = self.valid_edit()
        editor = Chem.RWMol(after)
        reactive = {frozenset(e["atomMaps"]) for e in rule.edit_contract(a, b, site)}
        bond = next(v for v in editor.GetBonds() if frozenset((v.GetBeginAtom().GetAtomMapNum(), v.GetEndAtom().GetAtomMapNum())) not in reactive and v.GetBeginAtom().GetAtomicNum() == v.GetEndAtom().GetAtomicNum() == 6)
        editor.RemoveBond(bond.GetBeginAtomIdx(), bond.GetEndAtomIdx())
        with self.assertRaisesRegex(ValueError, "unaffected bond"):
            rule.validate(before, editor.GetMol(), a, b, site)

    def test_exact_validator_rejects_remote_inversion_or_erasure(self):
        for erase in [False, True]:
            a, b, site, before, after = self.valid_edit()
            center = next(v for v in after.GetAtoms() if v.GetChiralTag() != Chem.ChiralType.CHI_UNSPECIFIED)
            if erase: center.SetChiralTag(Chem.ChiralType.CHI_UNSPECIFIED)
            else: center.InvertChirality()
            with self.assertRaisesRegex(ValueError, "configuration|stereo"):
                rule.validate(before, after, a, b, site)

    def test_exact_validator_rejects_invented_new_configuration(self):
        a, b, site, before, after = self.valid_edit("C=CCC")
        target = rule.participants(a, b, site)["halogenCarbon"]
        next(v for v in after.GetAtoms() if v.GetAtomMapNum() == target).SetChiralTag(Chem.ChiralType.CHI_TETRAHEDRAL_CCW)
        with self.assertRaisesRegex(ValueError, "invented|configuration|introduced|unspecified"):
            rule.validate(before, after, a, b, site)

    def test_exact_validator_rejects_halogen_identity_charge_or_wrong_h_provenance(self):
        for tamper in ["element", "charge", "hydrogen-map"]:
            a, b, site, before, after = self.valid_edit()
            p = rule.participants(a, b, site)
            atom = next(v for v in after.GetAtoms() if v.GetAtomMapNum() == p["halogen"])
            if tamper == "element": atom.SetAtomicNum(17)
            elif tamper == "charge": atom.SetFormalCharge(-1)
            else:
                # Swapping equivalent H labels at the same carbon is not a
                # provenance defect. Move the incoming label to a different
                # carbon so the exact mapped bond contract must reject it.
                original_h = next(v for v in after.GetAtoms() if v.GetAtomicNum() == 1
                                  and v.GetAtomMapNum() != p["hydrogen"]
                                  and v.GetNeighbors()[0].GetAtomMapNum() != p["hydrogenCarbon"])
                incoming = next(v for v in after.GetAtoms() if v.GetAtomMapNum() == p["hydrogen"])
                old_map = original_h.GetAtomMapNum(); original_h.SetAtomMapNum(p["hydrogen"]); incoming.SetAtomMapNum(old_map)
            with self.subTest(tamper=tamper), self.assertRaises(ValueError): rule.validate(before, after, a, b, site)

    def test_source_map_numbers_do_not_decide_symmetry_or_change_namespace(self):
        ref = {"smiles": "[CH3:42][CH:3]=[CH:25][CH3:11]"}
        rs = [r for r in service.match_reactions(ref, "hydrogen-bromide", IONIC)["reactions"] if r["mechanism"] == "Hydrohalogenation"]
        self.assertEqual(len(rs), 1)
        self.check_option(ref, rs[0], "CC(Br)CC", "hydrogen-bromide", IONIC)

    def test_no_new_ionic_mechanism_steps_or_stereochemistry_are_advertised(self):
        ref, rs, _ = self.options("C=CC")
        self.assertEqual(rs[0]["information"]["capabilities"]["mappedMechanism"], "unsupported")
        self.assertIsNone(service.reaction_diagram(rs[0]["id"], ref, "hydrogen-bromide", IONIC)["mechanism"])

    def test_hydration_and_halogenation_keep_their_independent_models(self):
        hydration = service.match_reactions({"smiles": "C=CCCCCCCCO"}, "water", {"catalyst": "acid"})
        self.assertTrue(any(r["mechanism"] == "Hydration" for r in hydration["reactions"]))
        self.assertFalse(self.options("C=CCCCCCCCO")[1])
        # Phase 3C independently adds Br2 anti outcomes, not HX permissions.
        bromination = service.match_reactions({"smiles": "CC/C=C/CC"}, "bromine", {"solvent": "dry"})["reactions"]
        self.assertEqual({r["productSmiles"] for r in bromination}, {canonical("CC[C@H](Br)[C@H](Br)CC")})
        self.assertEqual({r["productSmiles"] for r in service.match_reactions({"smiles": "C=CC"}, "bromine")["reactions"] if r["mechanism"] == "Bromination"},
                         {canonical("C[C@H](Br)CBr"), canonical("C[C@@H](Br)CBr")})

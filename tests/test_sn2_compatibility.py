"""Independent SN2 products, physical configurations and public mechanism checks."""
import unittest
from unittest.mock import patch
from rdkit import Chem
from rdkit.Chem import Descriptors, rdMolDescriptors, rdCIPLabeler
from server import chemistry_server as service, sn2_rule as rule
from server import reaction_engine as engine, reaction_compatibility as compatibility
from server.reaction_diagrams import _species, _combine, _identity

MEDIUM = {"solvent": "polar-aprotic"}


def canonical(smiles):
    return Chem.MolToSmiles(Chem.MolFromSmiles(smiles))


def bonds(mol):
    return {tuple(sorted((b.GetBeginAtom().GetAtomMapNum(), b.GetEndAtom().GetAtomMapNum()))): b.GetBondTypeAsDouble() for b in mol.GetBonds()}


class SN2CompatibilityTests(unittest.TestCase):
    def options(self, smiles, reagent="hydroxide", conditions=MEDIUM):
        ref = {"name": "Independent SN2 input", "smiles": smiles}
        result = service.match_reactions(ref, reagent, conditions)
        return ref, [r for r in result["reactions"] if r["mechanism"] == "SN2"], result

    def check_option(self, ref, r, expected, reagent="hydroxide"):
        self.assertEqual(r["productSmiles"], canonical(expected))
        expected_mol = Chem.MolFromSmiles(expected)
        self.assertEqual(r["productFormula"], rdMolDescriptors.CalcMolFormula(expected_mol))
        self.assertTrue(r["stoichiometry"]["balanced"])
        self.assertEqual([i["coefficient"] for i in r["stoichiometry"]["reactants"]], [1, 1])
        self.assertEqual(r["stoichiometry"]["product"]["coefficient"], 1)
        self.assertAlmostEqual(r["stoichiometry"]["product"]["molarMass"], Descriptors.MolWt(expected_mol), places=6)
        d = service.reaction_diagram(r["id"], ref, reagent, MEDIUM)
        self.assertEqual(d["products"][0]["smiles"], canonical(expected))
        self.assertIn("<svg", d["svg"])
        self.assertTrue(d["highlightsAvailable"])
        before_rows = [a for a in d["atoms"] if a["side"] == "reactants"]
        after_rows = [a for a in d["atoms"] if a["side"] == "products"]
        before = {a["mapId"]: (a["element"], a["formalCharge"]) for a in before_rows}
        after = {a["mapId"]: (a["element"], a["formalCharge"]) for a in after_rows}
        self.assertEqual((len(before), len(after)), (len(before_rows), len(after_rows)))
        self.assertEqual({m: v[0] for m, v in before.items()}, {m: v[0] for m, v in after.items()})
        self.assertEqual(sum(v[1] for v in before.values()), -1)
        self.assertEqual(sum(v[1] for v in after.values()), -1)
        report = r["compatibility"]
        charges = report["chargeChanges"]
        for m, (_, q) in before.items():
            self.assertEqual(after[m][1], next((c["after"] for c in charges if c["atomMap"] == m), q))
        self.assertEqual(len(d["atomMap"]), len(before))
        self.assertEqual(len(d["bondsBroken"]), 1)
        self.assertEqual(len(d["bondsFormed"]), 1)
        self.assertEqual(d["bondOrderChanges"], [])
        substitution = report["invertedSubstitutions"][0]
        center, leaving, incoming = (substitution[k] for k in ("center", "leaving", "incoming"))
        self.assertEqual(set(d["bondsBroken"][0]["atomMaps"]), {center, leaving})
        self.assertEqual(set(d["bondsFormed"][0]["atomMaps"]), {center, incoming})
        self.assertEqual((before[incoming], after[incoming]), (("O", -1), ("O", 0)))
        self.assertEqual((before[leaving][1], after[leaving][1]), (0, -1))
        self.assertEqual(d["products"][1]["smiles"], f"[{before[leaving][0]}-]")
        self.assertTrue(report["eligible"])
        self.assertEqual(report["substrateSiteMaps"], r["site"]["atomMaps"])
        self.assertEqual(set(report["reactiveAtomMaps"]), {center, leaving, incoming})
        self.assertEqual({(tuple(sorted(e["atomMaps"])), e["before"], e["after"]) for e in report["editContract"]},
                         {(tuple(sorted(e["atomMaps"])), e["before"], e["after"]) for e in d["changes"]})
        self.assertEqual(set(report["validation"].values()), {"verified"})
        reactive = [g for g in report["groups"] if g["disposition"] == "reactive"]
        self.assertEqual(len(reactive), 1)
        self.assertEqual(set(reactive[0]["atomMaps"]), {center, leaving})
        self.assertEqual(reactive[0]["relation"], "reactive")
        mechanism = d["mechanism"]
        self.assertEqual(mechanism["type"], "SN2")
        self.assertEqual(mechanism["roles"], {"electrophilic-carbon": center, "leaving-group": leaving, "nucleophile": incoming})
        self.assertEqual(len(mechanism["steps"]), 1)
        step = mechanism["steps"][0]
        self.assertTrue(step["concerted"])
        self.assertIsNone(step["intermediate"])
        self.assertEqual(step["protonTransfers"], [])
        self.assertEqual(len(step["electronMoves"]), 2)
        attack, departure = step["electronMoves"]
        self.assertEqual((attack["source"], attack["destination"]), ({"type": "lone-pair", "atomMaps": [incoming]}, {"type": "atom", "atomMaps": [center]}))
        self.assertEqual((departure["source"], departure["destination"]), ({"type": "bond", "atomMaps": [center, leaving]}, {"type": "atom", "atomMaps": [leaving]}))
        params = Chem.SmilesParserParams(); params.removeHs = False
        final_state = Chem.MolFromSmiles(step["state"]["mappedSmiles"], params)
        final_main = next(f for f in Chem.GetMolFrags(final_state, asMols=True) if any(a.GetAtomMapNum() == center for a in f.GetAtoms()))
        self.assertEqual(_identity(final_main), canonical(expected))
        self.assertEqual(mechanism["energyProfile"]["intermediates"], 0)
        self.assertIsNone(mechanism["energyProfile"]["activationEnergies"])
        p = service.run_curated_reaction(r["id"], ref, reagent, MEDIUM)["product"]
        self.assertEqual(p["smiles"], canonical(expected))
        self.assertEqual(p["representation"], "3d")
        main_rows = [a for a in after_rows if a["speciesIndex"] == 0]
        self.assertEqual([(a["atomIndex"], a["mapId"], a["element"]) for a in main_rows],
                         [(a["index"], a["mapId"], a["element"]) for a in p["atomLinks"]])
        self.assertNotIn(leaving, [a["mapId"] for a in p["atomLinks"]])
        self.assertIn(incoming, [a["mapId"] for a in p["atomLinks"]])
        shape = Chem.MolFromMolBlock(p["molfile"], removeHs=False)
        if any(i.specified == Chem.StereoSpecified.Unspecified for i in Chem.FindPotentialStereo(expected_mol)):
            self.assertEqual(Chem.MolToSmiles(Chem.MolFromSmiles(_identity(shape)), isomericSmiles=False), Chem.MolToSmiles(expected_mol, isomericSmiles=False))
        else:
            self.assertEqual(_identity(shape), canonical(expected))
        for atom in shape.GetAtoms(): atom.SetAtomMapNum(0)
        Chem.AssignStereochemistry(shape, cleanIt=True, force=True)
        rdCIPLabeler.AssignCIPLabels(shape)
        links = {a["mapId"]: a["index"] for a in p["atomLinks"]}
        for c in r["information"]["stereochemistry"]["product"]["chiralCenters"]:
            if c["specified"]:
                atom = shape.GetAtomWithIdx(links[c["atomMap"]])
                self.assertTrue(atom.HasProp("_CIPCode"))
                self.assertEqual(atom.GetProp("_CIPCode"), c["assignment"])
        return d, p

    def check(self, substrate, product):
        ref, options, _ = self.options(substrate)
        self.assertEqual(len(options), 1)
        self.check_option(ref, options[0], product)
        return options[0]

    def test_methyl_long_primary_and_actual_leaving_groups(self):
        for a, p in [("CCl", "CO"), ("CBr", "CO"), ("CI", "CO"), ("CCCCCCCCCCCCBr", "CCCCCCCCCCCCO"),
                     ("CCCCCCCl", "CCCCCCO"), ("CCCCCCCCCI", "CCCCCCCCCO")]:
            with self.subTest(substrate=a): self.check(a, p)

    def test_branched_secondary_and_exocyclic_regressions(self):
        for a, p in [("CCC(C)CBr", "CCC(C)CO"), ("CC(C)CCBr", "CC(C)CCO"),
                     ("CCC(Br)CC", "CCC(O)CC"), ("CCCC(Cl)CC", "CCCC(O)CC"), ("BrCC1CCCCC1", "OCC1CCCCC1")]:
            with self.subTest(substrate=a): self.check(a, p)

    def test_benzylic_and_methoxy_aromatic_compatibility(self):
        for a, p in [("BrCc1ccccc1", "OCc1ccccc1"), ("CC(Br)c1ccccc1", "CC(O)c1ccccc1"),
                     ("COc1ccc(CBr)cc1", "COc1ccc(CO)cc1")]:
            with self.subTest(substrate=a):
                r = self.check(a, p)
                self.assertEqual(r["reasoning"]["label"], "Possible")

    def test_remote_ethers_are_screened_not_assumed_inert(self):
        for a, p in [("COCCCBr", "COCCCO"), ("CCOCCCCCl", "CCOCCCCO"),
                     ("BrCCCCOC1CCCC1", "OCCCCOC1CCCC1"), ("BrCCCC1CCCO1", "OCCCC1CCCO1")]:
            with self.subTest(substrate=a):
                r = self.check(a, p)
                self.assertTrue(any(g["type"] == "ether" and g["disposition"] == "preserved" for g in r["compatibility"]["groups"]))
                self.assertEqual(r["reasoning"]["label"], "Possible")

    def test_remote_alcohols_and_combined_ether_alcohol_structures(self):
        for a, p in [("OCCCCCCCBr", "OCCCCCCCO"), ("CC(O)CCCCCCCBr", "CC(O)CCCCCCCO"),
                     ("OCCCCOCCCCBr", "OCCCCOCCCCO")]:
            with self.subTest(substrate=a):
                r = self.check(a, p)
                self.assertTrue(any(g["type"] == "alcohol" and g["disposition"] == "preserved" for g in r["compatibility"]["groups"]))
                self.assertIn("proton equilibria", " ".join(r["information"]["limitations"]))

    def test_local_inversion_both_enantiomers_and_source_atom_orders(self):
        for a, p in [("CC[C@H](Br)CCC", "CC[C@@H](O)CCC"), ("CC[C@@H](Br)CCC", "CC[C@H](O)CCC"),
                     ("Br[C@@H](C)CC", "O[C@H](C)CC"), ("C[C@H](Cl)CC", "C[C@@H](O)CC")]:
            with self.subTest(substrate=a): self.check(a, p)

    def test_distant_centers_retain_physical_configuration(self):
        for a, p in [("CC[C@H](C)CCCBr", "CC[C@H](C)CCCO"), ("CC[C@@H](C)CCCBr", "CC[C@@H](C)CCCO"),
                     ("CC[C@H](C)COCCCCBr", "CC[C@H](C)COCCCCO")]:
            with self.subTest(substrate=a): self.check(a, p)

    def test_simultaneous_local_inversion_and_distant_retention(self):
        for a, p in [("CC[C@H](C)CC[C@@H](Br)C", "CC[C@H](C)CC[C@H](O)C"),
                     ("CC[C@@H](C)CC[C@H](Br)C", "CC[C@@H](C)CC[C@@H](O)C"),
                     ("CC[C@H](C)COCCC[C@@H](Br)C", "CC[C@H](C)COCCC[C@H](O)C")]:
            r = self.check(a, p)
            info = r["information"]["stereochemistry"]
            self.assertEqual(len(info["reactant"]["chiralCenters"]), 2)
            self.assertEqual(len(info["product"]["chiralCenters"]), 2)

    def test_remote_cip_letter_changes_without_inversion(self):
        for tag, before, after in [("@", "R", "S"), ("@@", "S", "R")]:
            r = self.check(f"C[C{tag}H](CCOC)CCBr", f"C[C{tag}H](CCOC)CCO")
            info = r["information"]["stereochemistry"]
            self.assertEqual(info["reactant"]["chiralCenters"][0]["assignment"], before)
            self.assertEqual(info["product"]["chiralCenters"][0]["assignment"], after)

    def test_nonreactive_center_losing_stereogenicity_fails_closed(self):
        _, options, result = self.options("C[C@H](CCCCCO)CCCCCBr")
        self.assertFalse(options)
        self.assertIn("no longer stereogenic", " ".join(result["unsupportedReasons"]))
        self.assertIn("not silently", " ".join(result["unsupportedReasons"]))

    def test_unsigned_reacting_and_remote_centers_stay_unsigned(self):
        for a, p in [("CCC(Br)C", "CCC(O)C"), ("CCC(C)CCCBr", "CCC(C)CCCO")]:
            r = self.check(a, p)
            self.assertNotIn("@", r["productSmiles"])
            self.assertTrue(all(not c["specified"] and c["assignment"] is None for c in r["information"]["stereochemistry"]["product"]["chiralCenters"]))

    def test_multiple_sites_remain_individually_mapped(self):
        for a, expected in [("BrCCCCBr", ["OCCCCBr", "BrCCCCO"]),
                            ("ClCCCCCBr", ["OCCCCCBr", "ClCCCCCO"]),
                            ("COCCC(Br)CCCCCCl", ["COCCC(O)CCCCCCl", "COCCC(Br)CCCCCO"])]:
            ref, options, _ = self.options(a)
            self.assertEqual(len(options), 2)
            self.assertEqual(len({r["id"] for r in options}), 2)
            self.assertEqual(len({tuple(r["site"]["atomMaps"]) for r in options}), 2)
            self.assertEqual(sorted(r["productSmiles"] for r in options), sorted(canonical(p) for p in expected))
            for r in options:
                self.check_option(ref, r, r["productSmiles"])
                self.assertTrue(any(g["disposition"] == "alternative-site" for g in r["compatibility"]["groups"]))

    def test_multiple_specified_sites_invert_only_the_selected_center(self):
        a = "C[C@H](Br)CCC[C@@H](Cl)C"
        expected = ["C[C@@H](O)CCC[C@@H](Cl)C", "C[C@H](Br)CCC[C@H](O)C"]
        ref, options, _ = self.options(a)
        self.assertEqual(len(options), 2)
        self.assertEqual(sorted(r["productSmiles"] for r in options), sorted(canonical(p) for p in expected))
        for r in options: self.check_option(ref, r, r["productSmiles"])

    def test_tertiary_hindered_ring_bound_and_allylic_cases_stay_excluded(self):
        for a, why in [("CC(C)(C)Br", "tertiary"), ("CC(C)(C)CBr", "Neopentyl"),
                       ("BrC1CCCCC1", "Ring-bound"), ("C=CCBr", "Allylic"),
                       ("OCCCCCCC(Br)(C)C", "tertiary")]:
            _, options, result = self.options(a)
            self.assertFalse(options)
            self.assertIn(why, " ".join(result["unsupportedReasons"]))
        for a in ("C=CBr", "Brc1ccccc1", "CCCCF"):
            self.assertFalse(self.options(a)[1])

    def test_halohydrin_and_small_ring_closure_competition(self):
        for a, size in [("OCCBr", 3), ("OCCCBr", 4), ("OCCCCBr", 5), ("OCCCCCBr", 6)]:
            _, options, result = self.options(a)
            self.assertFalse(options)
            self.assertIn(f"{size}-membered intramolecular", " ".join(result["unsupportedReasons"]))

    def test_nearby_ethers_and_unvalidated_groups_rejected_precisely(self):
        rows = [("COCCBr", "near the electrophile"), ("COCBr", "directly on the electrophilic"),
                ("FCCCCBr", "F at substrate atom"), ("NCCCCBr", "N at substrate atom"), ("SCCCCBr", "S at substrate atom"),
                ("CC(=O)OCCCCBr", "ester"), ("O=C(O)CCCCBr", "carboxylic acid"), ("CC(=O)CCCCBr", "ketone"),
                ("O=CCCCBr", "aldehyde"), ("OCCCC(=O)NCCCCBr", "amide"), ("OOCCCCBr", "peroxide"),
                ("Oc1ccc(CBr)cc1", "phenol"), ("C#CCCCBr", "alkyne"), ("C/C=C/CCCBr", "alkene"),
                ("COC(OC)CCCCBr", "Acetal/ketal"), ("Brc1ccc(CCCCBr)cc1", "non-alkyl halide"),
                ("BrCCCCc1ccncc1", "Heteroaromatic")]
        for a, why in rows:
            with self.subTest(substrate=a):
                _, options, result = self.options(a)
                self.assertFalse(options)
                self.assertIn(why, " ".join(result["unsupportedReasons"]))

    def test_unsupported_other_halide_sites_and_geminal_cases(self):
        for a in ("BrCCCC(Br)(C)C", "ClC(Br)C", "C[C@](Cl)(Br)I"):
            self.assertFalse(self.options(a)[1])

    def test_invalid_electronic_states_and_enhanced_stereo_do_not_disappear(self):
        for a in ("not-smiles", "CC(Br)(C)(C)C", "BrCCC[O-]", "BrCC[CH2]", "BrCC[13CH2]C", "CCBr.O",
                  "CC[C@H](Br)CCC |&1:2|", "CC[C@H](Br)CCC |o1:2|"):
            with self.subTest(substrate=a), self.assertRaises(service.ChemistryError): self.options(a)
        for reagent in ("sodium-hydroxide", {"smiles": "[K+].[OH-]"}):
            with self.assertRaises(service.ChemistryError): self.options("CC[C@H](Br)CCC |&1:2|", reagent)
        with self.assertRaises(service.ChemistryError): self.options("CCBr", {"smiles": "C" * 1025})

    def test_ring_and_size_limits_remain(self):
        _, options, result = self.options("BrCCCC1CC1")
        self.assertFalse(options)
        self.assertIn("3-membered ring", " ".join(result["unsupportedReasons"]))
        _, options, _ = self.options("C" * 25 + "Br")
        self.assertEqual(len(options), 1)
        self.assertEqual(Chem.AddHs(Chem.MolFromSmiles(options[0]["productSmiles"])).GetNumAtoms(), 78)
        _, options, result = self.options("C" * 26 + "Br")
        self.assertFalse(options)
        self.assertIn("exceed 80 explicit atoms", " ".join(result["unsupportedReasons"]))

    def test_actual_hydroxide_salts_and_reverse_source_provenance(self):
        a = {"name": "Source map", "smiles": "[CH3:77][CH2:5][Br:19]"}
        for reagent in ("hydroxide", "sodium-hydroxide", {"smiles": "[K+].[OH-]"}):
            f = next(r for r in service.match_reactions(a, reagent, MEDIUM)["reactions"] if r["mechanism"] == "SN2")
            reverse = next(r for r in service.match_reactions(reagent, a, MEDIUM)["reactions"] if r["mechanism"] == "SN2")
            self.assertEqual(f["productSmiles"], canonical("CCO"))
            df = service.reaction_diagram(f["id"], a, reagent, MEDIUM)
            dr = service.reaction_diagram(reverse["id"], reagent, a, MEDIUM)
            self.assertEqual(df["svg"], dr["svg"])
            formula, mass = ("OH⁻", 17.007) if reagent == "hydroxide" else ("NaOH", 39.997) if reagent == "sodium-hydroxide" else ("KOH", 56.105)
            self.assertEqual({v["formula"]: v["inputSlot"] for v in reverse["stoichiometry"]["reactants"]}, {"C2H5Br": 1, formula: 0})
            self.assertAlmostEqual(next(v["molarMass"] for v in reverse["stoichiometry"]["reactants"] if v["inputSlot"] == 0), mass, places=6)
        item, _ = _species("source", a, 1)
        self.assertEqual({a.GetIntProp("sourceAtomMap") for a in item["mol"].GetAtoms() if a.HasProp("sourceAtomMap")}, {77, 5, 19})

    def test_new_nucleophiles_and_false_identities_are_not_enabled(self):
        for reagent in ("water", {"smiles": "[Na+].[O-]C"}, {"smiles": "[Na+].[I-]"}, {"smiles": "O", "name": "Hydroxide"}):
            if isinstance(reagent, dict) and "." in reagent["smiles"]:
                with self.assertRaises(service.ChemistryError): self.options("CCCCBr", reagent)
            else: self.assertFalse(self.options("CCCCBr", reagent)[1])
        with patch.dict(service.REACTIONS, {}, clear=True):
            result = service.match_reactions({"name": "False benzene", "cid": 241, "formula": "C6H6", "smiles": "COCCCBr"}, {"name": "Actual OH", "smiles": "[OH-]"}, MEDIUM)
            self.assertEqual(next(r for r in result["reactions"] if r["mechanism"] == "SN2")["productSmiles"], canonical("COCCCO"))

    def test_secondary_and_conditions_never_claim_efficiency(self):
        for a in ("CCC(Br)CC", "COCCCBr", "OCCCCCCCBr"):
            r = self.check(a, a.replace("Br", "O"))
            self.assertEqual(r["reasoning"]["label"], "Possible")
            self.assertIn("efficiency", r["conditions"])
        for cond, state in [({}, "incomplete"), ({"solvent": "aqueous-protic"}, "alternative"), ({"solvent": "polar-aprotic", "catalyst": "acid"}, "incomplete")]:
            _, options, _ = self.options("CCCBr", conditions=cond)
            self.assertEqual(options[0]["assessment"]["state"], state)
            self.assertNotEqual(options[0]["reasoning"]["label"], "Strong match")

    def valid_edit(self, smiles="CC[C@H](C)CC[C@@H](Br)C"):
        a, n = _species("a", {"name": "Mapped SN2", "smiles": smiles}, 1)
        b, _ = _species("b", {"name": "Actual OH", "smiles": "[OH-]"}, n)
        site = rule.sites(a["mol"])[0]
        before = _combine([a, b])
        after = _combine([{"mol": m} for m in engine.transform("SN2", [a, b], site)])
        return a, b, site, before, after

    def test_exact_edit_contract_and_atom_reordering(self):
        a, b, site, before, after = self.valid_edit()
        edits = rule.edit_contract(a["mol"], b["mol"], site)
        initial, final = bonds(before), bonds(after)
        self.assertEqual({p for p in initial.keys() | final.keys() if initial.get(p) != final.get(p)}, {tuple(sorted(e["atomMaps"])) for e in edits})
        self.assertEqual(len(edits), 2)
        rule.validate(before, after, a["mol"], b["mol"], site)
        rule.validate(before, Chem.RenumberAtoms(after, list(reversed(range(after.GetNumAtoms())))), a["mol"], b["mol"], site)
        with self.assertRaises(ValueError): compatibility.validate_edit_contract(before, after, edits, charge_changes=rule.charge_contract(a["mol"], b["mol"], site))

    def test_incorrect_inversion_remote_changes_and_bad_chemistry_fail(self):
        a, b, site, before, after = self.valid_edit()
        spec = rule.substitution(a["mol"], b["mol"], site)
        for mutation in ("retain-reacting", "erase-reacting", "invert-remote", "erase-remote", "atom", "charge", "map", "unselected-bond"):
            changed = Chem.Mol(after)
            reacting = next(x for x in changed.GetAtoms() if x.GetAtomMapNum() == spec["center"])
            remote = next(x for x in changed.GetAtoms() if x.GetChiralTag() != Chem.ChiralType.CHI_UNSPECIFIED and x.GetAtomMapNum() != spec["center"])
            if mutation == "retain-reacting": reacting.InvertChirality()
            elif mutation == "erase-reacting": reacting.SetChiralTag(Chem.ChiralType.CHI_UNSPECIFIED)
            elif mutation == "invert-remote": remote.InvertChirality()
            elif mutation == "erase-remote": remote.SetChiralTag(Chem.ChiralType.CHI_UNSPECIFIED)
            elif mutation == "atom": changed.GetAtomWithIdx(0).SetAtomicNum(7)
            elif mutation == "charge": changed.GetAtomWithIdx(0).SetFormalCharge(1)
            elif mutation == "map": changed.GetAtomWithIdx(0).SetAtomMapNum(0)
            else: next(b for b in changed.GetBonds() if all(x.GetSymbol() == "C" for x in (b.GetBeginAtom(), b.GetEndAtom()))).SetBondType(Chem.BondType.DOUBLE)
            with self.subTest(mutation=mutation), self.assertRaises(ValueError): rule.validate(before, changed, a["mol"], b["mol"], site)

    def test_no_invented_specified_stereo_at_unsigned_center(self):
        a, b, site, before, after = self.valid_edit("CCC(Br)C")
        changed = Chem.Mol(after)
        center_map = a["mol"].GetAtomWithIdx(site[0]).GetAtomMapNum()
        next(x for x in changed.GetAtoms() if x.GetAtomMapNum() == center_map).SetChiralTag(Chem.ChiralType.CHI_TETRAHEDRAL_CW)
        with self.assertRaises(ValueError): rule.validate(before, changed, a["mol"], b["mol"], site)

    def test_inversion_and_charge_permissions_cannot_move_to_other_sites(self):
        a, b, site, before, after = self.valid_edit()
        spec, charges = rule.substitution(a["mol"], b["mol"], site), rule.charge_contract(a["mol"], b["mol"], site)
        edits = rule.edit_contract(a["mol"], b["mol"], site)
        remote = next(x.GetAtomMapNum() for x in a["mol"].GetAtoms() if x.GetChiralTag() != Chem.ChiralType.CHI_UNSPECIFIED and x.GetIdx() != site[0])
        for specs in ([spec, spec], [{**spec, "center": remote}], [{**spec, "incoming": spec["leaving"]}], [{**spec, "center": True}]):
            with self.assertRaises(ValueError): compatibility.validate_edit_contract(before, after, edits, charge_changes=charges, inverted_substitutions=specs)
        for cs in ([charges[0]], [*charges, charges[0]], [{**charges[0], "before": 1}, charges[1]]):
            with self.assertRaises(ValueError): compatibility.validate_edit_contract(before, after, edits, charge_changes=cs, inverted_substitutions=[spec])

    def test_validation_failures_never_become_public_options(self):
        for target in ("server.reaction_compatibility.validate_edit_contract", "server.stereochemistry.validate_retained_stereo"):
            with patch(target, side_effect=ValueError("Independent SN2 contract failure")):
                _, options, result = self.options("COCCCBr")
                self.assertFalse(options)
                self.assertIn("Independent SN2 contract failure", " ".join(result["unsupportedReasons"]))
        with patch("server.reaction_engine.invert_sn2", return_value=False):
            self.assertFalse(self.options("CC[C@H](Br)CCC")[1])

    def test_mechanism_cannot_retain_configuration_when_net_inverts(self):
        a, options, _ = self.options("CC[C@H](Br)CCC")
        self.assertTrue(options)
        with patch("server.reaction_mechanisms.invert_sn2", return_value=False), self.assertRaises((service.ChemistryError, ValueError)):
            service.reaction_diagram(options[0]["id"], a, "hydroxide", MEDIUM)

    def test_unknown_groups_wrong_sites_and_reagents_fail_closed(self):
        mol = Chem.MolFromSmiles("CCBr")
        self.assertEqual(rule.group_check(mol, (1, 2), {"type": "unknown", "atomIndices": [0]})[0], "rejected")
        for invalid in ((), (0, 0), (0, 999), (True, 1), (0, 1)):
            self.assertFalse(rule.assess(mol, invalid)["eligible"])
        wrong, _ = _species("wrong", {"name": "Water", "smiles": "O"}, 100)
        with self.assertRaises(ValueError): rule.nucleophile(wrong["mol"])

    def test_sn1_e1_do_not_inherit_policy_and_e2_uses_its_own_increment(self):
        for a, reagent in [("COCCCBr", "hydroxide"), ("COCCCC(Br)(C)C", "water"), ("OCCCCCCCBr", "hydroxide")]:
            result = service.match_reactions({"smiles": a}, reagent)
            self.assertFalse(any(r["mechanism"] in {"SN1", "E1"} for r in result["reactions"]))
            for r in result["reactions"]:
                if r["mechanism"] == "E2":
                    self.assertEqual(r["compatibility"]["policy"], "hydroxide E2 elimination")
                    self.assertEqual(len(r["compatibility"]["editContract"]), 4)
        self.assertTrue(any(r["mechanism"] == "E2" for r in service.match_reactions({"smiles": "CCC(Br)C"}, "hydroxide")["reactions"]))
        self.assertTrue(any(r["mechanism"] == "SN1" for r in service.match_reactions({"smiles": "CC(C)(C)Cl"}, "water")["reactions"]))

    def test_prior_ester_and_reduction_oxidation_consumers_still_work(self):
        for a, reagent, mechanism in [("C=CC[C@H](C)CC", "hydrogen", "Hydrogenation"), ("CC[C@H](C)CC=O", "hydrogen", "Carbonyl hydrogenation"),
                                      ("CC[C@H](C)CCO", "sodium-hypochlorite", "Alcohol oxidation"),
                                      ("O=C1OCCC1", "water", "Ester hydrolysis"), ("CC(=O)Oc1ccccc1", "hydroxide", "Ester saponification")]:
            self.assertTrue(any(r["mechanism"] == mechanism for r in service.match_reactions({"smiles": a}, reagent)["reactions"]))

    def test_authenticated_public_http_match_diagram_and_run(self):
        from server.production_app import create_app
        origin = "https://sn2-increment.example.test"
        app = create_app({"TRIAL_PASSWORD": "SN2-synthetic-test-password", "SESSION_SECRET": "5a793bc832adc647a5f382190dead01d19f58f6fa0c9246eb8b2b31f0f419b60",
                          "PUBLIC_ORIGIN": origin, "FRAME_ANCESTORS": "https://site.example.test", "DIST_DIR": "/private/tmp/sn2-no-static-needed", "TESTING": True}, chemistry_backend=service)
        client = app.test_client()
        self.assertEqual(client.post("/login", base_url=origin, headers={"Origin": origin}, data={"password": "SN2-synthetic-test-password"}).status_code, 303)
        for a, expected in [("COCCCBr", "COCCCO"), ("CC[C@H](C)CC[C@@H](Br)C", "CC[C@H](C)CC[C@H](O)C")]:
            body = {"reactantA": {"smiles": a}, "reactantB": "hydroxide", "conditions": MEDIUM}
            response = client.post("/api/reactions/match", base_url=origin, headers={"Origin": origin}, json=body)
            self.assertEqual(response.status_code, 200)
            r = next(r for r in response.get_json()["reactions"] if r["mechanism"] == "SN2")
            self.assertEqual(r["productSmiles"], canonical(expected))
            body["reactionId"] = r["id"]
            d = client.post("/api/reactions/diagram", base_url=origin, headers={"Origin": origin}, json=body)
            p = client.post("/api/reactions/run", base_url=origin, headers={"Origin": origin}, json=body)
            self.assertEqual((d.status_code, p.status_code), (200, 200))
            self.assertEqual(d.get_json()["products"][0]["smiles"], p.get_json()["product"]["smiles"])
            self.assertEqual(d.get_json()["mechanism"]["type"], "SN2")
        response = client.post("/api/reactions/match", base_url=origin, headers={"Origin": origin}, json={"reactantA": {"smiles": "OCCBr"}, "reactantB": "hydroxide", "conditions": MEDIUM})
        self.assertFalse(any(r["mechanism"] == "SN2" for r in response.get_json()["reactions"]))
        self.assertIn("intramolecular", " ".join(response.get_json()["unsupportedReasons"]))


if __name__ == "__main__": unittest.main()

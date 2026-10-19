"""Independent oxidation expectations through match -> diagram -> run."""
import unittest
from unittest.mock import patch
from rdkit import Chem
from rdkit.Chem import Descriptors, rdMolDescriptors, rdCIPLabeler
from server import chemistry_server as service, alcohol_oxidation_rule as rule
from server import reaction_engine as engine, reaction_compatibility as compatibility
from server.reaction_diagrams import _species, _combine, _identity

MEDIUM = {"solvent": "aqueous-protic", "oxidationStage": "first"}
SECONDARY_PROFILE = {**MEDIUM,"temperature":"ambient","catalyst":"none","secondaryOxidationProfile":"naocl-acetic-ketone-v1"}


def canonical(smiles):
    return Chem.MolToSmiles(Chem.MolFromSmiles(smiles))


def bonds(mol):
    return {tuple(sorted((b.GetBeginAtom().GetAtomMapNum(), b.GetEndAtom().GetAtomMapNum()))): b.GetBondTypeAsDouble() for b in mol.GetBonds()}


class AlcoholOxidationCompatibilityTests(unittest.TestCase):
    def options(self, smiles, reagent="sodium-hypochlorite", conditions=MEDIUM):
        ref = {"name": "Independent alcohol input", "smiles": smiles}
        result = service.match_reactions(ref, reagent, conditions)
        return ref, [r for r in result["reactions"] if r["mechanism"] == "Alcohol oxidation"], result

    def check_option(self, ref, r, expected, reagent="sodium-hypochlorite"):
        self.assertEqual(r["productSmiles"], canonical(expected))
        expected_mol = Chem.MolFromSmiles(expected)
        self.assertEqual(r["productFormula"], rdMolDescriptors.CalcMolFormula(expected_mol))
        stoich = r["stoichiometry"]
        self.assertTrue(stoich["balanced"])
        self.assertEqual([i["coefficient"] for i in stoich["reactants"]], [1, 1])
        self.assertEqual(stoich["product"]["coefficient"], 1)
        self.assertAlmostEqual(stoich["product"]["molarMass"], Descriptors.MolWt(expected_mol), places=6)
        d = service.reaction_diagram(r["id"], ref, reagent, MEDIUM)
        self.assertEqual(d["products"][0]["smiles"], canonical(expected))
        self.assertEqual(sorted(p["smiles"] for p in d["products"][1:]), sorted(["O", "[Cl-].[Na+]"]))
        self.assertIn("<svg", d["svg"])
        self.assertTrue(d["highlightsAvailable"])
        before_rows = [a for a in d["atoms"] if a["side"] == "reactants"]
        after_rows = [a for a in d["atoms"] if a["side"] == "products"]
        before = {a["mapId"]: (a["element"], a["formalCharge"]) for a in before_rows}
        after = {a["mapId"]: (a["element"], a["formalCharge"]) for a in after_rows}
        self.assertEqual((len(before), len(after)), (len(before_rows), len(after_rows)))
        self.assertEqual({m: v[0] for m, v in before.items()}, {m: v[0] for m, v in after.items()})
        self.assertEqual(sum(v[1] for v in before.values()), sum(v[1] for v in after.values()))
        self.assertEqual(sum(v[1] for v in after.values()), 0)
        changes = r["compatibility"]["chargeChanges"]
        self.assertEqual({(before[c["atomMap"]][0], c["before"], c["after"]) for c in changes}, {("O", -1, 0), ("Cl", 0, -1)})
        for m, (_, q) in before.items():
            self.assertEqual(after[m][1], next((c["after"] for c in changes if c["atomMap"] == m), q))
        self.assertEqual(len(d["atomMap"]), len(before))
        self.assertEqual(len(d["bondsBroken"]), 3)
        self.assertEqual({frozenset(c["atoms"]) for c in d["bondsBroken"]}, {frozenset({"C", "H"}), frozenset({"O", "H"}), frozenset({"O", "Cl"})})
        self.assertEqual(len(d["bondsFormed"]), 2)
        self.assertTrue(all(set(c["atoms"]) == {"O", "H"} for c in d["bondsFormed"]))
        self.assertEqual(len(d["bondOrderChanges"]), 1)
        change = d["bondOrderChanges"][0]
        self.assertEqual((change["before"], change["after"]), (1, 2))
        self.assertEqual(set(change["atomMaps"]), set(r["site"]["atomMaps"]))
        self.assertEqual({before[m][0] for m in r["site"]["atomMaps"]}, {"C", "O"})
        report = r["compatibility"]
        self.assertTrue(report["eligible"])
        self.assertEqual(report["substrateSiteMaps"], r["site"]["atomMaps"])
        self.assertEqual({(tuple(sorted(e["atomMaps"])), e["before"], e["after"]) for e in report["editContract"]},
                         {(tuple(sorted(e["atomMaps"])), e["before"], e["after"]) for e in d["changes"]})
        self.assertEqual(set(report["validation"].values()), {"verified"})
        reactive = [g for g in report["groups"] if g["disposition"] == "reactive"]
        self.assertEqual(len(reactive), 1)
        self.assertEqual(reactive[0]["relation"], "reactive")
        self.assertEqual(set(reactive[0]["atomMaps"]), set(r["site"]["atomMaps"]))
        self.assertEqual(r["reasoning"]["label"], "Hypothetical aldehyde stage · conditional 2D only" if r.get("primaryOxidationModel") else "Hypothetical ketone stage · conditional 2D only")
        self.assertEqual(r["information"]["capabilities"]["mappedMechanism"], "unsupported")
        self.assertEqual(r["information"]["capabilities"]["stereochemistry"], "validated spectator retention; reactive alcohol center becomes planar")
        if r.get("primaryOxidationModel"):
            # Phase 5C keeps all graph/charge/provenance assertions above but
            # no longer calls a first-stage aldehyde an approved 3D endpoint.
            self.assertFalse(r["assessment"]["canRun"])
            self.assertTrue(r["assessment"]["evidence"]["canPreview2D"])
            self.assertFalse(r["primaryOxidationModel"]["aldehydeEndpointValidated"])
            with self.assertRaises(service.ChemistryError):
                service.run_curated_reaction(r["id"], ref, reagent, MEDIUM)
            return d, None
        # Phase 5D removes the old unqualified-secondary endpoint assertion,
        # while preserving actual 3D/stereo tests for the explicit bounded model.
        self.assertFalse(r["assessment"]["canRun"])
        with self.assertRaises(service.ChemistryError):service.run_curated_reaction(r["id"],ref,reagent,MEDIUM)
        if not r["secondaryOxidationModel"]["profileScopeEligible"]:
            with self.assertRaises(service.ChemistryError):service.run_curated_reaction(r["id"],ref,reagent,SECONDARY_PROFILE)
            return d,None
        p = service.run_curated_reaction(r["id"], ref, reagent, SECONDARY_PROFILE)["product"]
        self.assertEqual(p["smiles"], canonical(expected))
        self.assertEqual(p["representation"], "3d")
        main_rows = [a for a in after_rows if a["speciesIndex"] == 0]
        self.assertEqual([(a["atomIndex"], a["mapId"], a["element"]) for a in main_rows],
                         [(a["index"], a["mapId"], a["element"]) for a in p["atomLinks"]])
        shape = Chem.MolFromMolBlock(p["molfile"], removeHs=False)
        if any(i.specified == Chem.StereoSpecified.Unspecified for i in Chem.FindPotentialStereo(expected_mol)):
            self.assertEqual(Chem.MolToSmiles(Chem.MolFromSmiles(_identity(shape)), isomericSmiles=False), Chem.MolToSmiles(expected_mol, isomericSmiles=False))
        else:
            self.assertEqual(_identity(shape), canonical(expected))
        for atom in shape.GetAtoms(): atom.SetAtomMapNum(0)
        Chem.AssignStereochemistry(shape, cleanIt=True, force=True)
        rdCIPLabeler.AssignCIPLabels(shape)
        links = {a["mapId"]: a["index"] for a in p["atomLinks"]}
        for center in r["information"]["stereochemistry"]["product"]["chiralCenters"]:
            if center["specified"]:
                atom = shape.GetAtomWithIdx(links[center["atomMap"]])
                self.assertTrue(atom.HasProp("_CIPCode"))
                self.assertEqual(atom.GetProp("_CIPCode"), center["assignment"])
        return d, p

    def check(self, substrate, product):
        ref, options, _ = self.options(substrate)
        self.assertEqual(len(options), 1)
        self.check_option(ref, options[0], product)
        return options[0]

    def test_simple_long_and_branched_primary_alcohols(self):
        for a, p in [("CO", "C=O"), ("CCO", "CC=O"), ("CCCCCCCCCCCCO", "CCCCCCCCCCCC=O"),
                     ("CC(C)CCO", "CC(C)CC=O"), ("CC(C)(C)CO", "CC(C)(C)C=O"), ("OCC1CCCCC1", "O=CC1CCCCC1")]:
            with self.subTest(substrate=a): self.check(a, p)

    def test_secondary_branched_and_cyclic_alcohols(self):
        for a, p in [("CC(O)C", "CC(=O)C"), ("CCC(O)CC", "CCC(=O)CC"), ("CC(C)CC(O)C", "CC(C)CC(=O)C"),
                     ("OC1CCCC1", "O=C1CCCC1"), ("OC1CCCCCC1", "O=C1CCCCCC1"), ("CC1CCC(O)CC1", "CC1CCC(=O)CC1")]:
            with self.subTest(substrate=a): self.check(a, p)

    def test_screened_remote_ethers_and_cyclic_ethers(self):
        for a, p in [("COCCCO", "COCCC=O"), ("COCCCC(O)C", "COCCCC(=O)C"),
                     ("OCCCOC1CCCC1", "O=CCCOC1CCCC1"), ("OCCC1CCCO1", "O=CCC1CCCO1"),
                     ("COc1ccc(CCO)cc1", "COc1ccc(CC=O)cc1")]:
            with self.subTest(substrate=a):
                r = self.check(a, p)
                self.assertTrue(any(g["type"] == "ether" and g["disposition"] == "preserved" for g in r["compatibility"]["groups"]))

    def test_aromatic_net_options_have_explicit_oxidant_caveats(self):
        for a, p in [("OCCc1ccccc1", "O=CCc1ccccc1"), ("OCc1ccccc1", "O=Cc1ccccc1"), ("CC(O)c1ccccc1", "CC(=O)c1ccccc1")]:
            r = self.check(a, p)
            self.assertIn("chlorination", " ".join(r["information"]["limitations"]))

    def test_remote_absolute_centers_and_both_enantiomers(self):
        for a, p in [("CC[C@H](C)CCO", "CC[C@H](C)CC=O"), ("CC[C@@H](C)CCO", "CC[C@@H](C)CC=O"),
                     ("CC[C@H](C)COCCCCO", "CC[C@H](C)COCCCC=O"),
                     ("CC[C@H](C)CCCC(O)C", "CC[C@H](C)CCCC(=O)C")]:
            with self.subTest(substrate=a): self.check(a, p)

    def test_selected_specified_alcohol_center_becomes_planar_not_retained(self):
        for tag in ("@", "@@"):
            r = self.check(f"C[C{tag}H](O)CC", "CC(=O)CC")
            info = r["information"]["stereochemistry"]
            self.assertEqual(len(info["reactant"]["chiralCenters"]), 1)
            self.assertEqual(info["product"]["chiralCenters"], [])
            self.assertEqual(r["compatibility"]["consumedTetrahedralCenters"], [r["site"]["atomMaps"][0]])

    def test_retained_center_can_change_cip_letter_without_inverting(self):
        for tag, before, after in [("@", "S", "R"), ("@@", "R", "S")]:
            r = self.check(f"C[C{tag}H](CCOC)CCO", f"C[C{tag}H](CCOC)CC=O")
            info = r["information"]["stereochemistry"]
            self.assertEqual(info["reactant"]["chiralCenters"][0]["assignment"], before)
            self.assertEqual(info["product"]["chiralCenters"][0]["assignment"], after)

    def test_unsigned_centers_never_gain_assigned_configurations(self):
        r = self.check("CCC(C)CCO", "CCC(C)CC=O")
        self.assertTrue(r["information"]["stereochemistry"]["product"]["chiralCenters"])
        self.assertTrue(all(not c["specified"] and c["assignment"] is None for c in r["information"]["stereochemistry"]["product"]["chiralCenters"]))
        self.assertNotIn("@", r["productSmiles"])

    def test_local_stereo_consumption_does_not_erase_distant_center(self):
        for tag in ("@", "@@"):
            r = self.check(f"CC[C@H](C)CCCC[C{tag}H](O)C", "CC[C@H](C)CCCCC(=O)C")
            info = r["information"]["stereochemistry"]
            self.assertEqual(len(info["reactant"]["chiralCenters"]), 2)
            self.assertEqual(len(info["product"]["chiralCenters"]), 1)

    def test_multiple_alcohol_sites_are_exact_one_site_options(self):
        rows = [("OCCCO", ["O=CCCO", "OCCC=O"]), ("OCCC(O)C", ["O=CCC(O)C", "OCCC(=O)C"]),
                ("CC(O)CCCCCC(O)C", ["CC(=O)CCCCCC(O)C", "CC(O)CCCCCC(=O)C"])]
        for a, expected in rows:
            ref, options, _ = self.options(a)
            self.assertEqual(len(options), 2)
            self.assertEqual(len({r["id"] for r in options}), 2)
            self.assertEqual(len({tuple(r["site"]["atomMaps"]) for r in options}), 2)
            self.assertEqual(sorted(r["productSmiles"] for r in options), sorted(canonical(p) for p in expected))
            for r in options:
                self.check_option(ref, r, r["productSmiles"])
                self.assertTrue(any(g["disposition"] == "alternative-site" for g in r["compatibility"]["groups"]))
                self.assertEqual(len(rule.sites(Chem.MolFromSmiles(r["productSmiles"]))), 1)

    def test_multiple_sites_preserve_or_consume_only_the_selected_center(self):
        a = "CC[C@H](C)C[C@@H](O)CCCCCCO"
        expected = ["CC[C@H](C)CC(=O)CCCCCCO", "CC[C@H](C)C[C@@H](O)CCCCCC=O"]
        ref, options, _ = self.options(a)
        self.assertEqual(len(options), 2)
        self.assertEqual(sorted(r["productSmiles"] for r in options), sorted(canonical(s) for s in expected))
        for r in options: self.check_option(ref, r, r["productSmiles"])
        self.assertEqual(sorted(len(r["information"]["stereochemistry"]["product"]["chiralCenters"]) for r in options), [1, 2])

    def test_remote_tertiary_oh_can_remain_but_is_never_selected(self):
        r = self.check("CC(O)(C)CCCCCCO", "CC(O)(C)CCCCCC=O")
        self.assertTrue(any(g["type"] == "alcohol" and g["disposition"] == "preserved" for g in r["compatibility"]["groups"]))
        for a in ("CC(O)(C)C", "CCC(O)(C)C", "OC1(C)CCCCC1"):
            _, options, result = self.options(a)
            self.assertFalse(options)
            self.assertIn("Tertiary alcohols", " ".join(result["unsupportedReasons"]))

    def test_vicinal_diol_and_lactol_lactone_competition_fail_closed(self):
        for a, reason in [("OCCO", "Vicinal"), ("CC(O)C(O)C", "Vicinal"),
                          ("OCCCCO", "5-membered"), ("OCCCCCO", "6-membered"),
                          ("CC(O)CCC(O)C", "5-membered")]:
            _, options, result = self.options(a)
            self.assertFalse(options)
            self.assertIn(reason, " ".join(result["unsupportedReasons"]))

    def test_competing_unsaturation_and_existing_carbonyls_are_not_inert(self):
        for a, reason in [("C=CCO", "additional alkene"), ("C/C=C/CCCO", "additional alkene"),
                          ("C#CCCCO", "additional alkyne"), ("O=CCCCO", "existing aldehyde"),
                          ("CC(=O)CCCCO", "Additional carbonyl")]:
            _, options, result = self.options(a)
            self.assertFalse(options)
            self.assertIn(reason, " ".join(result["unsupportedReasons"]))

    def test_unvalidated_groups_and_ethers_have_precise_rejections(self):
        rows = [("FCCCCO", "F at substrate atom"), ("NCCCCO", "N at substrate atom"), ("SCCCCO", "S at substrate atom"),
                ("CC(=O)OCCCCO", "ester"), ("O=C(O)CCCCO", "carboxylic acid"), ("OCCCC(=O)N", "amide"),
                ("OOCCCCO", "peroxide"), ("Oc1ccc(CCO)cc1", "phenol"),
                ("OCCCCOCc1ccccc1", "Benzyl/allyl ether"), ("OCCCCOC(OC)C", "Acetal/ketal"),
                ("OCCCCOc1ccc(Oc2ccccc2)cc1", "Diaryl ether"), ("OCCCCc1ccncc1", "Heteroaromatic")]
        for a, reason in rows:
            with self.subTest(substrate=a):
                _, options, result = self.options(a)
                self.assertFalse(options)
                self.assertIn(reason, " ".join(result["unsupportedReasons"]))

    def test_near_site_centers_are_not_automatically_retained(self):
        for a in ("CC[C@H](C)CO", "CC[C@H](C)[C@@H](O)C"):
            _, options, result = self.options(a)
            self.assertFalse(options)
            self.assertIn("adjacent to the new carbonyl", " ".join(result["unsupportedReasons"]))

    def test_non_alcohols_invalid_and_unsupported_inputs(self):
        for a in ("COCCC", "Oc1ccccc1", "CC(=O)O", "CC(=O)C"):
            self.assertFalse(self.options(a)[1])
        for a in ("not-smiles", "CC(O)(C)(C)C", "OCCCC[O-]", "OCCC[CH2]", "OCCC[13CH2]C", "CCO.O",
                  "CC[C@H](C)CCO |&1:2|", "CC[C@H](C)CCO |o1:2|"):
            with self.subTest(substrate=a), self.assertRaises(service.ChemistryError): self.options(a)
        with self.assertRaises(service.ChemistryError): self.options("CCO", {"smiles": "C" * 1025})

    def test_small_ring_and_product_size_limits_are_preserved(self):
        for a in ("OC1CCC1", "OCCCC1CC1"):
            _, options, result = self.options(a)
            self.assertFalse(options)
            self.assertIn("membered ring", " ".join(result["unsupportedReasons"]))
        _, options, _ = self.options("C" * 26 + "O")
        self.assertEqual(len(options), 1)
        self.assertEqual(Chem.AddHs(Chem.MolFromSmiles(options[0]["productSmiles"])).GetNumAtoms(), 79)
        _, options, result = self.options("C" * 27 + "O")
        self.assertFalse(options)
        self.assertIn("exceed 80 explicit atoms", " ".join(result["unsupportedReasons"]))

    def test_first_stage_and_missing_or_incompatible_conditions_are_explicit(self):
        r = self.check("CCCCO", "CCCC=O")
        self.assertIn("further oxidation", r["explanation"])
        self.assertIn("not a claim of an isolated product", r["conditions"])
        self.assertIn("aldehyde-stage", " ".join(r["information"]["limitations"]))
        for cond, state in [({}, "incomplete"), ({"solvent": "dry"}, "alternative"), ({"solvent": "aqueous-protic", "catalyst": "acid"}, "incomplete")]:
            _, options, _ = self.options("CCCCO", conditions=cond)
            self.assertTrue(options)
            self.assertEqual(options[0]["assessment"]["state"], state)
            self.assertNotEqual(options[0]["reasoning"]["label"], "Strong match")
        _, options, result = self.options("CCCCO", conditions={"solvent": "aqueous-protic", "oxidationStage": "further"})
        self.assertFalse(options)
        self.assertIn("Further oxidation starts from an aldehyde", " ".join(result["unsupportedReasons"]))
        self.assertTrue(self.options("CCC(O)C", conditions={"solvent": "aqueous-protic", "oxidationStage": "further"})[1])

    def test_separate_aldehyde_oxidation_and_other_paths_do_not_inherit_policy(self):
        for a in ("CC[C@H](C)CC=O", "CC[C@H](C)CC(=O)C"):
            r = service.match_reactions({"smiles": a}, "sodium-hypochlorite", {"solvent": "aqueous-protic", "oxidationStage": "further"})
            self.assertFalse(r["reactions"])
        r = service.match_reactions({"smiles": "CCCC=O"}, "sodium-hypochlorite", {"solvent": "aqueous-protic", "oxidationStage": "further"})
        self.assertTrue(any(r["mechanism"] == "Aldehyde oxidation" and r["productSmiles"] == canonical("CCCC(=O)O") for r in r["reactions"]))
        for a in ("CC[C@H](C)CCO", "C[C@H](O)CC"):
            for reagent in ("water", "hydrogen-bromide"):
                reactions = service.match_reactions({"smiles": a}, reagent)["reactions"]
                self.assertFalse(any(r["mechanism"] == "Alcohol dehydration" for r in reactions))
                substitution = [r for r in reactions if r["mechanism"] == "Alcohol substitution"]
                if reagent == "water":
                    self.assertFalse(substitution)
                else:
                    # Phase 5B explicitly replaces the old global stereo ban:
                    # unrelated oxidation rules still grant no HX permission.
                    self.assertTrue(substitution)
                    self.assertTrue(all(r["compatibility"]["policy"] == "activated HX alcohol substitution" for r in substitution))
                    self.assertTrue(all(not r["assessment"]["canRun"] for r in substitution))
                    self.assertTrue(all(r["assessment"]["evidence"]["canPreview2D"] for r in substitution))

    def test_actual_oxidant_counterion_reverse_inputs_and_source_maps(self):
        for symbol in ("Li", "Na", "K", "Rb", "Cs"):
            a, b = {"smiles": "[CH3:75][CH2:2][OH:96]"}, {"smiles": f"[{symbol}+].[O-]Cl"}
            f = service.match_reactions(a, b, MEDIUM)["reactions"][0]
            r = service.match_reactions(b, a, MEDIUM)["reactions"][0]
            self.assertEqual(f["productSmiles"], canonical("CC=O"))
            self.assertEqual(f["productSmiles"], r["productSmiles"])
            df = service.reaction_diagram(f["id"], a, b, MEDIUM)
            dr = service.reaction_diagram(r["id"], b, a, MEDIUM)
            self.assertEqual(df["svg"], dr["svg"])
            self.assertEqual({p["smiles"] for p in df["products"][1:]}, {"O", canonical(f"[{symbol}+].[Cl-]")})
            self.assertEqual(next(i["inputSlot"] for i in r["stoichiometry"]["reactants"] if i["formula"] == "C2H6O"), 1)
            oxidant = next(i for i in r["stoichiometry"]["reactants"] if i["inputSlot"] == 0)
            self.assertAlmostEqual(oxidant["molarMass"], Chem.GetPeriodicTable().GetAtomicWeight(symbol) + 15.999 + 35.453, places=6)
        item, _ = _species("source", {**a, "name": "Source mapped alcohol"}, 1)
        self.assertEqual({a.GetIntProp("sourceAtomMap") for a in item["mol"].GetAtoms() if a.HasProp("sourceAtomMap")}, {75, 2, 96})

    def test_wrong_oxidants_and_false_identities_cannot_create_options(self):
        for reagent in ("hydrogen", "water", "hydroxide", {"smiles": "OO", "name": "Sodium hypochlorite"}):
            self.assertFalse(self.options("CCCCO", reagent)[1])
        a = {"smiles": "CC[C@H](C)CCO", "name": "False benzene", "cid": 241, "formula": "C6H6"}
        with patch.dict(service.REACTIONS, {}, clear=True):
            result = service.match_reactions(a, {"smiles": "[Na+].[O-]Cl", "name": "Actual entered reagent"}, MEDIUM)
            self.assertEqual(result["reactions"][0]["productSmiles"], canonical("CC[C@H](C)CC=O"))

    def valid_edit(self, substrate="CC[C@H](C)CCCC[C@@H](O)C"):
        a, n = _species("a", {"smiles": substrate, "name": "Mapped alcohol"}, 1)
        b, _ = _species("b", {"smiles": "[Na+].[O-]Cl", "name": "Actual hypochlorite"}, n)
        site = rule.sites(a["mol"])[0]
        before = _combine([a, b])
        after = _combine([{"mol": m} for m in engine.transform("Alcohol oxidation", [a, b], site)])
        return a, b, site, before, after

    def test_exact_bond_and_charge_contract_not_global_redox_permission(self):
        a, b, site, before, after = self.valid_edit()
        edits = rule.edit_contract(a["mol"], b["mol"], site)
        initial, final = bonds(before), bonds(after)
        self.assertEqual({p for p in initial.keys() | final.keys() if initial.get(p) != final.get(p)}, {tuple(sorted(e["atomMaps"])) for e in edits})
        self.assertEqual(len(edits), 6)
        rule.validate(before, after, a["mol"], b["mol"], site)
        with self.assertRaises(ValueError): compatibility.validate_edit_contract(before, after, edits)
        renumbered = Chem.RenumberAtoms(after, list(reversed(range(after.GetNumAtoms()))))
        rule.validate(before, renumbered, a["mol"], b["mol"], site)

    def test_remote_stereo_corruption_and_invented_stereo_fail_closed(self):
        a, b, site, before, after = self.valid_edit()
        for mutation in ("invert", "erase", "carbonyl-tag", "element", "charge", "map", "bond"):
            changed = Chem.Mol(after)
            center = next(a for a in changed.GetAtoms() if a.GetChiralTag() != Chem.ChiralType.CHI_UNSPECIFIED)
            carbonyl_map = a["mol"].GetAtomWithIdx(site[0]).GetAtomMapNum()
            carbonyl = next(atom for atom in changed.GetAtoms() if atom.GetAtomMapNum() == carbonyl_map)
            if mutation == "invert": center.InvertChirality()
            elif mutation == "erase": center.SetChiralTag(Chem.ChiralType.CHI_UNSPECIFIED)
            elif mutation == "carbonyl-tag": carbonyl.SetChiralTag(Chem.ChiralType.CHI_TETRAHEDRAL_CW)
            elif mutation == "element": changed.GetAtomWithIdx(0).SetAtomicNum(7)
            elif mutation == "charge": changed.GetAtomWithIdx(0).SetFormalCharge(1)
            elif mutation == "map": changed.GetAtomWithIdx(0).SetAtomMapNum(0)
            else: next(b for b in changed.GetBonds() if all(a.GetSymbol() == "C" for a in (b.GetBeginAtom(), b.GetEndAtom()))).SetBondType(Chem.BondType.DOUBLE)
            with self.subTest(mutation=mutation), self.assertRaises(ValueError): rule.validate(before, changed, a["mol"], b["mol"], site)
        unsigned = Chem.Mol(before)
        for atom in unsigned.GetAtoms(): atom.SetChiralTag(Chem.ChiralType.CHI_UNSPECIFIED)
        with self.assertRaises(ValueError): rule.validate(unsigned, after, a["mol"], b["mol"], site)

    def test_contract_cannot_authorize_charge_or_stereo_loss_elsewhere(self):
        a, b, site, before, after = self.valid_edit()
        edits = rule.edit_contract(a["mol"], b["mol"], site)
        charges, lost = rule.charge_contract(b["mol"]), rule.consumed_centers(a["mol"], site)
        distant = next(x.GetAtomMapNum() for x in a["mol"].GetAtoms() if x.GetChiralTag() != Chem.ChiralType.CHI_UNSPECIFIED and x.GetIdx() != site[0])
        for charge_edit in ([charges[0]], [*charges, charges[0]], [{**charges[0], "before": 0}, charges[1]]):
            with self.assertRaises(ValueError): compatibility.validate_edit_contract(before, after, edits, charge_changes=charge_edit, consumed_tetrahedral_centers=lost)
        for centers in (lost + [distant], [True], [lost[0], lost[0]], [999]):
            with self.assertRaises(ValueError): compatibility.validate_edit_contract(before, after, edits, charge_changes=charges, consumed_tetrahedral_centers=centers)

    def test_unknown_groups_wrong_sites_and_injected_failures_are_rejected(self):
        mol = Chem.MolFromSmiles("CCO")
        self.assertEqual(rule.group_check(mol, (1, 2), {"type": "unknown", "atomIndices": [0]})[0], "rejected")
        for invalid in ((), (0, 0), (0, 999), (True, 1), (0, 1)):
            self.assertFalse(rule.assess(mol, invalid)["eligible"])
        for target in ("server.reaction_compatibility.validate_edit_contract", "server.stereochemistry.validate_retained_stereo"):
            with patch(target, side_effect=ValueError("Independent oxidation contract failure")):
                _, options, result = self.options("COCCCO")
                self.assertFalse(options)
                self.assertIn("Independent oxidation contract failure", " ".join(result["unsupportedReasons"]))
        wrong, _ = _species("wrong", {"smiles": "OO", "name": "Wrong oxidant"}, 100)
        with self.assertRaises(ValueError): rule.oxidant_atoms(wrong["mol"])

    def test_prior_ester_and_hydrogenation_increments_remain_working(self):
        for a, reagent, mechanism in [("C=CC[C@H](C)CC", "hydrogen", "Hydrogenation"),
                                      ("CC[C@H](C)CC=O", "hydrogen", "Carbonyl hydrogenation"),
                                      ("O=C1OCCC1", "water", "Ester hydrolysis"),
                                      ("CC(=O)Oc1ccccc1", "hydroxide", "Ester saponification")]:
            self.assertTrue(any(r["mechanism"] == mechanism for r in service.match_reactions({"smiles": a}, reagent)["reactions"]))

    def test_authenticated_public_http_match_diagram_run(self):
        from server.production_app import create_app
        origin = "https://alcohol-increment.example.test"
        app = create_app({"TRIAL_PASSWORD": "Alcohol-synthetic-test-password",
                          "SESSION_SECRET": "5a793bc832adc647a5f382190dead01d19f58f6fa0c9246eb8b2b31f0f419b60",
                          "PUBLIC_ORIGIN": origin, "FRAME_ANCESTORS": "https://site.example.test",
                          "DIST_DIR": "/private/tmp/alcohol-no-static-needed", "TESTING": True}, chemistry_backend=service)
        client = app.test_client()
        self.assertEqual(client.post("/login", base_url=origin, headers={"Origin": origin}, data={"password": "Alcohol-synthetic-test-password"}).status_code, 303)
        for a, expected in [("CC[C@H](C)CCO", "CC[C@H](C)CC=O"), ("C[C@H](O)CC", "CC(=O)CC")]:
            body = {"reactantA": {"smiles": a}, "reactantB": "sodium-hypochlorite", "conditions": MEDIUM}
            response = client.post("/api/reactions/match", base_url=origin, headers={"Origin": origin}, json=body)
            self.assertEqual(response.status_code, 200)
            r = next(r for r in response.get_json()["reactions"] if r["mechanism"] == "Alcohol oxidation")
            self.assertEqual(r["productSmiles"], canonical(expected))
            body["reactionId"] = r["id"]
            d = client.post("/api/reactions/diagram", base_url=origin, headers={"Origin": origin}, json=body)
            p = client.post("/api/reactions/run", base_url=origin, headers={"Origin": origin}, json=body)
            if r.get("primaryOxidationModel"):
                # Phase 5C corrects the old unsupported aldehyde-endpoint claim.
                self.assertEqual((d.status_code, p.status_code), (200, 422))
                self.assertEqual(d.get_json()["products"][0]["smiles"], canonical(expected))
                self.assertFalse(r["assessment"]["evidence"]["canGenerate3D"])
            else:
                self.assertEqual((d.status_code,p.status_code),(200,422))
                body["conditions"]=SECONDARY_PROFILE
                qualified=client.post("/api/reactions/run",base_url=origin,headers={"Origin":origin},json=body)
                self.assertEqual(qualified.status_code,200)
                self.assertEqual(d.get_json()["products"][0]["smiles"],qualified.get_json()["product"]["smiles"])
        response = client.post("/api/reactions/match", base_url=origin, headers={"Origin": origin},
                               json={"reactantA": {"smiles": "OCCCCO"}, "reactantB": "sodium-hypochlorite", "conditions": MEDIUM})
        self.assertFalse(response.get_json()["reactions"])
        self.assertIn("cyclization", " ".join(response.get_json()["unsupportedReasons"]))


if __name__ == "__main__": unittest.main()

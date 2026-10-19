"""Independent carbonyl/H2 expectations through the actual public workflow."""
import unittest
from unittest.mock import patch
from rdkit import Chem
from rdkit.Chem import Descriptors, rdMolDescriptors, rdCIPLabeler
from server import chemistry_server as service, carbonyl_hydrogenation_rule as rule
from server import reaction_engine as engine, reaction_compatibility as compatibility
from server.reaction_diagrams import _species, _combine, _identity

METAL = {"catalyst": "metal"}


def canonical(smiles):
    return Chem.MolToSmiles(Chem.MolFromSmiles(smiles))


def bonds(mol):
    return {tuple(sorted((b.GetBeginAtom().GetAtomMapNum(), b.GetEndAtom().GetAtomMapNum()))): b.GetBondTypeAsDouble() for b in mol.GetBonds()}


class CarbonylCompatibilityTests(unittest.TestCase):
    def options(self, smiles, reagent="hydrogen", conditions=METAL):
        ref = {"name": "Independent carbonyl input", "smiles": smiles}
        result = service.match_reactions(ref, reagent, conditions)
        return ref, [r for r in result["reactions"] if r["mechanism"] == "Carbonyl hydrogenation"], result

    def check_option(self, ref, r, expected, reagent="hydrogen"):
        self.assertEqual(r["productSmiles"], canonical(expected))
        self.assertEqual(r["byproducts"], [])
        self.assertTrue(r["stoichiometry"]["balanced"])
        self.assertEqual([i["coefficient"] for i in r["stoichiometry"]["reactants"]], [1, 1])
        self.assertEqual(r["stoichiometry"]["product"]["coefficient"], 1)
        self.assertEqual(r["productFormula"], rdMolDescriptors.CalcMolFormula(Chem.MolFromSmiles(expected)))
        self.assertAlmostEqual(r["stoichiometry"]["product"]["molarMass"], Descriptors.MolWt(Chem.MolFromSmiles(expected)), places=6)
        d = service.reaction_diagram(r["id"], ref, reagent, METAL)
        self.assertEqual([p["smiles"] for p in d["products"]], [canonical(expected)])
        self.assertIn("<svg", d["svg"])
        self.assertTrue(d["highlightsAvailable"])
        before_rows = [a for a in d["atoms"] if a["side"] == "reactants"]
        after_rows = [a for a in d["atoms"] if a["side"] == "products"]
        before = {a["mapId"]: (a["element"], a["formalCharge"]) for a in before_rows}
        after = {a["mapId"]: (a["element"], a["formalCharge"]) for a in after_rows}
        self.assertEqual((len(before), len(after)), (len(before_rows), len(after_rows)))
        self.assertEqual(before, after)
        self.assertEqual(sum(a[1] for a in after.values()), 0)
        self.assertEqual(len(d["atomMap"]), len(before))
        self.assertEqual(len(d["bondsBroken"]), 1)
        self.assertEqual(d["bondsBroken"][0]["atoms"], ["H", "H"])
        self.assertEqual(len(d["bondsFormed"]), 2)
        self.assertEqual({frozenset(c["atoms"]) for c in d["bondsFormed"]}, {frozenset({"C", "H"}), frozenset({"O", "H"})})
        self.assertEqual(len(d["bondOrderChanges"]), 1)
        change = d["bondOrderChanges"][0]
        self.assertEqual((change["before"], change["after"]), (2, 1))
        self.assertEqual(set(change["atomMaps"]), set(r["site"]["atomMaps"]))
        self.assertEqual({before[m][0] for m in r["site"]["atomMaps"]}, {"C", "O"})
        report = r["compatibility"]
        self.assertTrue(report["eligible"])
        self.assertEqual(report["substrateSiteMaps"], r["site"]["atomMaps"])
        self.assertEqual({(tuple(sorted(e["atomMaps"])), e["before"], e["after"]) for e in report["editContract"]},
                         {(tuple(sorted(e["atomMaps"])), e["before"], e["after"]) for e in d["changes"]})
        self.assertEqual(set(report["validation"].values()), {"verified"})
        self.assertTrue(set(report["reactiveAtomMaps"]) <= before.keys())
        reactive = [g for g in report["groups"] if g["disposition"] == "reactive"]
        self.assertEqual(len(reactive), 1)
        self.assertEqual(reactive[0]["relation"], "reactive")
        self.assertEqual(set(reactive[0]["atomMaps"]), set(r["site"]["atomMaps"]))
        self.assertTrue(all(set(g["atomMaps"]) <= before.keys() for g in report["groups"]))
        p = service.run_curated_reaction(r["id"], ref, reagent, METAL)["product"]
        self.assertEqual(p["smiles"], canonical(expected))
        self.assertEqual(p["representation"], "3d")
        self.assertEqual([(a["atomIndex"], a["mapId"], a["element"]) for a in after_rows],
                         [(a["index"], a["mapId"], a["element"]) for a in p["atomLinks"]])
        shape = Chem.MolFromMolBlock(p["molfile"], removeHs=False)
        expected_mol = Chem.MolFromSmiles(expected)
        if any(i.specified == Chem.StereoSpecified.Unspecified for i in Chem.FindPotentialStereo(expected_mol)):
            self.assertEqual(Chem.MolToSmiles(Chem.MolFromSmiles(_identity(shape)), isomericSmiles=False),
                             Chem.MolToSmiles(expected_mol, isomericSmiles=False))
        else:
            self.assertEqual(_identity(shape), canonical(expected))
        # Even when a NEW center is unspecified, the rendered shape must retain
        # the OLD specified configurations. Maps never contribute to CIP ranks.
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

    def test_simple_long_and_branched_aldehydes(self):
        for a, p in [("C=O", "CO"), ("CC=O", "CCO"), ("CCCCCCC=O", "CCCCCCCO"),
                     ("CC(C)CC=O", "CC(C)CCO"), ("O=CC1CCCCC1", "OCC1CCCCC1")]:
            with self.subTest(substrate=a): self.check(a, p)

    def test_simple_branched_and_cyclic_ketones(self):
        for a, p in [("CC(=O)C", "CC(O)C"), ("CCC(=O)CC", "CCC(O)CC"),
                     ("CC(C)CC(=O)C", "CC(C)CC(O)C"), ("CC(C)(C)C(=O)CC", "CC(C)(C)C(O)CC"),
                     ("O=C1CCCC1", "OC1CCCC1"), ("O=C1CCCCCC1", "OC1CCCCCC1")]:
            with self.subTest(substrate=a): self.check(a, p)

    def test_screened_alcohols_are_checked_not_blanket_inert(self):
        for a, p in [("OCCC=O", "OCCCO"), ("OCCCCCCC=O", "OCCCCCCCO"),
                     ("CC(=O)CCCCCCO", "CC(O)CCCCCCO"), ("CC(O)CCCCCC=O", "CC(O)CCCCCCO")]:
            with self.subTest(substrate=a):
                r = self.check(a, p)
                groups = [g for g in r["compatibility"]["groups"] if g["type"] == "alcohol"]
                self.assertTrue(groups)
                self.assertTrue(all(g["disposition"] == "preserved" for g in groups))
                self.assertTrue(any(f["factor"].startswith("site-compatibility") for f in r["reasoning"]["factors"]))

    def test_screened_dialkyl_aryl_alkyl_and_cyclic_ethers(self):
        for a, p in [("COCCC=O", "COCCCO"), ("COCCC(=O)CC", "COCCC(O)CC"),
                     ("CC(=O)COCCC", "CC(O)COCCC"), ("COc1ccc(C=O)cc1", "COc1ccc(CO)cc1"),
                     ("O=CCCOC1CCCC1", "OCCCOC1CCCC1"), ("O=CC1CCCO1", "OCC1CCCO1")]:
            with self.subTest(substrate=a):
                r = self.check(a, p)
                self.assertTrue(any(g["type"] == "ether" and g["disposition"] == "preserved" for g in r["compatibility"]["groups"]))

    def test_existing_aromatic_net_options_remain_bounded_not_a_pd_protocol(self):
        for a, p in [("O=Cc1ccccc1", "OCc1ccccc1"), ("CC(=O)c1ccccc1", "CC(O)c1ccccc1"),
                     ("COc1ccc(C=O)cc1", "COc1ccc(CO)cc1"), ("O=CCc1ccccc1", "OCCc1ccccc1")]:
            with self.subTest(substrate=a):
                r = self.check(a, p)
                self.assertEqual(r["reasoning"]["label"], "Possible")
                self.assertIn("deoxygenation", " ".join(r["information"]["limitations"]))
                self.assertIn("not selective partial reduction", " ".join(r["information"]["limitations"]))

    def test_remote_absolute_centers_both_enantiomers_and_combinations(self):
        rows = [("CC[C@H](C)CC=O", "CC[C@H](C)CCO"), ("CC[C@@H](C)CC=O", "CC[C@@H](C)CCO"),
                ("CC[C@H](C)COCCCC=O", "CC[C@H](C)COCCCCO"),
                ("CC[C@H](C)C[C@@H](O)CCCCCC=O", "CC[C@H](C)C[C@@H](O)CCCCCCO"),
                ("CC[C@H](C)CCCC(=O)C", "CC[C@H](C)CCCC(O)C")]
        for a, p in rows:
            with self.subTest(substrate=a):
                r = self.check(a, p)
                self.assertIn("validated retention", r["information"]["stereochemistry"]["effect"])

    def test_retained_center_can_switch_cip_letter_without_inverting(self):
        for tag, before, after in [("@", "R", "S"), ("@@", "S", "R")]:
            r = self.check(f"C[C{tag}H](CCOC)CC=O", f"C[C{tag}H](CCOC)CCO")
            info = r["information"]["stereochemistry"]
            self.assertEqual(info["reactant"]["chiralCenters"][0]["assignment"], before)
            self.assertEqual(info["product"]["chiralCenters"][0]["assignment"], after)

    def test_remote_center_losing_stereogenicity_is_rejected_not_erased(self):
        _, options, result = self.options("C[C@H](CCCCO)CCCC=O")
        self.assertFalse(options)
        self.assertIn("no longer stereogenic", " ".join(result["unsupportedReasons"]))
        self.assertIn("not silently discarded", " ".join(result["unsupportedReasons"]))

    def test_separated_dicarbonyls_are_one_site_not_complete_reduction(self):
        rows = [("CC(=O)CCCC(=O)C", ["CC(O)CCCC(=O)C", "CC(=O)CCCC(O)C"]),
                ("O=CCCCCC=O", ["OCCCCCC=O", "O=CCCCCCO"]),
                ("CCC(=O)CCC=O", ["CCC(O)CCC=O", "CCC(=O)CCCO"])]
        for substrate, expected in rows:
            ref, options, _ = self.options(substrate)
            self.assertEqual(len(options), 2)
            self.assertEqual(len({r["id"] for r in options}), 2)
            self.assertEqual(len({tuple(r["site"]["atomMaps"]) for r in options}), 2)
            self.assertEqual(sorted(r["productSmiles"] for r in options), sorted(canonical(s) for s in expected))
            for r in options:
                self.check_option(ref, r, r["productSmiles"])
                self.assertEqual(len(rule.sites(Chem.MolFromSmiles(r["productSmiles"]))), 1)
                self.assertEqual(r["reasoning"]["label"], "Possible")
                self.assertTrue(any(g["disposition"] == "alternative-site" for g in r["compatibility"]["groups"]))

    def test_new_alcohol_center_and_originally_unsigned_centers_stay_unsigned(self):
        for substrate in ("CCC(=O)C", "CC(O)CCCCCC(=O)C"):
            _, options, _ = self.options(substrate)
            self.assertTrue(options)
            for r in options:
                mol = Chem.MolFromSmiles(r["productSmiles"])
                self.assertTrue(Chem.FindPotentialStereo(mol))
                self.assertFalse(any(a.GetChiralTag() != Chem.ChiralType.CHI_UNSPECIFIED for a in mol.GetAtoms()))
                self.assertEqual(r["information"]["capabilities"]["stereochemistry"], "validated spectator retention; new centers unassigned")
                self.assertEqual(r["information"]["capabilities"]["mappedMechanism"], "unsupported")

    def test_competing_and_unvalidated_groups_have_specific_reasons(self):
        rows = [("C=CCC=O", "additional alkene"), ("C/C=C/CCC=O", "additional alkene"),
                ("C=CC=O", "adjacent unsaturated"), ("C#CCCC=O", "additional alkyne"),
                ("CC(=O)C(=O)C", "additional carbonyl"), ("CC(=O)CC(=O)C", "1,3-dicarbonyl"),
                ("O=CCCC(=O)O", "carboxylic acid"), ("O=CCCC(=O)OC", "ester"), ("O=CCCC(=O)N", "amide"),
                ("O=CCCOO", "peroxide"), ("O=CCCc1ccc(O)cc1", "phenol"),
                ("O=CCCOCc1ccccc1", "Benzyl/allyl ether"), ("O=CCCOCC=C", "Benzyl/allyl ether"),
                ("O=CCCOC(O)C", "Acetal/ketal"), ("O=CCCOC(OC)C", "Acetal/ketal"),
                ("O=CCCC(O)O", "Geminal-diol"), ("O=CCCOCc1ccccc1", "Benzyl/allyl"),
                ("O=CCCC(O)c1ccccc1", "allylic/benzylic alcohol"),
                ("O=CCc1ccncc1", "Heteroaromatic"), ("O=CCCCF", "F at substrate atom"),
                ("O=CCCCCl", "Cl at substrate atom"), ("O=CCCCN", "N at substrate atom"),
                ("O=CCCCS", "S at substrate atom"), ("O=Cc1ccc(Oc2ccccc2)cc1", "Diaryl ether")]
        for sm, text in rows:
            with self.subTest(substrate=sm):
                _, options, result = self.options(sm)
                self.assertEqual(options, [])
                self.assertIn(text, " ".join(result["unsupportedReasons"]))

    def test_hydroxy_carbonyl_cyclization_and_alpha_chelation_are_screened(self):
        for sm, reason in [("OCCCC=O", "5-membered"), ("OCCCCC=O", "6-membered"),
                           ("CC(=O)CCC(O)C", "5-membered"), ("OCC=O", "alpha-hydroxy")]:
            _, options, result = self.options(sm)
            self.assertEqual(options, [])
            self.assertIn(reason, " ".join(result["unsupportedReasons"]))

    def test_small_rings_and_near_site_stereo_are_not_globally_allowed(self):
        for sm, reason in [("O=C1CCC1", "4-membered"), ("O=CCCC1CC1", "3-membered"),
                           ("CC[C@H](C)C=O", "at/adjacent")]:
            _, options, result = self.options(sm)
            self.assertFalse(options)
            self.assertIn(reason, " ".join(result["unsupportedReasons"]))

    def test_acid_ester_amide_and_wrong_reductants_never_become_false_sites(self):
        for substrate in ("CC(=O)O", "CC(=O)OC", "CC(=O)N", "COC", "CCC(O)C"):
            self.assertFalse(self.options(substrate)[1])
            mol = Chem.MolFromSmiles(substrate)
            for site in rule.sites(mol): self.assertFalse(rule.assess(mol, site)["eligible"])
        for reagent in ("water", "hydroxide", "sodium-hypochlorite"):
            self.assertFalse(self.options("CCCC=O", reagent)[1])
        with self.assertRaises(service.ChemistryError): self.options("CCCC=O", {"smiles": "[Na+].[BH4-]"})

    def test_invalid_electronic_states_components_and_enhanced_stereo_fail_closed(self):
        for sm in ("not-smiles", "CC(=O)(C)C", "O=CCCC[O-]", "O=CCC[CH2]", "O=CCC[13CH2]C", "CC=O.O",
                   "CC[C@H](C)CC=O |&1:2|", "CC[C@H](C)CC=O |o1:2|"):
            with self.subTest(substrate=sm), self.assertRaises(service.ChemistryError): self.options(sm)
        with self.assertRaises(service.ChemistryError):
            self.options("CC[C@H](C)CC=O |&1:2|", {"smiles": "[H][H]"})
        with self.assertRaises(service.ChemistryError):
            self.options("CC=O", {"smiles": "C" * 1025})

    def test_size_cap_counts_added_h2_and_does_not_erase_limits(self):
        _, options, _ = self.options("C" * 25 + "=O")
        self.assertEqual(len(options), 1)
        self.assertEqual(Chem.AddHs(Chem.MolFromSmiles(options[0]["productSmiles"])).GetNumAtoms(), 78)
        _, options, result = self.options("C" * 26 + "=O")
        self.assertFalse(options)
        self.assertIn("exceed 80 explicit atoms", " ".join(result["unsupportedReasons"]))

    def test_reverse_order_source_map_provenance_and_exact_product_atom_links(self):
        ref = {"name": "Source mapped carbonyl", "smiles": "[CH3:55][CH2:7][CH:93]=[O:21]"}
        r = next(r for r in service.match_reactions(ref, "hydrogen", METAL)["reactions"] if r["mechanism"] == "Carbonyl hydrogenation")
        reverse = next(r for r in service.match_reactions("hydrogen", ref, METAL)["reactions"] if r["mechanism"] == "Carbonyl hydrogenation")
        d, _ = self.check_option(ref, r, "CCCO")
        self.assertEqual(r["productSmiles"], reverse["productSmiles"])
        self.assertEqual(d["svg"], service.reaction_diagram(reverse["id"], "hydrogen", ref, METAL)["svg"])
        self.assertEqual({v["formula"]: v["inputSlot"] for v in reverse["stoichiometry"]["reactants"]}, {"H2": 0, "C3H6O": 1})
        item, _ = _species("provenance", ref, 1)
        self.assertEqual({a.GetIntProp("sourceAtomMap") for a in item["mol"].GetAtoms() if a.HasProp("sourceAtomMap")}, {55, 7, 93, 21})

    def test_names_formulas_and_cids_do_not_determine_eligibility(self):
        a = {"smiles": "CC[C@H](C)CC=O", "name": "False benzene name", "formula": "C6H6", "cid": 241}
        b = {"smiles": "[H][H]", "name": "Actual entered H2"}
        with patch.dict(service.REACTIONS, {}, clear=True):
            r = next(r for r in service.match_reactions(a, b, METAL)["reactions"] if r["mechanism"] == "Carbonyl hydrogenation")
            self.assertEqual(r["productSmiles"], canonical("CC[C@H](C)CCO"))

    def test_missing_or_different_catalyst_never_becomes_aligned(self):
        for condition in ({}, {"catalyst": "none"}, {"catalyst": "acid"}, {"catalyst": "lindlar"}):
            _, options, _ = self.options("COCCC=O", conditions=condition)
            self.assertTrue(options)
            self.assertNotEqual(options[0]["assessment"]["state"], "aligned")
            self.assertNotEqual(options[0]["reasoning"]["label"], "Strong match")

    def valid_edit(self, substrate="C[C@H](CCOC)CC=O"):
        a, n = _species("a", {"name": "Mapped carbonyl", "smiles": substrate}, 1)
        b, _ = _species("b", {"name": "Actual H2", "smiles": "[H][H]"}, n)
        site = rule.sites(a["mol"])[0]
        before = _combine([a, b])
        after = _combine([{"mol": m} for m in engine.transform("Carbonyl hydrogenation", [a, b], site)])
        return a, b, site, before, after, rule.edit_contract(a["mol"], b["mol"], site)

    def test_independent_edit_contract_preserves_every_unselected_bond(self):
        a, b, site, before, after, edits = self.valid_edit("OCCCCCC(=O)CCCOC")
        initial, final = bonds(before), bonds(after)
        changed = {p for p in initial.keys() | final.keys() if initial.get(p) != final.get(p)}
        self.assertEqual(changed, {tuple(sorted(e["atomMaps"])) for e in edits})
        self.assertEqual(len(changed), 4)
        rule.validate(before, after, a["mol"], b["mol"], site)
        renumbered = Chem.RenumberAtoms(after, list(reversed(range(after.GetNumAtoms()))))
        compatibility.validate_edit_contract(before, renumbered, edits)

    def test_contract_rejects_atom_charge_unselected_bond_and_stereo_corruption(self):
        a, b, site, before, after, _ = self.valid_edit()
        for mutation in ("element", "charge", "bond", "invert", "erase", "map"):
            changed = Chem.Mol(after)
            center = next(a for a in changed.GetAtoms() if a.GetChiralTag() != Chem.ChiralType.CHI_UNSPECIFIED)
            if mutation == "element": changed.GetAtomWithIdx(0).SetAtomicNum(7)
            elif mutation == "charge": changed.GetAtomWithIdx(0).SetFormalCharge(1)
            elif mutation == "map": changed.GetAtomWithIdx(0).SetAtomMapNum(0)
            elif mutation == "invert": center.InvertChirality()
            elif mutation == "erase": center.SetChiralTag(Chem.ChiralType.CHI_UNSPECIFIED)
            else:
                ether = next(o for o in changed.GetAtoms() if o.GetSymbol() == "O" and all(n.GetSymbol() == "C" for n in o.GetNeighbors()))
                ether.GetBonds()[0].SetBondType(Chem.BondType.DOUBLE)
            with self.subTest(mutation=mutation), self.assertRaises(ValueError): rule.validate(before, changed, a["mol"], b["mol"], site)
        original_unsigned = Chem.Mol(before)
        next(a for a in original_unsigned.GetAtoms() if a.GetChiralTag() != Chem.ChiralType.CHI_UNSPECIFIED).SetChiralTag(Chem.ChiralType.CHI_UNSPECIFIED)
        with self.assertRaises(ValueError): rule.validate(original_unsigned, after, a["mol"], b["mol"], site)

    def test_failed_validation_and_unknown_groups_never_become_public_options(self):
        for target in ("server.reaction_compatibility.validate_edit_contract", "server.stereochemistry.validate_retained_stereo"):
            with patch(target, side_effect=ValueError("Independent carbonyl validation failure")):
                _, options, result = self.options("COCCC=O")
                self.assertFalse(options)
                self.assertIn("Independent carbonyl validation failure", " ".join(result["unsupportedReasons"]))
        mol = Chem.MolFromSmiles("CC=O")
        self.assertEqual(rule.group_check(mol, (1, 2), {"type": "unknown", "atomIndices": [0]})[0], "rejected")
        for invalid in ((), (0, 0), (0, 999), (True, 1), (0, 1)):
            self.assertFalse(rule.assess(mol, invalid)["eligible"])
        a, b, site, _, _, _ = self.valid_edit()
        water, _ = _species("wrong", {"name": "Water", "smiles": "O"}, 100)
        with self.assertRaises(ValueError): rule.edit_contract(a["mol"], water["mol"], site)

    def test_phase1_esters_alkene_compatibility_and_other_policies_unchanged(self):
        for sm in ("C=CCCCO", "C=CC[C@H](C)CC"):
            r = service.match_reactions({"smiles": sm}, "hydrogen", METAL)
            self.assertTrue(any(x["mechanism"] == "Hydrogenation" for x in r["reactions"]))
        for sm in ("O=C1OCCC1", "CC(=O)Oc1ccccc1"):
            for reagent, mechanism in [("water", "Ester hydrolysis"), ("hydroxide", "Ester saponification")]:
                self.assertTrue(any(r["mechanism"] == mechanism for r in service.match_reactions({"smiles": sm}, reagent)["reactions"]))
        # Phase 2C opts alcohol oxidation in separately; aldehyde oxidation
        # still cannot inherit either hydrogenation compatibility policy.
        r = service.match_reactions({"smiles": "CC[C@H](C)CC=O"}, "sodium-hypochlorite", {"solvent": "aqueous-protic", "oxidationStage": "further"})
        self.assertFalse(any(x["mechanism"] == "Aldehyde oxidation" for x in r["reactions"]))

    def test_authenticated_http_public_match_diagram_run_and_specific_rejection(self):
        from server.production_app import create_app
        origin = "https://carbonyl-increment.example.test"
        password = "Carbonyl-synthetic-test-password"
        app = create_app({"TRIAL_PASSWORD": password,
                          "SESSION_SECRET": "5a793bc832adc647a5f382190dead01d19f58f6fa0c9246eb8b2b31f0f419b60",
                          "PUBLIC_ORIGIN": origin, "FRAME_ANCESTORS": "https://site.example.test",
                          "DIST_DIR": "/private/tmp/carbonyl-no-static-needed", "TESTING": True}, chemistry_backend=service)
        client = app.test_client()
        self.assertEqual(client.post("/login", base_url=origin, headers={"Origin": origin}, data={"password": password}).status_code, 303)
        for sm, expected in [("CC[C@H](C)CC=O", "CC[C@H](C)CCO"), ("COCCC=O", "COCCCO")]:
            body = {"reactantA": {"smiles": sm}, "reactantB": "hydrogen", "conditions": METAL}
            response = client.post("/api/reactions/match", base_url=origin, headers={"Origin": origin}, json=body)
            self.assertEqual(response.status_code, 200)
            r = next(r for r in response.get_json()["reactions"] if r["mechanism"] == "Carbonyl hydrogenation")
            self.assertTrue(r["compatibility"]["eligible"])
            self.assertEqual(r["productSmiles"], canonical(expected))
            body["reactionId"] = r["id"]
            d = client.post("/api/reactions/diagram", base_url=origin, headers={"Origin": origin}, json=body)
            p = client.post("/api/reactions/run", base_url=origin, headers={"Origin": origin}, json=body)
            self.assertEqual((d.status_code, p.status_code), (200, 200))
            self.assertEqual(d.get_json()["products"][0]["smiles"], p.get_json()["product"]["smiles"])
        response = client.post("/api/reactions/match", base_url=origin, headers={"Origin": origin},
                               json={"reactantA": {"smiles": "OCCCC=O"}, "reactantB": "hydrogen", "conditions": METAL})
        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.get_json()["reactions"])
        self.assertIn("hemiacetal/hemiketal", " ".join(response.get_json()["unsupportedReasons"]))


if __name__ == "__main__": unittest.main()

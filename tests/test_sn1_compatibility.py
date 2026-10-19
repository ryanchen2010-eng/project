"""Independent water-solvolysis net graphs and exact stepwise SN1 contracts."""
import unittest
from unittest.mock import patch
from rdkit import Chem
from rdkit.Chem import Descriptors, rdMolDescriptors, rdCIPLabeler
from server import chemistry_server as service, sn1_rule as rule, stereochemistry as stereo
from server import reaction_engine as engine, reaction_compatibility as compatibility
from server.reaction_diagrams import _species, _combine, _identity

CONDITIONS = {"solvent": "aqueous-protic", "temperature": "ambient"}


def canonical(smiles):
    return Chem.MolToSmiles(Chem.MolFromSmiles(smiles))


def parse_state(state):
    params = Chem.SmilesParserParams(); params.removeHs = False
    return Chem.MolFromSmiles(state["mappedSmiles"], params)


def atoms(molecule):
    return {a.GetAtomMapNum(): a for a in molecule.GetAtoms()}


def mapped(smiles):
    a, n = _species("substrate", {"name": "Independent SN1 structure", "smiles": smiles}, 1)
    b, n = _species("water", {"name": "Water", "smiles": "O"}, n)
    solvent, _ = _species("solvent", {"name": "Solvent water", "smiles": "O"}, n)
    return a, b, solvent


class SN1CompatibilityTests(unittest.TestCase):
    def options(self, smiles, reagent="water", conditions=CONDITIONS):
        ref = {"name": "Independent SN1 test input", "smiles": smiles}
        result = service.match_reactions(ref, reagent, conditions)
        return ref, [r for r in result["reactions"] if r["mechanism"] == "SN1"], result

    def check_option(self, ref, r, expected):
        expected = canonical(expected)
        self.assertEqual(r["productSmiles"], expected)
        self.assertEqual(r["productFormula"], rdMolDescriptors.CalcMolFormula(Chem.MolFromSmiles(expected)))
        data = r["stoichiometry"]
        self.assertTrue(data["balanced"])
        self.assertEqual([x["coefficient"] for x in data["reactants"]], [1, 1])
        self.assertEqual(data["product"]["coefficient"], 1)
        self.assertAlmostEqual(data["product"]["molarMass"], Descriptors.MolWt(Chem.MolFromSmiles(expected)), places=6)
        self.assertAlmostEqual(data["reactants"][1]["molarMass"], 18.015, places=6)
        self.assertTrue(any("hydronium" in x for x in data["notes"]))
        d = service.reaction_diagram(r["id"], ref, "water", CONDITIONS)
        self.assertTrue(d["highlightsAvailable"])
        self.assertEqual(d["products"][0]["smiles"], expected)
        source = {a["mapId"]: (a["element"], a["formalCharge"]) for a in d["atoms"] if a["side"] == "reactants"}
        target = {a["mapId"]: (a["element"], a["formalCharge"]) for a in d["atoms"] if a["side"] == "products"}
        self.assertEqual(source, target)  # simplified neutral alcohol + HX net equation
        report = r["compatibility"]
        self.assertEqual(report["policy"], "water SN1 solvolysis")
        self.assertTrue(report["eligible"])
        self.assertEqual(set(report["validation"].values()), {"verified"})
        self.assertEqual(report["substrateSiteMaps"], r["site"]["atomMaps"])
        s = report["solvolyses"][0]
        c, x, o, h = (s[k] for k in ("center", "leaving", "incoming", "hydrogen"))
        self.assertEqual((source[o][0], source[h][0]), ("O", "H"))
        self.assertEqual({frozenset(e["atomMaps"]) for e in d["bondsBroken"]}, {frozenset((c, x)), frozenset((o, h))})
        self.assertEqual({frozenset(e["atomMaps"]) for e in d["bondsFormed"]}, {frozenset((c, o)), frozenset((x, h))})
        self.assertFalse(d["bondOrderChanges"])
        self.assertEqual(d["products"][1]["smiles"], source[x][0])
        self.assertEqual(set(report["reactiveAtomMaps"]), {c, x, o, h})
        self.assertEqual({(frozenset(e["atomMaps"]), e["before"], e["after"]) for e in report["editContract"]},
                         {(frozenset(e["atomMaps"]), e["before"], e["after"]) for e in d["changes"]})
        self.check_mechanism(d, r)
        p = service.run_curated_reaction(r["id"], ref, "water", CONDITIONS)["product"]
        self.assertEqual((p["smiles"], p["representation"]), (expected, "3d"))
        rows = [a for a in d["atoms"] if a["side"] == "products" and a["speciesIndex"] == 0]
        self.assertEqual([(a["atomIndex"], a["mapId"], a["element"]) for a in rows],
                         [(a["index"], a["mapId"], a["element"]) for a in p["atomLinks"]])
        self.assertTrue({c, o} <= {a["mapId"] for a in p["atomLinks"]})
        self.assertFalse({x, h} & {a["mapId"] for a in p["atomLinks"]})
        # A single conformer may choose a shape at an unsigned center. Check
        # only stereochemistry actually specified in the molecular identity.
        shape = Chem.MolFromMolBlock(p["molfile"], removeHs=False)
        for atom in shape.GetAtoms(): atom.SetAtomMapNum(0)
        Chem.AssignStereochemistryFrom3D(shape, replaceExistingTags=True)
        rdCIPLabeler.AssignCIPLabels(shape)
        links = {a["mapId"]: a["index"] for a in p["atomLinks"]}
        for center in r["information"]["stereochemistry"]["product"]["chiralCenters"]:
            if center["specified"]:
                self.assertEqual(shape.GetAtomWithIdx(links[center["atomMap"]]).GetProp("_CIPCode"), center["assignment"])
        self.assertIsNone(r["information"]["carbocationModel"]["racemizationRatio"])
        self.assertEqual(r["reasoning"]["label"], "Possible")
        return d

    def check_mechanism(self, d, r):
        m = d["mechanism"]
        self.assertEqual(m["type"], "SN1")
        c, x, o, base, h = (m["roles"][k] for k in ("electrophilic-carbon", "leaving-group", "nucleophile", "proton-transfer-base", "transferred-proton"))
        steps = m["steps"]
        self.assertEqual([s["title"] for s in steps], ["Ionization", "Nucleophilic capture", "Proton transfer"])
        self.assertFalse(any(s["concerted"] for s in steps))
        self.assertEqual([s["intermediate"] is not None for s in steps], [True, True, False])
        expected_moves = [
            [({"type": "bond", "atomMaps": [c, x]}, {"type": "atom", "atomMaps": [x]})],
            [({"type": "lone-pair", "atomMaps": [o]}, {"type": "atom", "atomMaps": [c]})],
            [({"type": "lone-pair", "atomMaps": [base]}, {"type": "atom", "atomMaps": [h]}),
             ({"type": "bond", "atomMaps": [o, h]}, {"type": "atom", "atomMaps": [o]})]]
        for index, step in enumerate(steps):
            self.assertEqual([(e["source"], e["destination"]) for e in step["electronMoves"]], expected_moves[index])
            before, after = parse_state(step["beforeState"]), parse_state(step["state"])
            self.assertEqual({k: a.GetAtomicNum() for k, a in atoms(before).items()}, {k: a.GetAtomicNum() for k, a in atoms(after).items()})
            self.assertEqual(sum(a.GetFormalCharge() for a in after.GetAtoms()), 0)
            self.assertEqual(atoms(after)[c].GetChiralTag(), Chem.ChiralType.CHI_UNSPECIFIED)
            self.assertEqual(atoms(after)[x].GetFormalCharge(), -1)
            if index == 0:
                self.assertEqual((atoms(after)[c].GetFormalCharge(), atoms(after)[c].GetDegree(), atoms(after)[c].GetHybridization()), (1, 3, Chem.HybridizationType.SP2))
                self.assertNotIn(o, {n.GetAtomMapNum() for n in atoms(after)[c].GetNeighbors()})
                self.assertFalse(step["protonTransfers"])
            elif index == 1:
                self.assertEqual((atoms(after)[c].GetFormalCharge(), atoms(after)[o].GetFormalCharge(), atoms(after)[o].GetDegree()), (0, 1, 3))
                self.assertFalse(step["protonTransfers"])
            else:
                self.assertEqual((atoms(after)[o].GetFormalCharge(), atoms(after)[base].GetFormalCharge(), atoms(after)[base].GetDegree()), (0, 1, 3))
                self.assertEqual({frozenset(e["atomMaps"]) for e in step["protonTransfers"]}, {frozenset((o, h)), frozenset((base, h))})
                self.assertEqual(atoms(after)[h].GetNeighbors()[0].GetAtomMapNum(), base)
                main = next(f for f in Chem.GetMolFrags(after, asMols=True) if c in atoms(f))
                self.assertEqual(_identity(main), r["productSmiles"])
                identities = {_identity(f) for f in Chem.GetMolFrags(after, asMols=True)}
                self.assertTrue({"[OH3+]", f"[{atoms(after)[x].GetSymbol()}-]"} <= identities)
        self.assertEqual(m["energyProfile"]["intermediates"], 2)
        self.assertIsNone(m["energyProfile"]["activationEnergies"])

    def check(self, substrate, products, count=1):
        ref, options, result = self.options(substrate)
        self.assertEqual(len(options), count, result["unsupportedReasons"])
        self.assertEqual({r["productSmiles"] for r in options}, {canonical(p) for p in products})
        for r in options: self.check_option(ref, r, r["productSmiles"])
        return options

    def reject(self, substrate, reason):
        _, opts, result = self.options(substrate)
        self.assertFalse(opts)
        self.assertRegex(" ".join(result["unsupportedReasons"]), reason)

    def test_tertiary_long_branched_and_existing_leaving_groups(self):
        for x in ("Cl", "Br", "I"):
            for a, p in [(f"CCCCCC({x})(C)CC", "CCCCCC(O)(C)CC"), (f"CC(C)CCC({x})(C)C", "CC(C)CCC(O)(C)C")]:
                with self.subTest(substrate=a): self.check(a, [p])

    def test_primary_secondary_and_tertiary_benzylic(self):
        for a, p in [("BrCc1ccccc1", "OCc1ccccc1"), ("CCC(Cl)c1ccccc1", "CCC(O)c1ccccc1"),
                     ("CC(Br)(C)c1ccccc1", "CC(O)(C)c1ccccc1"), ("CC(I)c1ccc(C)cc1", "CC(O)c1ccc(C)cc1")]:
            with self.subTest(substrate=a): self.check(a, [p])

    def test_symmetric_allylic_net_only_and_central_alkyl_variations(self):
        for a, p in [("C=CCBr", "C=CCO"), ("C=C(C)CCl", "C=C(C)CO"), ("C=C(CC)CI", "C=C(CC)CO")]:
            with self.subTest(substrate=a):
                r = self.check(a, [p])[0]
                self.assertEqual(r["information"]["carbocationModel"]["basis"], "symmetric allylic resonance")
                self.assertIn("same constitution", next(x["explanation"] for x in r["compatibility"]["groups"] if x["type"] == "alkene"))

    def test_ordinary_primary_methyl_and_unscreened_secondary_are_not_enabled(self):
        for a in ("CBr", "CCCl", "CCCCCCI", "CCCC(Br)C", "CC[C@H](Br)CCC"):
            with self.subTest(substrate=a): self.reject(a, "Ordinary primary/methyl and secondary")

    def test_unequal_allylic_vinylic_aryl_and_propargylic_stay_excluded(self):
        for a in ("CC=CCBr", "C=CC(Br)C", "C=CC(Br)(C)C", "BrC=C", "Brc1ccccc1", "C#CCBr"):
            with self.subTest(substrate=a): self.reject(a, "allylic|carbocation|alkyne|unsaturation")

    def test_distant_primary_secondary_oh_screened_as_bounded(self):
        for a, p in [("OCCCCCCC(Br)(C)C", "OCCCCCCC(O)(C)C"), ("CC(O)CCCCCCC(Br)(C)C", "CC(O)CCCCCCC(O)(C)C")]:
            with self.subTest(substrate=a):
                r = self.check(a, [p])[0]
                self.assertEqual(next(g["disposition"] for g in r["compatibility"]["groups"] if g["type"] == "alcohol"), "preserved")

    def test_distant_dialkyl_and_aryl_alkyl_ethers(self):
        for a, p in [("COCCCCCCC(Br)(C)C", "COCCCCCCC(O)(C)C"), ("c1ccccc1OCCCCCCC(Br)(C)C", "c1ccccc1OCCCCCCC(O)(C)C")]:
            with self.subTest(substrate=a): self.check(a, [p])

    def test_small_oxygen_capture_paths_rejected_with_exact_explanations(self):
        for n in (3, 4, 5, 6):
            for prefix in ("O", "CO"):
                a = prefix + "C" * (n - 1) + "C(Br)(C)C"
                # O → center n bonds, prospective closure n+1 members.
                if n <= 5: self.reject(a, f"{n+1}-membered intramolecular")
        self.reject("COCCCC(Br)(C)C", "5-membered intramolecular")  # fixed A177 retained

    def test_direct_vicinal_oxygen_not_treated_as_remote(self):
        for a in ("COC(Br)(C)C", "CC(O)C(Br)(C)C", "COCC(Br)(C)C"):
            self.reject(a, "heteroatom|Geminal|Direct/vicinal|oxocarbenium|shift")

    def test_acid_sensitive_remote_alcohols_are_not_spectators(self):
        for a in ("CC(O)(C)CCCCCCC(Br)(C)C", "c1ccccc1C(O)CCCCCCC(Br)(C)C", "CC(O)(O)CCCCCCC(Br)(C)C"):
            self.reject(a, "acid-sensitive|geminal|Geminal")

    def test_acid_sensitive_ether_acetal_and_benzyl_ends_rejected(self):
        for a in ("CC(C)(C)OCCCCCCC(Br)(C)C", "c1ccccc1COCCCCCCC(Br)(C)C", "COC(OC)CCCCCCC(Br)(C)C"):
            self.reject(a, "acid-driven|acetal|ketal")

    def test_ring_bound_and_bridgehead_carbocations_rejected(self):
        for a in ("CC1(Br)CCCCC1", "BrC1CCCCC1", "BrC12CCC(CC1)CC2"):
            self.reject(a, "Ring-bound|bridgehead")

    def test_adjacent_branched_carbon_shifts_are_not_invented(self):
        for a in ("CC(C)C(Br)(C)C", "CC(C)(C)C(Br)(C)C", "CC(Br)(C)CC1CCCCC1"):
            if a == "CC(Br)(C)CC1CCCCC1":
                self.check(a, ["CC(O)(C)CC1CCCCC1"])
            else: self.reject(a, "hydride/alkyl shifts")

    def test_adjacent_cyclic_and_benzylic_shift_risks_rejected(self):
        self.reject("CC(Br)(C)C1CCCCC1", "ring migration/expansion")
        self.reject("CC(Br)(C)Cc1ccccc1", "benzylic cation after a shift")

    def test_competing_groups_and_elements_fail_closed(self):
        for a in ("NCCCCCC(Br)(C)C", "SCCCCCC(Br)(C)C", "FCCCCCC(Br)(C)C", "O=CCCCCC(Br)(C)C",
                  "C=CCCCCC(Br)(C)C", "BrC(C)(C)CCCc1ccncc1", "Clc1ccc(C(Br)(C)C)cc1", "OOCCCCCCC(Br)(C)C"):
            self.reject(a, "unsupported|Unsupported|additional|Additional|compatibility|unsaturation|heteroaromatic|Heteroaromatic|element|outside")

    def test_distant_configuration_physical_retention_and_reassigned_cip(self):
        for a, p in [("CC[C@H](C)CCC(Br)(C)C", "CC[C@H](C)CCC(O)(C)C"),
                     ("CC[C@@H](C)COCCCCCC(Br)(C)C", "CC[C@@H](C)COCCCCCC(O)(C)C")]:
            self.check(a, [p])

    def test_both_specified_reacting_enantiomers_lose_configuration(self):
        for a in ("C[C@H](Br)c1ccccc1", "C[C@@H](Br)c1ccccc1", "Br[C@H](C)c1ccccc1"):
            r = self.check(a, ["CC(O)c1ccccc1"])[0]
            center = next(c for c in r["information"]["stereochemistry"]["product"]["chiralCenters"] if c["atomMap"] == r["site"]["atomMaps"][0])
            self.assertEqual((center["specified"], center["assignment"]), (False, None))

    def test_unchanged_physical_configuration_can_change_cip_letter(self):
        # Br-bearing arm initially outranks the remote Cl-bearing arm. O
        # replacing Br reverses those priorities, without physical inversion.
        r = self.check("CCC[C@H](CCCCl)CCC(Br)(C)C", ["CCC[C@H](CCCCl)CCC(O)(C)C"])[0]
        info = r["information"]["stereochemistry"]
        old = next(c for c in info["reactant"]["chiralCenters"] if c["specified"])
        new = next(c for c in info["product"]["chiralCenters"] if c["atomMap"] == old["atomMap"])
        self.assertEqual((old["assignment"], new["assignment"]), ("R", "S"))
        self.assertTrue(new["specified"])

    def test_local_loss_and_remote_retention_in_same_molecule(self):
        a = "CC[C@H](C)COCCCCCC[C@H](Br)c1ccccc1"
        self.check(a, ["CC[C@H](C)COCCCCCCC(O)c1ccccc1"])

    def test_unsigned_and_nonstereogenic_products_get_no_invented_tags(self):
        for a, p in [("CC(Br)c1ccccc1", "CC(O)c1ccccc1"), ("CC(Br)(C)C", "CC(O)(C)C")]:
            r = self.check(a, [p])[0]
            self.assertFalse(any(c["specified"] for c in r["information"]["stereochemistry"]["product"]["chiralCenters"]))

    def test_multiple_eligible_sites_remain_separately_selectable(self):
        options = self.check("CC(Br)(C)CCCC(Cl)(C)CC", ["CC(O)(C)CCCC(Cl)(C)CC", "CC(Br)(C)CCCC(O)(C)CC"], 2)
        self.assertEqual(len({r["site"]["siteId"] for r in options}), 2)
        for r in options:
            self.assertTrue(any(g["disposition"] == "alternative-site" for g in r["compatibility"]["groups"]))

    def test_separated_primary_halide_is_not_granted_sn1_permission(self):
        self.check("BrCCCCCC(Cl)(C)C", ["BrCCCCCC(O)(C)C"])

    def test_nearby_and_unvalidated_additional_halides_rejected(self):
        for a in ("CC(Br)(C)CC(Br)(C)C", "CC(Br)(C)CCCC(Br)C", "CC(Br)(Cl)C"):
            self.reject(a, "multiple halides|additional halide|Geminal")

    def test_water_is_an_actual_graph_not_a_name_and_no_new_nucleophiles(self):
        for b in ("hydroxide", "sodium-hydroxide", {"name": "Water", "smiles": "[OH-]"}, {"name": "Water", "smiles": "CO"}):
            self.assertFalse(self.options("CC(Br)(C)C", b)[1])
        for b in ({"smiles": "[O-]C"}, {"smiles": "[NH2-]"}):
            with self.assertRaises(service.ChemistryError): self.options("CC(Br)(C)C", b)
        _, options, result = self.options("CC(Br)(C)C", {"smiles": "CO"})
        self.assertFalse(options)
        self.assertIn("alcohol trapping", " ".join(result["unsupportedReasons"]))

    def test_missing_and_incompatible_conditions_are_not_experimental_protocols(self):
        for conditions, expected in [({}, "incomplete"), ({"solvent": "polar-aprotic", "temperature": "heated"}, "alternative"), (CONDITIONS, "aligned")]:
            _, opts, _ = self.options("CC(Br)(C)C", conditions=conditions)
            self.assertEqual(opts[0]["assessment"]["state"], expected)
            self.assertEqual(opts[0]["reasoning"]["label"], {"alternative": "Reference differs", "incomplete": "Conditions incomplete", "aligned": "Possible"}[expected])
            self.assertIn("not a", opts[0]["reasoning"]["note"])

    def test_reverse_inputs_actual_water_and_source_map_numbers(self):
        a = {"smiles": "[CH3:77][C:5]([Br:99])([CH3:2])[CH3:17]"}
        b = {"name": "not the identity", "smiles": "[OH2:53]"}
        forward = next(r for r in service.match_reactions(a, b, CONDITIONS)["reactions"] if r["mechanism"] == "SN1")
        reverse = next(r for r in service.match_reactions(b, a, CONDITIONS)["reactions"] if r["mechanism"] == "SN1")
        self.assertEqual(reverse["productSmiles"], canonical("CC(O)(C)C"))
        self.assertEqual(service.reaction_diagram(forward["id"], a, b, CONDITIONS)["svg"], service.reaction_diagram(reverse["id"], b, a, CONDITIONS)["svg"])
        self.assertAlmostEqual(reverse["stoichiometry"]["reactants"][0]["molarMass"], 18.015)

    def test_size_electronic_disconnected_and_enhanced_stereo_fail_closed(self):
        for a in ("not-smiles", "CC(Br)(C)(C)C", "BrC(C)(C)CCC[O-]", "BrC(C)(C)CC[CH2]", "BrC(C)(C)CC[13CH2]C", "CC(Br)(C)C.O",
                  "C[C@H](Br)c1ccccc1 |&1:1|"):
            with self.assertRaises(service.ChemistryError): self.options(a)
        # Explicit-atom cap is unchanged (80 substrate+incoming O atoms).
        self.assertTrue(self.options("C" * 22 + "C(Br)(C)C")[1])
        self.reject("C" * 23 + "C(Br)(C)C", "80|size|atom")

    def test_enhanced_stereo_guard_also_applies_to_reversed_public_input(self):
        a = {"smiles": "C[C@H](Br)c1ccccc1 |&1:1|"}
        with self.assertRaises(service.ChemistryError): service.match_reactions("water", a)

    def valid_edit(self, smiles="CC[C@H](C)CCC(Br)(C)C"):
        a, b, _ = mapped(smiles); site = rule.sites(a["mol"])[0]
        before = _combine([a, b]); after = _combine([{"mol": m} for m in engine.transform("SN1", [a, b], site)])
        return a, b, site, before, after

    def test_exact_net_contract_and_atom_order_independent_serialization(self):
        for smiles in ("CC[C@H](C)CCC(Br)(C)C", "C[C@H](Br)c1ccccc1", "C=CCBr"):
            a, b, site, before, after = self.valid_edit(smiles)
            rule.validate(before, after, a["mol"], b["mol"], site)
            rule.validate(before, Chem.RenumberAtoms(after, list(reversed(range(after.GetNumAtoms())))), a["mol"], b["mol"], site)
            if "@" in smiles and "c1" in smiles:
                with self.assertRaises(ValueError): compatibility.validate_edit_contract(before, after, rule.edit_contract(a["mol"], b["mol"], site))

    def test_changed_distant_configuration_charge_bond_or_map_fails(self):
        a, b, site, before, after = self.valid_edit()
        wrongs = []
        for change in ("invert", "erase"):
            m = Chem.Mol(after); center = next(x for x in m.GetAtoms() if x.GetChiralTag() in stereo.TETRAHEDRAL)
            center.InvertChirality() if change == "invert" else center.SetChiralTag(Chem.ChiralType.CHI_UNSPECIFIED); wrongs.append(m)
        m = Chem.Mol(after); next(x for x in m.GetAtoms() if x.GetAtomicNum() == 35).SetFormalCharge(-1); wrongs.append(m)
        m = Chem.Mol(after); m.GetBondWithIdx(0).SetBondType(Chem.BondType.DOUBLE); wrongs.append(m)
        m = Chem.Mol(after); m.GetAtomWithIdx(0).SetAtomMapNum(999); wrongs.append(m)
        for m in wrongs:
            with self.assertRaises(ValueError): rule.validate(before, m, a["mol"], b["mol"], site)

    def test_invented_product_rs_fails_even_with_net_permission(self):
        a, b, site, before, after = self.valid_edit("C[C@H](Br)c1ccccc1")
        s = rule.participants(a["mol"], b["mol"], site)
        for tag in stereo.TETRAHEDRAL:
            wrong = Chem.Mol(after); atoms(wrong)[s["center"]].SetChiralTag(tag)
            with self.assertRaises(ValueError): rule.validate(before, wrong, a["mol"], b["mol"], site)

    def test_wrong_permissions_cannot_erase_distant_stereo(self):
        a, b, site, before, after = self.valid_edit(); spec = rule.participants(a["mol"], b["mol"], site)
        for field, value in [("center", 3), ("center", True), ("center", 999), ("hydrogen", spec["incoming"]), ("stage", "unknown")]:
            wrong = {**spec, field: value}
            with self.assertRaises(ValueError): compatibility.validate_edit_contract(before, after, rule.edit_contract(a["mol"], b["mol"], site), solvolyses=[wrong])
        with self.assertRaises(ValueError): stereo.validate_retained_stereo(before, after, solvolyses=[spec, spec])

    def test_invalid_actual_water_electronic_graphs_fail(self):
        a, b, _ = mapped("CC(Br)(C)C"); site = rule.sites(a["mol"])[0]
        for change in (lambda m: m.GetAtomWithIdx(0).SetFormalCharge(-1), lambda m: m.GetAtomWithIdx(1).SetIsotope(2),
                       lambda m: m.GetAtomWithIdx(0).SetNumRadicalElectrons(1)):
            wrong = Chem.Mol(b["mol"]); change(wrong)
            with self.assertRaises(ValueError): rule.participants(a["mol"], wrong, site)

    def test_unknown_groups_and_wrong_sites_fail_closed(self):
        molecule = Chem.MolFromSmiles("CC(Br)(C)C")
        for site in ((), (0, 1), (True, 2), (1, 999), (1, 2, 3)):
            self.assertFalse(rule.assess(molecule, site)["eligible"])
        self.assertEqual(rule.group_check(molecule, (1, 2), {"type": "unknown", "atomIndices": [0]})[0], "rejected")

    def test_net_validation_failure_cannot_publish_candidate(self):
        with patch.object(rule, "validate", side_effect=ValueError("Independent SN1 validation blocked")):
            _, opts, result = self.options("CC(Br)(C)C")
        self.assertFalse(opts)
        self.assertIn("Independent SN1 validation blocked", " ".join(result["unsupportedReasons"]))

    def test_every_mechanism_stage_runs_same_contract(self):
        from server import reaction_mechanisms
        a = {"smiles": "C[C@H](Br)c1ccccc1"}
        ids, custom, _ = service._resolve_reactants(a, "water"); catalog = {**service.REACTANTS, **custom}
        generated, _ = engine.generate_pair(*ids, catalog, conditions=CONDITIONS)
        r = next(r for r in generated.values() if r["mechanism"] == "SN1")
        with patch.object(rule, "validate", wraps=rule.validate) as checked:
            reaction_mechanisms.build_mechanism(r, catalog)
        self.assertEqual([c.args[5] for c in checked.call_args_list], ["ionization", "capture", "deprotonation"])
        for stage in ("ionization", "capture", "deprotonation"):
            original = rule.validate
            def fail(*args, **kwargs):
                if len(args) > 5 and args[5] == stage: raise ValueError("Independent stage blocked")
                return original(*args, **kwargs)
            with patch.object(rule, "validate", side_effect=fail), self.assertRaises(ValueError): reaction_mechanisms.build_mechanism(r, catalog)

    def test_corrupt_elementary_charges_and_stereo_fail(self):
        ref, opts, _ = self.options("CC[C@H](C)COCCCCCC[C@H](Br)c1ccccc1")
        d = service.reaction_diagram(opts[0]["id"], ref, "water", CONDITIONS)
        a, b, solvent = mapped(ref["smiles"]); site = rule.sites(a["mol"])[0]
        for step, stage in zip(d["mechanism"]["steps"], ("ionization", "capture", "deprotonation")):
            before, after = parse_state(step["beforeState"]), parse_state(step["state"])
            rule.validate(before, after, a["mol"], b["mol"], site, stage, solvent["mol"])
            wrong = Chem.Mol(after); c = a["mol"].GetAtomWithIdx(site[0]).GetAtomMapNum()
            atoms(wrong)[c].SetChiralTag(Chem.ChiralType.CHI_TETRAHEDRAL_CW)
            with self.assertRaises(ValueError): rule.validate(before, wrong, a["mol"], b["mol"], site, stage, solvent["mol"])
            wrong = Chem.Mol(after); next(x for x in wrong.GetAtoms() if x.GetAtomicNum() == 35).SetFormalCharge(0)
            with self.assertRaises(ValueError): rule.validate(before, wrong, a["mol"], b["mol"], site, stage, solvent["mol"])

    def test_wrong_proton_destination_is_not_permitted(self):
        a, b, site, before, after = self.valid_edit(); spec = rule.participants(a["mol"], b["mol"], site)
        from server.reaction_diagrams import _remove, _add
        wrong = Chem.RWMol(after); _remove(wrong, spec["leaving"], spec["hydrogen"])
        remote = next(x.GetAtomMapNum() for x in wrong.GetAtoms() if x.GetAtomicNum() == 6 and x.GetAtomMapNum() != spec["center"])
        _add(wrong, remote, spec["hydrogen"])
        with self.assertRaises(ValueError): rule.validate(before, wrong.GetMol(), a["mol"], b["mol"], site)

    def test_extra_contract_edits_or_charge_permissions_cannot_bypass_sn1(self):
        a, b, site, before, after = self.valid_edit("C[C@H](Br)c1ccccc1")
        s = rule.participants(a["mol"], b["mol"], site)
        with self.assertRaises(ValueError):
            compatibility.validate_edit_contract(before, after, rule.edit_contract(a["mol"], b["mol"], site),
                                                 charge_changes=[{"atomMap": s["center"], "before": 0, "after": 1}], solvolyses=[s])
        with self.assertRaises(ValueError):
            compatibility.validate_edit_contract(before, after, rule.edit_contract(a["mol"], b["mol"], site), solvolyses=[{**s, "stage": "capture"}])

    def test_wrong_solvent_proton_acceptor_cannot_receive_stage_permission(self):
        ref, opts, _ = self.options("C[C@H](Br)c1ccccc1")
        step = service.reaction_diagram(opts[0]["id"], ref, "water", CONDITIONS)["mechanism"]["steps"][-1]
        a, b, solvent = mapped(ref["smiles"]); site = rule.sites(a["mol"])[0]
        wrong = Chem.Mol(solvent["mol"]); next(x for x in wrong.GetAtoms() if x.GetAtomicNum() == 8).SetFormalCharge(-1)
        with self.assertRaises(ValueError): rule.validate(parse_state(step["beforeState"]), parse_state(step["state"]), a["mol"], b["mol"], site, "deprotonation", wrong)

    def test_carbonyl_and_acid_groups_are_not_retained_by_solvolysis_guess(self):
        for a in ("OC(=O)CCCCCCC(Br)(C)C", "COC(=O)CCCCCCC(Br)(C)C", "CC(=O)CCCCCCC(Br)(C)C"):
            self.reject(a, "additional|compatibility")

    def test_other_pathway_boundaries_stay_independent(self):
        for smiles, reagent, expected in [("C=CCBr", "hydroxide", set()), ("CC[C@H](Br)CCC", "water", set()),
                                         ("COCCCCCCC(Br)(C)C", "water", {"SN1", "E1"}), ("COCCCBr", "hydroxide", {"SN2", "E2"})]:
            self.assertEqual({r["mechanism"] for r in service.match_reactions({"smiles": smiles}, reagent)["reactions"]}, expected)
        ref, options, result = self.options("C[C@H](Br)c1ccccc1")
        self.assertEqual({r["mechanism"] for r in result["reactions"]}, {"SN1", "E1"})  # E1 now has its own planar-center contract; SN1 unchanged.

    def test_authenticated_actual_public_match_diagram_and_run(self):
        from server.production_app import create_app
        origin = "https://sn1-increment.example.test"
        app = create_app({"TRIAL_PASSWORD": "SN1-synthetic-test-password", "SESSION_SECRET": "580e43a1eef3796298cb4c2b373097cad1c416f8c6a8fb9be900d970ec6d18fd", "PUBLIC_ORIGIN": origin,
                          "FRAME_ANCESTORS": "https://site.example.test", "DIST_DIR": "/private/tmp/sn1-no-static-needed", "TESTING": True}, chemistry_backend=service)
        client = app.test_client()
        self.assertEqual(client.post("/login", base_url=origin, headers={"Origin": origin}, data={"password": "SN1-synthetic-test-password"}).status_code, 303)
        for smiles in ("COCCCCCCC(Br)(C)C", "C[C@H](Br)c1ccccc1", "C=CCBr", "CC(Br)(C)CCCC(Cl)(C)CC"):
            body = {"reactantA": {"smiles": smiles}, "reactantB": "water", "conditions": CONDITIONS}
            response = client.post("/api/reactions/match", base_url=origin, headers={"Origin": origin}, json=body)
            self.assertEqual(response.status_code, 200)
            options = [r for r in response.get_json()["reactions"] if r["mechanism"] == "SN1"]
            self.assertTrue(options)
            for r in options:
                body["reactionId"] = r["id"]
                d = client.post("/api/reactions/diagram", base_url=origin, headers={"Origin": origin}, json=body)
                run = client.post("/api/reactions/run", base_url=origin, headers={"Origin": origin}, json=body)
                self.assertEqual((d.status_code, run.status_code), (200, 200))
                self.assertEqual(d.get_json()["products"][0]["smiles"], run.get_json()["product"]["smiles"])


if __name__ == "__main__":
    unittest.main()

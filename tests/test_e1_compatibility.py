"""Independent E1 products, exact two-stage contracts and spectator stereo."""
import unittest
from unittest.mock import patch
from rdkit import Chem
from rdkit.Chem import Descriptors, rdMolDescriptors, rdCIPLabeler
from server import chemistry_server as service, e1_rule as rule, stereochemistry as stereo
from server import reaction_engine as engine, reaction_compatibility as compatibility
from server.reaction_diagrams import _species, _combine, _identity

CONDITIONS = {"solvent": "aqueous-protic", "temperature": "heated"}


def canonical(smiles):
    return Chem.MolToSmiles(Chem.MolFromSmiles(smiles))


def atoms(mol):
    return {a.GetAtomMapNum(): a for a in mol.GetAtoms()}


def parse_state(state):
    params = Chem.SmilesParserParams(); params.removeHs = False
    return Chem.MolFromSmiles(state["mappedSmiles"], params)


def mapped(smiles):
    a, n = _species("substrate", {"name": "Independent E1 structure", "smiles": smiles}, 1)
    solvent, _ = _species("solvent", {"name": "Solvent water", "smiles": "O"}, n)
    return a, solvent


class E1CompatibilityTests(unittest.TestCase):
    def options(self, smiles, reagent="water", conditions=CONDITIONS):
        ref = {"name": "Independent E1 test input", "smiles": smiles}
        result = service.match_reactions(ref, reagent, conditions)
        return ref, [r for r in result["reactions"] if r["mechanism"] == "E1"], result

    def check_option(self, ref, r, expected):
        expected = canonical(expected)
        self.assertEqual(r["productSmiles"], expected)
        self.assertEqual(r["productFormula"], rdMolDescriptors.CalcMolFormula(Chem.MolFromSmiles(expected)))
        data = r["stoichiometry"]
        self.assertTrue(data["balanced"])
        self.assertEqual([(x["inputSlot"], x["coefficient"]) for x in data["reactants"]], [(0, 1)])
        self.assertEqual(data["product"]["coefficient"], 1)
        self.assertAlmostEqual(data["product"]["molarMass"], Descriptors.MolWt(Chem.MolFromSmiles(expected)), places=6)
        self.assertEqual(data["excludedInputs"], [{"inputSlot": 1, "name": "Water", "reason": "Solvent / medium; not consumed in this net equation."}])
        self.assertTrue(any("hydronium" in n for n in data["notes"]))
        d = service.reaction_diagram(r["id"], ref, "water", CONDITIONS)
        self.assertTrue(d["highlightsAvailable"])
        self.assertEqual(d["products"][0]["smiles"], expected)
        source = {a["mapId"]: (a["element"], a["formalCharge"]) for a in d["atoms"] if a["side"] == "reactants"}
        target = {a["mapId"]: (a["element"], a["formalCharge"]) for a in d["atoms"] if a["side"] == "products"}
        self.assertEqual(source, target)  # neutral simplified alkene + HX net reporting
        report = r["compatibility"]
        self.assertEqual(report["policy"], "water E1 elimination")
        self.assertTrue(report["eligible"])
        self.assertEqual(set(report["validation"].values()), {"verified"})
        self.assertEqual(report["substrateSiteMaps"], r["site"]["atomMaps"])
        s = report["e1Eliminations"][0]
        alpha, beta, h, x = (s[k] for k in ("alpha", "beta", "hydrogen", "leaving"))
        self.assertEqual(source[h][0], "H")
        self.assertEqual(r["site"]["parameters"]["betaHydrogenMap"], h)
        self.assertIn(h, r["site"]["parameters"]["betaHydrogenMaps"])
        self.assertEqual({frozenset(e["atomMaps"]) for e in d["bondsBroken"]}, {frozenset((alpha, x)), frozenset((beta, h))})
        self.assertEqual({frozenset(e["atomMaps"]) for e in d["bondsFormed"]}, {frozenset((x, h))})
        self.assertEqual(len(d["bondOrderChanges"]), 1)
        self.assertEqual(set(d["bondOrderChanges"][0]["atomMaps"]), {alpha, beta})
        self.assertEqual(d["products"][1]["smiles"], source[x][0])
        self.assertEqual(set(report["reactiveAtomMaps"]), {alpha, beta, h, x})
        self.assertEqual({(frozenset(e["atomMaps"]), e["before"], e["after"]) for e in report["editContract"]},
                         {(frozenset(e["atomMaps"]), e["before"], e["after"]) for e in d["changes"]})
        self.check_mechanism(d, r)
        p = service.run_curated_reaction(r["id"], ref, "water", CONDITIONS)["product"]
        self.assertEqual((p["smiles"], p["representation"]), (expected, "3d"))
        rows = [a for a in d["atoms"] if a["side"] == "products" and a["speciesIndex"] == 0]
        self.assertEqual([(a["atomIndex"], a["mapId"], a["element"]) for a in rows], [(a["index"], a["mapId"], a["element"]) for a in p["atomLinks"]])
        self.assertTrue({alpha, beta} <= {a["mapId"] for a in p["atomLinks"]})
        self.assertFalse({x, h} & {a["mapId"] for a in p["atomLinks"]})
        shape = Chem.MolFromMolBlock(p["molfile"], removeHs=False)
        for atom in shape.GetAtoms(): atom.SetAtomMapNum(0)
        Chem.AssignStereochemistryFrom3D(shape, replaceExistingTags=True)
        rdCIPLabeler.AssignCIPLabels(shape)
        links = {a["mapId"]: a["index"] for a in p["atomLinks"]}
        for center in r["information"]["stereochemistry"]["product"]["chiralCenters"]:
            if center["specified"]:
                self.assertEqual(shape.GetAtomWithIdx(links[center["atomMap"]]).GetProp("_CIPCode"), center["assignment"])
        self.assertFalse(any(a["specified"] for a in r["information"]["stereochemistry"]["product"]["alkenes"]))
        self.assertIsNone(r["information"]["carbocationModel"]["stereoisomerRatio"])
        self.assertEqual(r["reasoning"]["label"], "Possible")
        return d

    def check_mechanism(self, d, r):
        m = d["mechanism"]; roles = m["roles"]
        a, b, h, x, base = (roles[k] for k in ("alpha-carbon", "beta-carbon", "beta-hydrogen", "leaving-group", "base"))
        self.assertEqual(m["type"], "E1")
        steps = m["steps"]
        self.assertEqual([s["title"] for s in steps], ["Ionization", "Elimination"])
        # Beta C–H loss and pi formation are coupled within the SECOND step,
        # not concerted with leaving-group departure as in E2.
        self.assertEqual([s["concerted"] for s in steps], [False, True])
        self.assertEqual([s["intermediate"] is not None for s in steps], [True, False])
        expected_moves = [[({"type": "bond", "atomMaps": [a, x]}, {"type": "atom", "atomMaps": [x]})],
                          [({"type": "lone-pair", "atomMaps": [base]}, {"type": "atom", "atomMaps": [h]}),
                           ({"type": "bond", "atomMaps": [b, h]}, {"type": "bond", "atomMaps": [b, a]})]]
        for index, step in enumerate(steps):
            self.assertEqual([(e["source"], e["destination"]) for e in step["electronMoves"]], expected_moves[index])
            before, after = parse_state(step["beforeState"]), parse_state(step["state"])
            self.assertEqual({k: v.GetAtomicNum() for k, v in atoms(before).items()}, {k: v.GetAtomicNum() for k, v in atoms(after).items()})
            self.assertEqual(sum(v.GetFormalCharge() for v in after.GetAtoms()), 0)
            self.assertEqual(atoms(after)[a].GetChiralTag(), Chem.ChiralType.CHI_UNSPECIFIED)
            self.assertEqual(atoms(after)[x].GetFormalCharge(), -1)
            if index == 0:
                self.assertEqual((atoms(after)[a].GetFormalCharge(), atoms(after)[a].GetDegree(), atoms(after)[a].GetHybridization()), (1, 3, Chem.HybridizationType.SP2))
                self.assertEqual(atoms(after)[b].GetHybridization(), Chem.HybridizationType.SP3)
                self.assertEqual(after.GetBondBetweenAtoms(atoms(after)[a].GetIdx(), atoms(after)[b].GetIdx()).GetBondType(), Chem.BondType.SINGLE)
                self.assertIn(h, {v.GetAtomMapNum() for v in atoms(after)[b].GetNeighbors()})
                self.assertFalse(step["protonTransfers"])
            else:
                self.assertEqual((atoms(after)[a].GetFormalCharge(), atoms(after)[base].GetFormalCharge(), atoms(after)[base].GetDegree()), (0, 1, 3))
                bond = after.GetBondBetweenAtoms(atoms(after)[a].GetIdx(), atoms(after)[b].GetIdx())
                self.assertEqual((bond.GetBondType(), bond.GetStereo()), (Chem.BondType.DOUBLE, Chem.BondStereo.STEREONONE))
                self.assertEqual({frozenset(e["atomMaps"]) for e in step["protonTransfers"]}, {frozenset((b, h)), frozenset((base, h))})
                self.assertEqual(atoms(after)[h].GetNeighbors()[0].GetAtomMapNum(), base)
                main = next(f for f in Chem.GetMolFrags(after, asMols=True) if a in atoms(f))
                self.assertEqual(_identity(main), r["productSmiles"])
                self.assertTrue({"[OH3+]", f"[{atoms(after)[x].GetSymbol()}-]"} <= {_identity(f) for f in Chem.GetMolFrags(after, asMols=True)})
        self.assertEqual(m["energyProfile"]["intermediates"], 1)
        self.assertIsNone(m["energyProfile"]["activationEnergies"])

    def check(self, substrate, products, count=None):
        ref, options, result = self.options(substrate)
        self.assertTrue(options, result["unsupportedReasons"])
        if count is not None: self.assertEqual(len(options), count, result["unsupportedReasons"])
        self.assertEqual({r["productSmiles"] for r in options}, {canonical(p) for p in products})
        for r in options: self.check_option(ref, r, r["productSmiles"])
        return options

    def reject(self, substrate, reason):
        _, opts, result = self.options(substrate)
        self.assertFalse(opts)
        self.assertRegex(" ".join(result["unsupportedReasons"]), reason)

    def test_long_tertiary_and_existing_halogen_families(self):
        for x in ("Cl", "Br", "I"):
            self.check(f"CCCCCC({x})(C)C", ["CCCCC=C(C)C", "C=C(C)CCCCC"], 2)

    def test_screened_branching_not_adjacent_shift_risk(self):
        self.check("CC(C)CCC(Br)(C)C", ["CC(C)CC=C(C)C", "C=C(C)CCC(C)C"], 2)

    def test_distinct_beta_positions_give_three_constitutional_products(self):
        self.check("CCCC(Br)(C)CC", ["CCC=C(C)CC", "CC=C(C)CCC", "C=C(CC)CCC"], 3)

    def test_equivalent_beta_positions_do_not_duplicate_products(self):
        self.check("CC(Br)(C)C", ["C=C(C)C"], 1)
        self.check("CCC(Br)(CC)CC", ["CC=C(CC)CC"], 1)

    def test_secondary_isopropyl_and_secbutyl_are_bounded_not_blanket(self):
        self.check("CC(Cl)C", ["C=CC"], 1)
        self.check("CCC(Br)C", ["C=CCC", "CC=CC"], 2)
        self.check("C[C@H](I)CC", ["C=CCC", "CC=CC"], 2)
        for a in ("CCCC(Br)C", "CCC(Br)CC", "CC[C@H](Br)CCC"):
            self.reject(a, "secondary aliphatic sites are assessed individually")

    def test_benzylic_secondary_and_tertiary_options(self):
        self.check("CC(Br)c1ccccc1", ["C=Cc1ccccc1"], 1)
        self.check("CCC(Cl)c1ccccc1", ["CC=Cc1ccccc1"], 1)
        self.check("CCC(Br)(C)c1ccccc1", ["CC=C(C)c1ccccc1", "C=C(CC)c1ccccc1"], 2)

    def test_narrow_allylic_secondary_tertiary_and_beta_variants(self):
        self.check("C=C(C)C(Br)C", ["C=C(C)C=C"], 1)
        self.check("C=C(C)C(Cl)(C)C", ["C=C(C)C(=C)C"], 1)
        options = self.check("C=C(CC)C(Br)(C)CC", ["C=C(CC)C(=C)CC", "C=C(CC)C(C)=CC"], 2)
        self.assertTrue(all(r["information"]["carbocationModel"]["basis"] == "bounded allylic resonance" for r in options))

    def test_allylic_cumulene_or_unequal_terminal_routes_remain_excluded(self):
        for a in ("C=CCBr", "C=CC(Br)C", "C=CC(Br)(C)C", "CC=CC(Br)(C)C", "C=C(c1ccccc1)C(Br)(C)C"):
            self.reject(a, "secondary|allylic|saturated beta|cumulated|cumule")

    def test_remote_ordinary_ethers_and_alcohols_preserved_with_limits(self):
        for a, products in [("COCCCCCCC(Br)(C)C", ["COCCCCCC=C(C)C", "C=C(C)CCCCCCOC"]),
                            ("OCCCCCCC(Br)(C)C", ["OCCCCCC=C(C)C", "C=C(C)CCCCCCO"]),
                            ("CC(O)CCCCCCC(Br)(C)C", ["CC(O)CCCCCC=C(C)C", "CC(O)CCCCCCC(C)=C"])]:
            self.check(a, products, 2)

    def test_remote_aryl_alkyl_ether_and_carbon_skeleton(self):
        self.check("c1ccccc1OCCCCCCC(Br)(C)C", ["c1ccccc1OCCCCCC=C(C)C", "c1ccccc1OCCCCCCC(C)=C"], 2)

    def test_near_oxygen_and_fixed_a197_remain_excluded(self):
        for a in ("COCCC(Br)(C)C", "OCCC(Br)(C)C", "COCCCC(Br)(C)C", "OCCCCC(Br)(C)C"):
            self.reject(a, "intramolecular|oxygen-to-carbocation|capture")

    def test_direct_vicinal_heteroatom_and_beta_coupling_rejected(self):
        for a in ("COC(Br)(C)C", "COCC(Br)(C)C", "CC(O)C(Br)(C)C", "CC(Br)(Cl)C"):
            self.reject(a, "Geminal|Direct/vicinal|beta|shift")

    def test_acid_sensitive_remote_alcohols_not_assumed_inert(self):
        for a in ("CC(O)(C)CCCCCCC(Br)(C)C", "c1ccccc1C(O)CCCCCCC(Br)(C)C", "CC(O)(O)CCCCCCC(Br)(C)C"):
            self.reject(a, "Acid-sensitive|acid-sensitive|geminal")

    def test_acid_sensitive_ethers_and_acetals_rejected(self):
        for a in ("CC(C)(C)OCCCCCCC(Br)(C)C", "c1ccccc1COCCCCCCC(Br)(C)C", "COC(OC)CCCCCCC(Br)(C)C"):
            self.reject(a, "Acid-sensitive|acetal|cleavage")

    def test_distant_configuration_retention_and_backwards_smiles_parity(self):
        self.check("CC[C@H](C)CCC(Br)(C)C", ["CC[C@H](C)CC=C(C)C", "CC[C@H](C)CCC(C)=C"], 2)
        self.check("CC[C@@H](C)COCCCCCCC(Br)(C)C", ["CC[C@@H](C)COCCCCCC=C(C)C", "CC[C@@H](C)COCCCCCCC(C)=C"], 2)

    def test_retained_physical_center_can_change_its_cip_letter(self):
        options = self.check("CCC[C@H](CCCCl)CCC(Br)(C)C", ["CCC[C@H](CCCCl)CC=C(C)C", "CCC[C@H](CCCCl)CCC(C)=C"], 2)
        for r in options:
            info = r["information"]["stereochemistry"]
            old = next(c for c in info["reactant"]["chiralCenters"] if c["specified"])
            new = next(c for c in info["product"]["chiralCenters"] if c["atomMap"] == old["atomMap"])
            self.assertEqual(old["assignment"], "R")
            # Internal beta elimination changes a nearer CIP comparison and
            # retains R; terminal elimination removes Br's remote priority and
            # gives S. Both retain the independently specified physical parity.
            expected = "R" if r["productSmiles"] == canonical("CCC[C@H](CCCCl)CC=C(C)C") else "S"
            self.assertEqual(new["assignment"], expected)
        self.assertEqual({r["information"]["stereochemistry"]["product"]["chiralCenters"][0]["assignment"] for r in options}, {"R", "S"})

    def test_specified_reacting_benzylic_centers_are_lost_not_inverted(self):
        for a in ("C[C@H](Br)c1ccccc1", "C[C@@H](Br)c1ccccc1"):
            r = self.check(a, ["C=Cc1ccccc1"], 1)[0]
            self.assertFalse(r["information"]["stereochemistry"]["product"]["chiralCenters"])

    def test_local_loss_distant_retention_and_ether_together(self):
        a = "CC[C@H](C)COCCCCCC[C@H](Br)c1ccccc1"
        self.check(a, ["CC[C@H](C)COCCCCCC= Cc1ccccc1".replace(" ", "")], 1)

    def test_new_ez_unassigned_even_from_specified_alpha(self):
        for a in ("CC[C@H](Br)c1ccccc1", "CC[C@@H](Br)c1ccccc1"):
            r = self.check(a, ["CC=Cc1ccccc1"], 1)[0]
            self.assertEqual(len(r["information"]["stereochemistry"]["product"]["alkenes"]), 1)
            self.assertEqual(r["information"]["stereochemistry"]["product"]["alkenes"][0]["assignment"], None)

    def test_multiple_halide_identities_stay_distinct_after_beta_dedup(self):
        options = self.check("CC(Br)(C)CCC(Br)(C)C", ["C=C(C)CCC(Br)(C)C", "CC(C)=CCC(Br)(C)C"], 4)
        self.assertEqual(len({r["site"]["siteId"] for r in options}), 4)
        self.assertEqual(len({tuple(r["site"]["atomMaps"][:2]) for r in options}), 2)

    def test_distinct_halides_and_primary_spectator(self):
        self.check("BrCCCCCC(Cl)(C)C", ["BrCCCCC=C(C)C", "BrCCCCCC(C)=C"], 2)

    def test_source_map_labels_cannot_split_equivalent_beta_sites(self):
        for a in ("CCC(Br)(C)C", "[CH3:77][CH2:2][C:9]([Br:33])([CH3:16])[CH3:3]"):
            self.check(a, ["CC=C(C)C", "C=C(C)CC"], 2)
            source, _ = mapped(a)
            self.assertEqual(len(rule.sites(source["mol"])), 2)
            self.assertEqual(len(rule.sites(Chem.RenumberAtoms(source["mol"], list(reversed(range(source["mol"].GetNumAtoms())))))), 2)

    def test_no_actual_beta_h_and_aromatic_beta_are_not_eliminated(self):
        for a in ("CBr", "BrCc1ccccc1", "BrC(c1ccccc1)(c1ccccc1)c1ccccc1", "CC(C)(C)C(Br)C(C)(C)C"):
            self.reject(a, "beta|primary|shift")

    def test_primary_neopentyl_vinyl_aryl_and_propargyl_controls(self):
        for a in ("CCBr", "CCCCCl", "CC(C)(C)CBr", "BrC=C", "Brc1ccccc1", "C#CCBr"):
            self.reject(a, "primary|carbocation|sp³|shift|alkyne")

    def test_cyclic_ring_bound_and_adjacent_ring_cases_rejected(self):
        for a in ("CC1(Br)CCCCC1", "BrC1CCCCC1", "CC(Br)(C)C1CCCCC1", "BrC12CCC(CC1)CC2"):
            self.reject(a, "Ring-bound|cyclic|bridgehead")

    def test_rearrangement_prone_branch_and_benzylic_destination_rejected(self):
        for a in ("CC(C)C(Br)(C)C", "CC(C)(C)C(Br)(C)C", "CC(Br)(C)Cc1ccccc1"):
            self.reject(a, "shift|benzylic cation")

    def test_unsupported_groups_elements_and_multiple_halides_rejected(self):
        for a in ("NCCCCCC(Br)(C)C", "SCCCCCC(Br)(C)C", "FCCCCCC(Br)(C)C", "O=CCCCCC(Br)(C)C",
                  "OC(=O)CCCCCC(Br)(C)C", "C=CCCCCC(Br)(C)C", "BrC(C)(C)CCCc1ccncc1", "CC(Br)(C)CC(Br)(C)C"):
            self.reject(a, "outside|additional|Additional|capture|multiple halides|Heteroaromatic|unsaturation")

    def test_water_graph_required_and_no_other_base_family(self):
        for b in ("hydroxide", "sodium-hydroxide", {"name": "Water", "smiles": "[OH-]"}, {"name": "Water", "smiles": "CO"}):
            self.assertFalse(self.options("CC(Br)(C)C", b)[1])
        self.assertIn("actual solvent water", " ".join(self.options("CC(Br)(C)C", {"smiles": "CO"})[2]["unsupportedReasons"]))
        for b in ({"smiles": "[O-]C"}, {"smiles": "[NH2-]"}):
            with self.assertRaises(service.ChemistryError): self.options("CC(Br)(C)C", b)

    def test_conditions_qualitative_and_invalid_selectors_rejected(self):
        for conditions, state in [({}, "incomplete"), ({"solvent": "polar-aprotic", "temperature": "ambient"}, "alternative"), (CONDITIONS, "aligned")]:
            _, opts, _ = self.options("CC(Br)(C)C", conditions=conditions)
            self.assertEqual(opts[0]["assessment"]["state"], state)
            self.assertEqual(opts[0]["reasoning"]["label"], {"alternative": "Reference differs", "incomplete": "Conditions incomplete", "aligned": "Possible"}[state])
        with self.assertRaises(service.ChemistryError): self.options("CC(Br)(C)C", conditions={"solvent": "imaginary"})

    def test_reverse_inputs_preserve_diagram_and_exclude_water_slot(self):
        a = {"smiles": "[CH3:77][CH2:2][C:9]([Br:33])([CH3:16])[CH3:3]"}
        for reverse in (False, True):
            first, second = ("water", a) if reverse else (a, "water")
            result = service.match_reactions(first, second, CONDITIONS)
            opts = [r for r in result["reactions"] if r["mechanism"] == "E1"]
            self.assertEqual(len(opts), 2)
            for r in opts:
                self.assertEqual(r["stoichiometry"]["reactants"][0]["inputSlot"], 1 if reverse else 0)
                self.assertEqual(r["stoichiometry"]["excludedInputs"][0]["inputSlot"], 0 if reverse else 1)
                self.assertTrue(service.reaction_diagram(r["id"], first, second, CONDITIONS)["mechanism"])

    def test_size_and_invalid_electronic_or_enhanced_stereo_fail_closed(self):
        for a in ("not-smiles", "CC(Br)(C)(C)C", "BrC(C)(C)CCC[O-]", "BrC(C)(C)CC[CH2]", "BrC(C)(C)CC[13CH2]C", "CC(Br)(C)C.O", "C[C@H](Br)c1ccccc1 |&1:1|"):
            with self.assertRaises(service.ChemistryError): self.options(a)
        self.assertEqual(len(self.options("C" * 23 + "C(Br)(C)C")[1]), 2)
        self.reject("C" * 24 + "C(Br)(C)C", "80|size|atom")

    def valid_edit(self, smiles="CC[C@H](C)CCC(Br)(C)C", index=0):
        a, _ = mapped(smiles); site = rule.sites(a["mol"])[index]
        before = Chem.Mol(a["mol"]); after = _combine([{"mol": m} for m in engine.transform("E1", [a], site)])
        return a, site, before, after

    def test_exact_net_contract_survives_renumbering_and_serialization(self):
        for source in ("CC[C@H](C)CCC(Br)(C)C", "C[C@H](Br)c1ccccc1", "C=C(C)C(Br)(C)C"):
            a, site, before, after = self.valid_edit(source)
            rule.validate(before, after, a["mol"], site)
            rule.validate(before, Chem.RenumberAtoms(after, list(reversed(range(after.GetNumAtoms())))), a["mol"], site)

    def test_remote_inversion_loss_charge_map_or_bond_corruption_fails(self):
        a, site, before, after = self.valid_edit()
        wrongs = []
        for change in ("invert", "erase"):
            m = Chem.Mol(after); center = next(v for v in m.GetAtoms() if v.GetChiralTag() in stereo.TETRAHEDRAL)
            center.InvertChirality() if change == "invert" else center.SetChiralTag(Chem.ChiralType.CHI_UNSPECIFIED); wrongs.append(m)
        m = Chem.Mol(after); next(v for v in m.GetAtoms() if v.GetAtomicNum() == 35).SetFormalCharge(-1); wrongs.append(m)
        m = Chem.Mol(after); m.GetAtomWithIdx(0).SetAtomMapNum(999); wrongs.append(m)
        m = Chem.Mol(after); m.GetBondWithIdx(0).SetBondType(Chem.BondType.DOUBLE); wrongs.append(m)
        for m in wrongs:
            with self.assertRaises(ValueError): rule.validate(before, m, a["mol"], site)

    def test_invented_alpha_tags_or_alkene_ez_fail(self):
        a, site, before, after = self.valid_edit("CCC(Br)C", 0)
        s = rule.participants(a["mol"], site)
        wrong = Chem.Mol(after); atoms(wrong)[s["alpha"]].SetChiralTag(Chem.ChiralType.CHI_TETRAHEDRAL_CW)
        with self.assertRaises(ValueError): rule.validate(before, wrong, a["mol"], site)
        for index in range(len(rule.sites(a["mol"]))):
            a, site, before, after = self.valid_edit("CCC(Br)C", index)
            s = rule.participants(a["mol"], site); wrong = Chem.Mol(after)
            bond = wrong.GetBondBetweenAtoms(atoms(wrong)[s["alpha"]].GetIdx(), atoms(wrong)[s["beta"]].GetIdx())
            refs = [next(n.GetIdx() for n in c.GetNeighbors() if n.GetIdx() != other.GetIdx()) for c, other in ((bond.GetBeginAtom(), bond.GetEndAtom()), (bond.GetEndAtom(), bond.GetBeginAtom()))]
            bond.SetStereoAtoms(*refs); bond.SetStereo(Chem.BondStereo.STEREOTRANS)
            with self.assertRaises(ValueError): rule.validate(before, wrong, a["mol"], site)

    def test_invalid_stage_or_distant_center_permissions_cannot_bypass_validation(self):
        a, site, before, after = self.valid_edit(); s = rule.participants(a["mol"], site)
        for field, value in (("alpha", 3), ("alpha", True), ("alpha", 999), ("stage", "unknown"), ("hydrogen", s["beta"])):
            wrong = {**s, field: value}
            with self.assertRaises(ValueError): compatibility.validate_edit_contract(before, after, rule.stage_edits(s), e1_eliminations=[wrong])
        with self.assertRaises(ValueError): stereo.validate_retained_stereo(before, after, e1_eliminations=[s, s])

    def test_net_validation_failure_cannot_publish_candidate(self):
        with patch.object(rule, "validate", side_effect=ValueError("Independent E1 validator blocked")):
            _, opts, result = self.options("CC(Br)(C)C")
        self.assertFalse(opts)
        self.assertIn("Independent E1 validator blocked", " ".join(result["unsupportedReasons"]))

    def test_both_mechanism_stages_pass_the_same_contract(self):
        from server import reaction_mechanisms
        ref = {"smiles": "C[C@H](Br)c1ccccc1"}
        ids, custom, _ = service._resolve_reactants(ref, "water"); catalog = {**service.REACTANTS, **custom}
        generated, _ = engine.generate_pair(*ids, catalog, conditions=CONDITIONS)
        r = next(r for r in generated.values() if r["mechanism"] == "E1")
        with patch.object(rule, "validate", wraps=rule.validate) as checked: reaction_mechanisms.build_mechanism(r, catalog)
        self.assertEqual([c.args[4] for c in checked.call_args_list], ["ionization", "elimination"])
        for stage in ("ionization", "elimination"):
            original = rule.validate
            def fail(*args, **kwargs):
                if len(args) > 4 and args[4] == stage: raise ValueError("Independent stage blocked")
                return original(*args, **kwargs)
            with patch.object(rule, "validate", side_effect=fail), self.assertRaises(ValueError): reaction_mechanisms.build_mechanism(r, catalog)

    def test_elementary_cation_charge_and_tetra_tag_corruption_fail(self):
        ref, opts, _ = self.options("C[C@H](Br)c1ccccc1")
        d = service.reaction_diagram(opts[0]["id"], ref, "water", CONDITIONS)
        a, solvent = mapped(ref["smiles"]); site = rule.sites(a["mol"])[0]
        for step, stage in zip(d["mechanism"]["steps"], ("ionization", "elimination")):
            before, after = parse_state(step["beforeState"]), parse_state(step["state"])
            rule.validate(before, after, a["mol"], site, stage, solvent["mol"])
            s = rule.participants(a["mol"], site, stage, solvent["mol"])
            wrong = Chem.Mol(after); atoms(wrong)[s["alpha"]].SetChiralTag(Chem.ChiralType.CHI_TETRAHEDRAL_CW)
            with self.assertRaises(ValueError): rule.validate(before, wrong, a["mol"], site, stage, solvent["mol"])
            wrong = Chem.Mol(after); atoms(wrong)[s["leaving"]].SetFormalCharge(0)
            with self.assertRaises(ValueError): rule.validate(before, wrong, a["mol"], site, stage, solvent["mol"])

    def test_wrong_base_graph_and_missing_hydrogen_fail_closed(self):
        a, solvent = mapped("CC(Br)(C)C"); site = rule.sites(a["mol"])[0]
        for mutate in (lambda m: m.GetAtomWithIdx(0).SetFormalCharge(-1), lambda m: m.GetAtomWithIdx(1).SetIsotope(2), lambda m: m.GetAtomWithIdx(0).SetNumRadicalElectrons(1)):
            wrong = Chem.Mol(solvent["mol"]); mutate(wrong)
            with self.assertRaises(ValueError): rule.participants(a["mol"], site, "ionization", wrong)
        with self.assertRaises(ValueError): rule.participants(a["mol"], site, "ionization")

    def test_wrong_proton_destination_and_concerted_stage_permission_fail(self):
        from server.reaction_diagrams import _remove, _add
        a, site, before, after = self.valid_edit(); s = rule.participants(a["mol"], site)
        wrong = Chem.RWMol(after); _remove(wrong, s["leaving"], s["hydrogen"])
        remote = next(v.GetAtomMapNum() for v in wrong.GetAtoms() if v.GetAtomicNum() == 6 and v.GetAtomMapNum() not in {s["alpha"], s["beta"]})
        _add(wrong, remote, s["hydrogen"])
        with self.assertRaises(ValueError): rule.validate(before, wrong.GetMol(), a["mol"], site)
        # The overall net edit cannot masquerade as a single elementary
        # ionization: beta-H cleavage and double formation must be later.
        with self.assertRaises(ValueError):
            compatibility.validate_edit_contract(before, after, rule.stage_edits(s), e1_eliminations=[{**s, "stage": "ionization"}])

    def test_wrong_sites_unknown_groups_and_no_preset_dependency(self):
        mol = Chem.MolFromSmiles("CC(Br)(C)C")
        for site in ((), (1, 2), (True, 2, 0), (1, 2, 999), (1, 1, 0)):
            self.assertFalse(rule.assess(mol, site)["eligible"])
        self.assertEqual(rule.group_check(mol, (1, 2), {"type": "unknown", "atomIndices": [0]})[0], "rejected")
        with patch.dict(service.REACTIONS, {}, clear=True): self.check("COCCCCCCC(Br)(C)C", ["COCCCCCC=C(C)C", "C=C(C)CCCCCCOC"], 2)

    def test_sn1_sn2_e2_permissions_and_examples_stay_independent(self):
        self.assertTrue(any(r["mechanism"] == "SN1" for r in self.options("CCC(Br)C")[2]["reactions"]))  # Independently screened secondary water capture now shares the cation assessment.
        self.assertFalse(any(r["mechanism"] == "SN1" for r in self.options("C=C(C)C(Br)(C)C")[2]["reactions"]))
        for a in ("C=CCBr", "C=C(C)C(Br)(C)C"):
            self.assertFalse(any(r["mechanism"] in {"SN2", "E2"} for r in service.match_reactions({"smiles": a}, "hydroxide")["reactions"]))
        self.assertEqual({r["mechanism"] for r in service.match_reactions("tert-butyl-chloride", "water")["reactions"]}, {"SN1", "E1"})

    def test_authenticated_public_match_diagram_run_and_rejected_control(self):
        from server.production_app import create_app
        origin = "https://e1-increment.example.test"
        app = create_app({"TRIAL_PASSWORD": "E1-synthetic-test-password", "SESSION_SECRET": "580e43a1eef3796298cb4c2b373097cad1c416f8c6a8fb9be900d970ec6d18fd", "PUBLIC_ORIGIN": origin,
                          "FRAME_ANCESTORS": "https://site.example.test", "DIST_DIR": "/private/tmp/e1-no-static-needed", "TESTING": True}, chemistry_backend=service)
        client = app.test_client()
        self.assertEqual(client.post("/login", base_url=origin, headers={"Origin": origin}, data={"password": "E1-synthetic-test-password"}).status_code, 303)
        for smiles in ("COCCCCCCC(Br)(C)C", "C[C@H](Br)c1ccccc1", "C=C(C)C(Br)(C)C", "CCC(Br)C"):
            body = {"reactantA": {"smiles": smiles}, "reactantB": "water", "conditions": CONDITIONS}
            response = client.post("/api/reactions/match", base_url=origin, headers={"Origin": origin}, json=body)
            self.assertEqual(response.status_code, 200)
            opts = [r for r in response.get_json()["reactions"] if r["mechanism"] == "E1"]
            self.assertTrue(opts)
            for r in opts:
                body["reactionId"] = r["id"]
                d = client.post("/api/reactions/diagram", base_url=origin, headers={"Origin": origin}, json=body)
                p = client.post("/api/reactions/run", base_url=origin, headers={"Origin": origin}, json=body)
                self.assertEqual((d.status_code, p.status_code), (200, 200))
                self.assertEqual(d.get_json()["products"][0]["smiles"], p.get_json()["product"]["smiles"])
        negative = client.post("/api/reactions/match", base_url=origin, headers={"Origin": origin},
                               json={"reactantA": {"smiles": "COCCC(Br)(C)C"}, "reactantB": "water", "conditions": CONDITIONS})
        self.assertEqual(negative.status_code, 200)
        self.assertFalse(any(r["mechanism"] == "E1" for r in negative.get_json()["reactions"]))
        self.assertIn("4-membered", " ".join(negative.get_json()["unsupportedReasons"]))


if __name__ == "__main__": unittest.main()

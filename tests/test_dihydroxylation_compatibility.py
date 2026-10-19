"""Independent Phase 3F products, parity/CIP, conservation and failure controls."""
import unittest
from unittest.mock import patch
from rdkit import Chem
from server import chemistry_server as service, dihydroxylation_rule as rule
from server.reaction_diagrams import _species, _combine, _finish

CONDITIONS = {"catalyst": "osmium", "workup": "aqueous-release"}
def canonical(s, stereo=True): return Chem.MolToSmiles(Chem.MolFromSmiles(s), isomericSmiles=stereo)
def cips(r):
    return tuple(c["assignment"] for c in sorted(r["stereochemistry"]["product"]["chiralCenters"], key=lambda c:c["atomMap"])
                 if c["atomMap"] in r["site"]["atomMaps"])


class DihydroxylationCompatibilityTests(unittest.TestCase):
    def options(self, source, conditions=None, reagent="hydrogen-peroxide"):
        ref = {"smiles": source, "name": "Independent diol test substrate"}
        reagent = reagent if not isinstance(reagent,str) or reagent in service.REACTANTS else {"smiles":reagent}
        response = service.match_reactions(ref, reagent, CONDITIONS if conditions is None else conditions)
        return ref, [r for r in response["reactions"] if r["mechanism"] == "Alkene dihydroxylation"], response

    def check(self, source, expected, count):
        ref, rs, response = self.options(source)
        self.assertEqual(len(rs), count, response["unsupportedReasons"])
        self.assertEqual({canonical(r["productSmiles"], False) for r in rs}, {canonical(s, False) for s in expected})
        self.assertEqual(len({r["productSmiles"] for r in rs}), count)
        for r in rs:
            self.assertTrue(r["assessment"]["canRun"]); self.assertFalse(r["assessment"]["workupRepresented"])
            self.assertTrue(r["stoichiometry"]["balanced"]); self.assertFalse(r["byproducts"])
            self.assertIsNone(r["dihydroxylationStereo"]["ratios"])
            self.assertEqual(r["information"]["capabilities"]["mappedMechanism"], "unsupported")
            d = service.reaction_diagram(r["id"], ref, "hydrogen-peroxide", CONDITIONS)
            self.assertIsNone(d["mechanism"]); self.assertEqual(len(d["products"]), 1)
            self.assertIn("adds syn OH",d["summary"])
            self.assertNotIn("stereo remains unassigned",d["svg"])
            self.assertTrue(d["highlightsAvailable"])
            before = [a for a in d["atoms"] if a["side"] == "reactants"]
            after = [a for a in d["atoms"] if a["side"] == "products"]
            identity = lambda rows: {a["mapId"]:(a["element"], a["formalCharge"]) for a in rows}
            self.assertEqual(identity(before), identity(after)); self.assertEqual(len(identity(before)), len(before))
            p = r["site"]["parameters"]; a,b = p["alkene"]; o1,o2 = p["oxygens"]
            origins = {a["mapId"]:a for a in before}
            for o in p["oxygens"]: self.assertEqual((origins[o]["element"], origins[o]["speciesIndex"]), ("O", 1))
            for h in p["hydroxylHydrogens"]: self.assertEqual((origins[h]["element"], origins[h]["speciesIndex"]), ("H", 1))
            edits = lambda rows: {(frozenset(e["atomMaps"]), e["before"], e["after"]) for e in rows}
            expected_edits = {(frozenset((a,b)),2,1), (frozenset((o1,o2)),1,None), (frozenset((a,o1)),None,1), (frozenset((b,o2)),None,1)}
            self.assertEqual(edits(d["changes"]), expected_edits)
            self.assertEqual(edits(r["compatibility"]["editContract"]), expected_edits)
            self.assertEqual((len(d["bondsFormed"]),len(d["bondsBroken"]),len(d["bondOrderChanges"])), (2,1,1))
            model = service.run_curated_reaction(r["id"],ref,"hydrogen-peroxide",CONDITIONS)["product"]
            self.assertEqual(model["representation"],"3d"); self.assertEqual(model["smiles"], r["productSmiles"])
            self.assertEqual([(v["atomIndex"],v["mapId"],v["element"]) for v in after], [(v["index"],v["mapId"],v["element"]) for v in model["atomLinks"]])
            coordinates = Chem.MolFromMolBlock(model["molfile"],removeHs=False)
            indices = {v["mapId"]:v["index"] for v in model["atomLinks"]}
            for o,h in zip(p["oxygens"],p["hydroxylHydrogens"]):
                self.assertEqual(coordinates.GetBondBetweenAtoms(indices[o],indices[h]).GetBondTypeAsDouble(),1)
            for atom in coordinates.GetAtoms(): atom.SetAtomMapNum(0)
            Chem.AssignStereochemistryFrom3D(coordinates,replaceExistingTags=True)
            Chem.AssignStereochemistry(coordinates,cleanIt=True,force=True); Chem.AssignCIPLabels(coordinates)
            indices = {v["mapId"]:v["index"] for v in model["atomLinks"]}
            for c in r["stereochemistry"]["product"]["chiralCenters"]:
                if c["specified"]:
                    atom = coordinates.GetAtomWithIdx(indices[c["atomMap"]])
                    self.assertTrue(atom.HasProp("_CIPCode")); self.assertEqual(atom.GetProp("_CIPCode"),c["assignment"])
        return rs

    def reject(self, source, reason):
        _,rs,response = self.options(source)
        self.assertFalse(rs); self.assertIn(reason," ".join(response["unsupportedReasons"]))

    def test_ethene_achiral(self): self.assertEqual(self.check("C=C",["OCCO"],1)[0]["dihydroxylationStereo"]["assignedAtomMaps"],[])
    def test_propene_both_faces(self): self.assertEqual({cips(r) for r in self.check("C=CC",["CC(O)CO"],2)},{("R",),("S",)})
    def test_long_terminal(self): self.check("C=CCCCCCCCCCC",["CCCCCCCCCCC(O)CO"],2)
    def test_branched_terminal(self): self.check("C=C(C)CCC",["CCCC(C)(O)CO"],2)
    def test_tertiary_carbon_not_a_carbocation_rearrangement(self): self.check("C=CC(C)(C)C",["CC(C)(C)C(O)CO"],2)
    def test_identical_terminal_substituents_achiral(self): self.check("C=C(C)C",["CC(C)(O)CO"],1)
    def test_tetrasubstituted_achiral(self): self.check("CC(C)=C(C)C",["CC(C)(O)C(C)(C)O"],1)
    def test_single_center_no_possible_ez(self): self.assertEqual({cips(r) for r in self.check("CC(C)=CC",["CC(O)C(C)(C)O"],2)},{("R",),("S",)})
    def test_e_2_butene_independent_rr_ss(self): self.assertEqual({cips(r) for r in self.check("C/C=C/C",["CC(O)C(O)C"],2)},{("R","R"),("S","S")})
    def test_z_2_butene_independent_meso(self): self.assertEqual({cips(r) for r in self.check("C/C=C\\C",["CC(O)C(O)C"],1)},{("R","S")})
    def test_e_3_hexene_rr_ss(self): self.assertEqual({cips(r) for r in self.check("CC/C=C/CC",["CCC(O)C(O)CC"],2)},{("R","R"),("S","S")})
    def test_z_3_hexene_meso(self): self.assertEqual({cips(r) for r in self.check("CC/C=C\\CC",["CCC(O)C(O)CC"],1)},{("R","S")})
    def test_unsymmetrical_e_both_faces(self): self.assertEqual({cips(r) for r in self.check("C/C=C/CCC",["CC(O)C(O)CCC"],2)},{("R","R"),("S","S")})
    def test_unsymmetrical_z_not_meso(self): self.assertEqual({cips(r) for r in self.check("C/C=C\\CCC",["CC(O)C(O)CCC"],2)},{("R","S"),("S","R")})
    def test_unknown_internal_unsigned(self): self.assertEqual(cips(self.check("CC=CCCC",["CC(O)C(O)CCC"],1)[0]),(None,None))
    def test_unknown_tetrasubstituted_unsigned(self): self.assertEqual(cips(self.check("CCC(C)=C(C)CC",["CCC(C)(O)C(C)(O)CC"],1)[0]),(None,None))
    def test_cyclopentene_cis(self): self.assertEqual(self.check("C1=CCCC1",["OC1C(O)CCC1"],1)[0]["dihydroxylationStereo"]["hydroxylRelationship"],"cis")
    def test_cyclohexene_cis_meso_rs(self): self.assertEqual({cips(r) for r in self.check("C1=CCCCC1",["OC1C(O)CCCC1"],1)},{("R","S")})
    def test_cycloheptene_cis(self): self.check("C1=CCCCCC1",["OC1C(O)CCCCC1"],1)
    def test_unsymmetrical_ring_both_faces(self): self.check("CC1=CCCCC1",["CC1(O)C(O)CCCC1"],2)
    def test_styrene(self): self.check("C=Cc1ccccc1",["OCC(O)c1ccccc1"],2)
    def test_e_stilbene(self): self.assertEqual({cips(r) for r in self.check("c1ccccc1/C=C/c1ccccc1",["OC(c1ccccc1)C(O)c1ccccc1"],2)},{("R","R"),("S","S")})
    def test_z_stilbene_meso(self): self.check("c1ccccc1/C=C\\c1ccccc1",["OC(c1ccccc1)C(O)c1ccccc1"],1)
    def test_remote_alcohol(self): self.check("C=CCCCO",["OCCCC(O)CO"],2)
    def test_remote_ether(self): self.check("C=CCCCOC",["COCCCC(O)CO"],2)
    def test_two_remote_alcohols(self): self.check("C=CCCCC(CO)CO",["OCC(CO)CCCC(O)CO"],2)
    def test_distant_center_physical_retention(self): self.check("C=CC[C@H](C)CC",["CC[C@H](C)CC(O)CO"],2)
    def test_distant_center_opposite_configuration(self): self.check("C=CC[C@@H](C)CC",["CC[C@@H](C)CC(O)CO"],2)
    def test_distant_and_new_centers_are_diastereomeric_not_racemic_claim(self):
        rs = self.check("C/C=C/CC[C@H](C)CC",["CC(O)C(O)CC[C@H](C)CC"],2)
        self.assertTrue(all(r["dihydroxylationStereo"]["ratios"] is None for r in rs))
    def test_equivalent_diene_sites_grouped_not_lost(self):
        rs = self.check("C=CCCCCC=C",["C=CCCCCC(O)CO"],2)
        self.assertTrue(all(len(r["site"]["parameters"]["equivalentSiteFaces"]) == 2 for r in rs))
    def test_distinct_diene_sites_preserved(self):
        rs = self.check("C=CCCCCC=CC",["CC=CCCCCC(O)CO","C=CCCCCC(O)C(O)C"],3)
        self.assertEqual(len({tuple(r["site"]["atomMaps"]) for r in rs}),2)
    def test_unselected_ez_retained(self): self.check("C=CCCCCC/C=C/CC",["CC/C=C/CCCCCC(O)CO","C=CCCCCCC(O)C(O)CC"],4)

    def test_conjugated_rejected(self): self.reject("C=CC=C","Conjugated")
    def test_cumulated_rejected(self): self.reject("C=C=C","Conjugated")
    def test_direct_enol_rejected(self): self.reject("C=C(O)C","Direct heteroatom")
    def test_near_alcohol_directing_rejected(self): self.reject("C=CCCO","Near-site")
    def test_allyl_alcohol_rejected(self): self.reject("C=CCO","Activated")
    def test_near_ether_rejected(self): self.reject("C=CCOC","Activated")
    def test_tertiary_oh_competition(self): self.reject("C=CCCCCC(O)(C)C","Activated")
    def test_acetal_rejected(self): self.reject("C=CCCCCC(OC)OC","acid-sensitive")
    def test_benzylic_ether_rejected(self): self.reject("C=CCCCCOCc1ccccc1","Activated")
    def test_phenol_competing_oxidation(self): self.reject("C=Cc1ccc(O)cc1","aromatic oxidation")
    def test_carbonyl_competing(self): self.reject("C=CCCC=O","aldehyde")
    def test_ester_competing(self): self.reject("C=CCCC(=O)OC","ester")
    def test_alkyne_competing(self): self.reject("C=CCCCCC#C","alkyne")
    def test_peroxide_competing(self): self.reject("C=CCCCCOO","peroxide")
    def test_near_diene_oxidative_cyclization(self): self.reject("C=CCCC=C","oxidative-cyclization")
    def test_adjacent_specified_center(self): self.reject("C=C[C@H](C)CC","Adjacent specified")
    def test_eight_membered_ring_unvalidated(self): self.reject("C1=CCCCCCC1","5–7-membered")
    def test_fused_ring_unvalidated(self): self.reject("C1=CCC2CCCCC2C1","5–7-membered")
    def test_exocyclic_ring_unvalidated(self): self.reject("C=C1CCCCC1","Exocyclic")
    def test_saturated_control(self): self.assertFalse(self.options("CCCCC")[1])
    def test_aromatic_only_control(self): self.assertFalse(self.options("c1ccccc1")[1])
    def test_size_limit(self): self.reject("C="+"C"*29,"80 explicit atoms")
    def test_wrong_reagents_not_promoted(self):
        for reagent in ["O", "COO", "peracetic-acid", "bromine"]:
            self.assertFalse(self.options("C=CC",reagent=reagent)[1])
    def test_nmo_not_silently_enabled(self):
        with self.assertRaises(service.ChemistryError): self.options("C=CC",reagent={"smiles":"C[N+]1([O-])CCOCC1"})
    def test_kmno4_not_enabled(self):
        with self.assertRaises(service.ChemistryError): self.options("C=CC",reagent={"smiles":"[K+].[O-][Mn](=O)(=O)=O"})

    def test_missing_workup_conditional_only(self):
        ref,rs,_ = self.options("C=CC",{"catalyst":"osmium"})
        for r in rs:
            self.assertFalse(r["assessment"]["canRun"]); self.assertIn("workup",r["assessment"]["missingSettings"])
            self.assertIsNone(service.reaction_diagram(r["id"],ref,"hydrogen-peroxide",{"catalyst":"osmium"})["mechanism"])
            with self.assertRaisesRegex(service.ChemistryError,"work-up is not confirmed"):
                service.run_curated_reaction(r["id"],ref,"hydrogen-peroxide",{"catalyst":"osmium"})
    def test_water_medium_does_not_confirm_workup(self): self.assertFalse(self.options("C=CC",{"catalyst":"osmium","solvent":"aqueous-protic"})[1][0]["assessment"]["canRun"])
    def test_missing_os_activation(self):
        for catalyst in ["", "none", "acid", "metal", "radical", "lindlar"]:
            self.assertFalse(self.options("C=CC",{"catalyst":catalyst,"workup":"aqueous-release"})[1][0]["assessment"]["canRun"])
    def test_heated_oxidation_not_inferred(self): self.assertFalse(self.options("C=CC",{**CONDITIONS,"temperature":"heated"})[1][0]["assessment"]["canRun"])
    def test_confirmed_net_conditions_not_labeled_strong_prediction(self):
        self.assertEqual(self.options("C=CC")[1][0]["reasoning"]["label"],"Model conditions match")
    def test_incomplete_starting_geometry_not_silently_cleaned(self):
        self.reject("C/C=CCC","directional C=C annotation")
    def test_invalid_workup_value(self):
        with self.assertRaises(service.ChemistryError): self.options("C=CC",{**CONDITIONS,"workup":"guess"})
    def test_invalid_reagent_stereo_cannot_be_normalized_away(self):
        with self.assertRaisesRegex(service.ChemistryError,"H2O2 has no configured"):
            self.options("C=CC",reagent={"smiles":"[O@H]O"})
    def test_distant_cip_changes_without_physical_inversion(self):
        rs = self.check("C=CCC[C@H](C)CCC(C)(C)C",["CC(C)(C)CC[C@@H](C)CCC(O)CO"],2)
        for r in rs:
            old = r["stereochemistry"]["reactant"]["chiralCenters"][0]
            new = next(c for c in r["stereochemistry"]["product"]["chiralCenters"] if c["atomMap"] == old["atomMap"])
            self.assertEqual((old["assignment"],new["assignment"]),("S","R"))
    def test_source_order_and_map_labels_do_not_choose_cip(self):
        for source in ["C(=C/C)\\C", "[CH3:92]/[CH:6]=[CH:8]/[CH3:75]"]:
            self.assertEqual({cips(r) for r in self.check(source,["CC(O)C(O)C"],2)},{("R","R"),("S","S")})
    def test_reordered_product_validates_same_physical_stereo(self):
        before,after,s,r,site = self.prepared("C=CC[C@H](C)CC")
        rule.validate(before,Chem.RenumberAtoms(after,list(reversed(range(after.GetNumAtoms())))),s,r,site)
    def test_match_does_not_embed_to_assign_stereo(self):
        with patch.object(service,"analyze_molfile",side_effect=AssertionError("No conformer stereo prediction")):
            self.assertEqual(len(self.options("C/C=C/C")[1]),2)
    def test_reversed_input_slots_preserve_peroxide_identity(self):
        response = service.match_reactions("hydrogen-peroxide",{"smiles":"C/C=C/C"},CONDITIONS)
        for r in response["reactions"]:
            self.assertEqual(r["stoichiometry"]["reactants"][0]["formula"],"H2O2")
            self.assertEqual(service.run_curated_reaction(r["id"],"hydrogen-peroxide",{"smiles":"C/C=C/C"},CONDITIONS)["product"]["smiles"],r["productSmiles"])

    def prepared(self, source="C/C=C/C"):
        substrate,_ = _species("s",{"name":"test","smiles":source},1)
        reagent,_ = _species("r",{"name":"test","smiles":"OO"},substrate["mol"].GetNumAtoms()+1)
        before = _combine([substrate,reagent]); site = (*graph_site(substrate["mol"]),0)
        editor = Chem.RWMol(before); rule.edit(editor,before,substrate["mol"],reagent["mol"],site)
        return before,_finish(editor),substrate["mol"],reagent["mol"],site
    def test_tamper_syn_to_anti_rejected(self):
        before,after,s,r,site = self.prepared(); after.GetAtomWithIdx(site[0]).InvertChirality()
        with self.assertRaisesRegex(ValueError,"same-face"): rule.validate(before,after,s,r,site)
    def test_tamper_unknown_geometry_assignment_rejected(self):
        before,after,s,r,site = self.prepared("CC=CCC"); after.GetAtomWithIdx(site[0]).SetChiralTag(Chem.ChiralType.CHI_TETRAHEDRAL_CW)
        with self.assertRaisesRegex(ValueError,"cannot invent"): rule.validate(before,after,s,r,site)
    def test_tamper_distant_stereo_rejected(self):
        before,after,s,r,site = self.prepared("C=CC[C@H](C)CC")
        next(a for a in after.GetAtoms() if a.GetIdx() not in site[:2] and a.GetChiralTag()!=Chem.ChiralType.CHI_UNSPECIFIED).InvertChirality()
        with self.assertRaises(ValueError): rule.validate(before,after,s,r,site)
    def test_tamper_atom_identity_rejected(self):
        before,after,s,r,site = self.prepared(); after.GetAtomWithIdx(0).SetAtomMapNum(999)
        with self.assertRaises(ValueError): rule.validate(before,after,s,r,site)
    def test_tamper_charge_rejected(self):
        before,after,s,r,site = self.prepared(); after.GetAtomWithIdx(0).SetFormalCharge(1)
        with self.assertRaises(ValueError): rule.validate(before,after,s,r,site)
    def test_invalid_face_rejected(self):
        before,after,s,r,site = self.prepared()
        with self.assertRaises(ValueError): rule.validate(before,after,s,r,(*site[:2],2))
    def test_tamper_spectator_bond_rejected(self):
        before,after,s,r,site = self.prepared("C=CCCCCC")
        editor=Chem.RWMol(after); editor.RemoveBond(4,5)
        with self.assertRaises(ValueError): rule.validate(before,editor.GetMol(),s,r,site)


def graph_site(molecule):
    return next((b.GetBeginAtomIdx(),b.GetEndAtomIdx()) for b in molecule.GetBonds() if b.GetBondType()==Chem.BondType.DOUBLE)

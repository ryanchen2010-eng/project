"""Independent Phase 3D products, CIP/relative stereo and public graph checks.

These are tests, not visible molecule examples. No random product conformer
decides expected stereo; its coordinates only verify an already selected tag.
"""
import unittest
from unittest.mock import patch
from rdkit import Chem
from server import chemistry_server as service, chlorination_rule as rule, halogen_addition_stereo as anti
from server.reaction_diagrams import _species, _combine
from server.reaction_conditions import assess_conditions

DRY={"solvent":"dry","catalyst":"none"}
def canonical(s,stereo=True): return Chem.MolToSmiles(Chem.MolFromSmiles(s),isomericSmiles=stereo)


class ChlorinationCompatibilityTests(unittest.TestCase):
    def options(self,smiles,conditions=DRY,reagent="chlorine"):
        ref={"smiles":smiles,"name":"Independent structure"}
        response=service.match_reactions(ref,reagent,conditions)
        return ref,[r for r in response["reactions"] if r["mechanism"]=="Chlorination"],response

    def check(self,source,expected,count,conditions=DRY):
        ref,rs,response=self.options(source,conditions)
        self.assertEqual(len(rs),count,response["unsupportedReasons"])
        self.assertEqual({canonical(r["productSmiles"],False) for r in rs},{canonical(s,False) for s in expected})
        self.assertEqual(len({r["productSmiles"] for r in rs}),count)
        for r in rs:
            self.assertTrue(r["assessment"]["canRun"])
            self.assertEqual(r["byproducts"],[])
            self.assertTrue(r["stoichiometry"]["balanced"])
            self.assertEqual([v["coefficient"] for v in r["stoichiometry"]["reactants"]],[1,1])
            self.assertEqual(r["stoichiometry"]["excludedInputs"],[])
            self.assertEqual(r["stoichiometry"]["product"]["coefficient"],1)
            self.assertIsNone(r["chlorinationStereo"]["ratios"])
            d=service.reaction_diagram(r["id"],ref,"chlorine",conditions)
            self.assertIsNone(d["mechanism"])
            self.assertTrue(d["highlightsAvailable"])
            before=[a for a in d["atoms"] if a["side"]=="reactants"]
            after=[a for a in d["atoms"] if a["side"]=="products"]
            identity=lambda rows:{a["mapId"]:(a["element"],a["formalCharge"]) for a in rows}
            self.assertEqual(identity(before),identity(after));self.assertEqual(len(identity(before)),len(before))
            p=r["site"]["parameters"]
            self.assertEqual({a["mapId"] for a in before if a["speciesIndex"]==1},set(p["chlorines"]))
            self.assertEqual({a["element"] for a in before if a["speciesIndex"]==1},{"Cl"})
            self.assertEqual(len(d["bondsBroken"]),1);self.assertEqual(set(d["bondsBroken"][0]["atomMaps"]),set(p["chlorines"]))
            self.assertEqual({frozenset(v["atomMaps"]) for v in d["bondsFormed"]},
                             {frozenset(pair) for pair in zip(p["alkene"],p["chlorines"])})
            self.assertEqual(len(d["bondOrderChanges"]),1)
            self.assertEqual((d["bondOrderChanges"][0]["before"],d["bondOrderChanges"][0]["after"]),(2,1))
            contract=lambda edits:{(frozenset(v["atomMaps"]),v["before"],v["after"]) for v in edits}
            self.assertEqual(contract(d["changes"]),contract(r["compatibility"]["editContract"]))
            product=service.run_curated_reaction(r["id"],ref,"chlorine",conditions)["product"]
            self.assertEqual(product["smiles"],r["productSmiles"])
            self.assertEqual(product["representation"],"3d")
            self.assertEqual([(a["atomIndex"],a["mapId"],a["element"]) for a in after],
                             [(a["index"],a["mapId"],a["element"]) for a in product["atomLinks"]])
            coordinates=Chem.MolFromMolBlock(product["molfile"],removeHs=False)
            for a in coordinates.GetAtoms():a.SetAtomMapNum(0)
            Chem.AssignStereochemistryFrom3D(coordinates,replaceExistingTags=True)
            Chem.AssignStereochemistry(coordinates,cleanIt=True,force=True)
            Chem.AssignCIPLabels(coordinates)
            indices={a["mapId"]:a["index"] for a in product["atomLinks"]}
            for c in r["stereochemistry"]["product"]["chiralCenters"]:
                if c["specified"]:
                    a=coordinates.GetAtomWithIdx(indices[c["atomMap"]])
                    self.assertTrue(a.HasProp("_CIPCode"));self.assertEqual(a.GetProp("_CIPCode"),c["assignment"])
        return rs

    def reject(self,source,reason,conditions=DRY):
        _,rs,response=self.options(source,conditions)
        self.assertFalse(rs);self.assertIn(reason," ".join(response["unsupportedReasons"]))

    def local_cips(self,r):
        return tuple(c["assignment"] for c in sorted(r["stereochemistry"]["product"]["chiralCenters"],key=lambda c:c["atomMap"])
                     if c["atomMap"] in r["site"]["atomMaps"])

    def test_ethene_no_fabricated_centers(self):
        r=self.check("C=C",["ClCCCl"],1)[0]
        self.assertEqual(r["chlorinationStereo"]["assignedAtomMaps"],[])

    def test_propene_two_enantiomeric_alternatives(self):
        rs=self.check("C=CC",["CC(Cl)CCl"],2)
        self.assertEqual({self.local_cips(r) for r in rs},{("R",),("S",)})

    def test_long_chains_beyond_presets(self):
        self.check("C=CCCC",["ClCC(Cl)CCC"],2)
        self.check("C=CCCCCCCCCCC",["ClCC(Cl)CCCCCCCCCC"],2)

    def test_branched_terminal_single_new_center(self): self.check("C=C(C)CCC",["ClCC(Cl)(C)CCC"],2)
    def test_identical_substituents_not_chiral(self): self.check("C=C(C)C",["ClCC(Cl)(C)C"],1)

    def test_chloronium_model_does_not_copy_hx_shift_restriction(self):
        self.check("C=CC(C)C",["ClCC(Cl)C(C)C"],2)
        self.check("C=CC(C)(C)C",["ClCC(Cl)C(C)(C)C"],2)

    def test_unspecified_internal_geometry_stays_unsigned(self):
        r=self.check("CC=CCCC",["CC(Cl)C(Cl)CCC"],1)[0]
        self.assertTrue(all(not c["specified"] for c in r["stereochemistry"]["product"]["chiralCenters"]))
        self.assertIn("unknown",r["chlorinationStereo"]["outcome"])

    def test_e_butene_independent_meso_rs_expectation(self):
        rs=self.check("C/C=C/C",["CC(Cl)C(Cl)C"],1)
        self.assertEqual(set(self.local_cips(rs[0])),{"R","S"})
        self.assertEqual(len(rs[0]["site"]["parameters"]["equivalentSiteFaces"]),2)

    def test_z_butene_independent_rr_ss_expectation(self):
        rs=self.check("C/C=C\\C",["CC(Cl)C(Cl)C"],2)
        self.assertEqual({self.local_cips(r) for r in rs},{("R","R"),("S","S")})

    def test_e_and_z_hexene_relative_configurations(self):
        e=self.check("CC/C=C/CC",["CCC(Cl)C(Cl)CC"],1)
        z=self.check("CC/C=C\\CC",["CCC(Cl)C(Cl)CC"],2)
        self.assertEqual(set(self.local_cips(e[0])),{"R","S"})
        self.assertEqual({self.local_cips(r) for r in z},{("R","R"),("S","S")})

    def test_unsymmetric_e_internal_is_not_automatically_meso(self):
        rs=self.check("C/C=C/CC",["CC(Cl)C(Cl)CC"],2)
        self.assertEqual({self.local_cips(r) for r in rs},{("R","S"),("S","R")})

    def test_unsymmetric_z_internal_enantiomeric_pair(self):
        rs=self.check("C/C=C\\CC",["CC(Cl)C(Cl)CC"],2)
        self.assertEqual({self.local_cips(r) for r in rs},{("R","R"),("S","S")})

    def test_tetrasubstituted_unknown_geometry_unsigned(self): self.check("CCC(C)=C(C)CCC",["CCC(Cl)(C)C(Cl)(C)CCC"],1)

    def test_small_monocycles_trans_rr_ss_not_cis_meso(self):
        for source,product in [("C1=CCCC1","ClC1CCCC1Cl"),("C1=CCCCC1","ClC1CCCCC1Cl"),("C1=CCCCCC1","ClC1CCCCCC1Cl")]:
            rs=self.check(source,[product],2)
            self.assertEqual({self.local_cips(r) for r in rs},{("R","R"),("S","S")})
            self.assertTrue(all(r["chlorinationStereo"]["productRingRelationship"]=="trans Cl/Cl" for r in rs))

    def test_substituted_cyclic_anti_centers(self): self.check("CC1=CCCCC1",["CC1(Cl)C(Cl)CCCC1"],2)

    def test_eight_membered_unknown_geometry_not_assumed_cis(self):
        r=self.check("C1=CCCCCCC1",["ClC1CCCCCCC1Cl"],1)[0]
        self.assertIsNone(r["chlorinationStereo"]["productRingRelationship"])
        self.assertEqual(r["chlorinationStereo"]["assignedAtomMaps"],[])

    def test_valid_trans_cyclooctene_not_generically_labeled_trans_product(self):
        rs=self.check("C1CCC/C=C/CC1",["ClC1CCCCCCC1Cl"],1)
        self.assertIsNone(rs[0]["chlorinationStereo"]["productRingRelationship"])
        self.assertEqual(set(self.local_cips(rs[0])),{"R","S"})

    def test_styrene_only_one_center_no_fabricated_two_center_anti_ratio(self):
        rs=self.check("C=Cc1ccccc1",["ClCC(Cl)c1ccccc1"],2)
        self.assertEqual({self.local_cips(r) for r in rs},{("R",),("S",)})

    def test_alpha_methylstyrene_and_unactivated_ring_retention(self): self.check("C=C(C)c1ccccc1",["ClCC(Cl)(C)c1ccccc1"],2)
    def test_internal_aryl_stereo_scrambling_unvalidated(self): self.reject("C/C=C/c1ccccc1","benzylic-ion")
    def test_activated_aromatic_substitution_not_inert(self): self.reject("C=Cc1ccc(O)cc1","aromatic")

    def test_remote_primary_alcohol_not_assumed_inert(self): self.reject("C=CCCCCCCCO","not independently validated")
    def test_remote_secondary_alcohol_not_assumed_inert(self): self.reject("C=CCCCCCCC(O)C","not independently validated")
    def test_remote_ordinary_ether_not_assumed_inert(self): self.reject("C=CCCCCCCCOC","not independently validated")

    def test_near_oxygen_capture_including_medium_rings(self):
        self.reject("C=CCO","oxygen")
        for s in ["C=CCCO","C=CCCCO","C=CCCCCO","C=CCCCCCO"]:
            with self.subTest(s=s):self.reject(s,"intramolecular oxygen capture")

    def test_ether_cyclization_not_ignored(self): self.reject("C=CCCOC","oxygen capture")
    def test_labile_oxygen_and_other_functional_groups_rejected(self):
        for s in ["C=CCCCCCCCOC(C)(C)C","C=CCCCCCCC(=O)O","C=CCCCCCCC=O","C=CCCCCCCOO"]:
            with self.subTest(s=s): self.assertFalse(self.options(s)[1])

    def test_distant_both_specified_configurations_preserved(self):
        for tag in ["@","@@"]:
            source=f"C=CC[C{tag}H](C)CC"
            rs=self.check(source,[f"ClCC(Cl)C[C{tag}H](C)CC"],2)
            self.assertTrue(all(r["stereochemistry"]["reactant"]["chiralCenters"][0]["specified"] for r in rs))
            self.assertTrue(all(len(r["stereochemistry"]["product"]["chiralCenters"])==2 for r in rs))

    def test_distant_center_cip_recomputed_not_copied(self):
        rs=self.check("C=CCC[C@H](C)CCC(C)(C)C",["ClCC(Cl)CC[C@H](C)CCC(C)(C)C"],2)
        old=rs[0]["stereochemistry"]["reactant"]["chiralCenters"][0]
        for r in rs:
            new=next(c for c in r["stereochemistry"]["product"]["chiralCenters"] if c["atomMap"]==old["atomMap"])
            self.assertNotEqual(old["assignment"],new["assignment"])

    def test_adjacent_specified_center_fails_closed(self): self.reject("C=C[C@H](C)CC","Adjacent specified")

    def test_widely_separated_independent_sites(self):
        rs=self.check("C=CCCCCCCCCC=CC",["ClCC(Cl)CCCCCCCCC=CC","C=CCCCCCCCCC(Cl)C(Cl)C"],3)
        self.assertEqual(len({tuple(r["site"]["atomMaps"]) for r in rs}),2)

    def test_symmetric_equivalent_sites_group_without_merging_enantiomers(self):
        rs=self.check("C=CCCCCCCCCC=C",["ClCC(Cl)CCCCCCCCC=C"],2)
        self.assertTrue(all(len(r["site"]["parameters"]["equivalentSiteFaces"])==2 for r in rs))

    def test_unselected_specified_ez_preserved(self):
        rs=self.check("C/C=C/CCCCCCCC/C=C\\C",["CC(Cl)C(Cl)CCCCCCCC/C=C\\C","C/C=C/CCCCCCCCC(Cl)C(Cl)C"],4)
        for r in rs:self.assertEqual(len([b for b in r["stereochemistry"]["product"]["alkenes"] if b["specified"]]),1)

    def test_short_polyene_and_conjugation_rejected(self):
        for s in ["C=CCCCCC=C","C=CC=C","C=C=C"]:
            self.assertFalse(self.options(s)[1])

    def test_unsupported_rings_elements_and_electronics(self):
        for s in ["C1=CCC1","C1=CCCCCCCC1","C=C1CCCCC1","C=CCCF","C=CCN"]:
            self.assertFalse(self.options(s)[1])
        for source in ["[CH2]C=C","[13CH2]=CC"]:
            with self.assertRaises(service.ChemistryError):self.options(source)

    def test_radical_activation_clears_ionic_option(self):
        self.reject("C=CC","Radical Cl2",{"solvent":"dry","catalyst":"radical"})

    def test_capturing_or_unknown_media_only_conditional_2d(self):
        for medium in ["aqueous-protic","ethanolic-protic","polar-aprotic",""]:
            conditions={"solvent":medium}
            ref,rs,_=self.options("C=CC",conditions)
            self.assertEqual(len(rs),2)
            for r in rs:
                self.assertFalse(r["assessment"]["canRun"])
                self.assertFalse(service.reaction_diagram(r["id"],ref,"chlorine",conditions)["assessment"]["canRun"])
                with self.assertRaises(service.ChemistryError):service.run_curated_reaction(r["id"],ref,"chlorine",conditions)

    def test_extra_activation_and_heat_not_treated_as_dichloride_protocol(self):
        for settings in [{"catalyst":"acid"},{"catalyst":"metal"},{"temperature":"heated"}]:
            for r in self.options("C=CC",{**DRY,**settings})[1]:
                self.assertFalse(r["assessment"]["canRun"]);self.assertEqual(r["assessment"]["status"],"unevaluated")

    def test_wrong_reagents_do_not_become_cl2_by_name(self):
        for reagent in ["bromine","hydrogen-chloride",{"smiles":"ClI"},{"smiles":"II"}]:
            self.assertFalse(self.options("C=CC",reagent=reagent)[1])
        with self.assertRaises(service.ChemistryError):self.options("C=CC",reagent={"smiles":"[Cl-]","name":"Clomine"})

    def test_reagent_validator_rejects_bonds_charges_isotopes(self):
        for s in ["BrBr","Cl","[Cl-]","[35Cl]Cl","ClI","OCl"]:
            with self.assertRaises(ValueError):rule.reagent_check(Chem.MolFromSmiles(s))

    def test_size_bound_counts_added_both_chlorines(self):
        self.assertTrue(self.options("C="+"C"*25)[1])
        self.reject("C="+"C"*26,"80 explicit")

    def test_invalid_raw_stereo_not_erased_by_canonicalization(self):
        for source in ["C/C=C","C/C=C1CCCC1"]:
            self.assertFalse(self.options(source)[1])

    def test_reversed_inputs_preserve_cl_provenance_and_slots(self):
        ref={"smiles":"C/C=C\\C"}
        response=service.match_reactions("chlorine",ref,DRY)
        self.assertEqual(len(response["reactions"]),2)
        for r in response["reactions"]:
            self.assertEqual(r["stoichiometry"]["reactants"][0]["formula"],"Cl2")
            self.assertEqual(r["stoichiometry"]["reactants"][0]["inputSlot"],0)
            self.assertTrue(service.run_curated_reaction(r["id"],"chlorine",ref,DRY)["balanced"])

    def test_map_numbers_never_become_cip_priorities(self):
        a=self.options("C/C=C/C")[1]
        b=self.options("[CH3:41]/[CH:21]=[CH:3]/[CH3:99]")[1]
        self.assertEqual({r["productSmiles"] for r in a},{r["productSmiles"] for r in b})

    def test_atom_reordering_does_not_change_stereochemical_product_set(self):
        mol=Chem.MolFromSmiles("C/C=C\\CC")
        expected={r["productSmiles"] for r in self.options(Chem.MolToSmiles(mol))[1]}
        for order in [list(reversed(range(mol.GetNumAtoms()))),[2,0,4,1,3]]:
            text=Chem.MolToSmiles(Chem.RenumberAtoms(mol,order),canonical=False)
            self.assertEqual({r["productSmiles"] for r in self.options(text)[1]},expected)

    def valid_edit(self):
        a,next_map=_species("a",{"name":"S","smiles":"C/C=C/CCC[C@H](C)CC"},1)
        b,_=_species("b",{"name":"Cl2","smiles":"ClCl"},next_map)
        site=tuple(rule.sites(a["mol"])[0]);before=_combine([a,b]);editor=Chem.RWMol(before)
        rule.edit(editor,a["mol"],b["mol"],site);after=editor.GetMol();Chem.SanitizeMol(after)
        return a["mol"],b["mol"],site,before,after

    def test_validator_rejects_syn_wrong_face_or_erased_new_center(self):
        for tamper in ["syn","face","erase"]:
            a,b,site,before,after=self.valid_edit()
            center=after.GetAtomWithIdx(site[0])
            if tamper=="syn":center.InvertChirality()
            elif tamper=="erase":center.SetChiralTag(Chem.ChiralType.CHI_UNSPECIFIED)
            else:site=(*site[:2],1-site[2])
            with self.assertRaises(ValueError):rule.validate(before,after,a,b,site)

    def test_validator_rejects_distant_inversion_or_stereo_erasure(self):
        for erase in [False,True]:
            a,b,site,before,after=self.valid_edit()
            center=next(v for v in after.GetAtoms() if v.GetChiralTag() in anti.stereo.TETRAHEDRAL and v.GetIdx() not in site[:2])
            if erase:center.SetChiralTag(Chem.ChiralType.CHI_UNSPECIFIED)
            else:center.InvertChirality()
            with self.assertRaises(ValueError):rule.validate(before,after,a,b,site)

    def test_validator_rejects_unaffected_bond_or_halogen_tampering(self):
        for tamper in ["bond","element","charge","maps"]:
            a,b,site,before,after=self.valid_edit();p=rule.participants(a,b,site)
            br=next(v for v in after.GetAtoms() if v.GetAtomMapNum()==p["chlorines"][0])
            if tamper=="element":br.SetAtomicNum(35)
            elif tamper=="charge":br.SetFormalCharge(-1)
            elif tamper=="maps":br.SetAtomMapNum(p["chlorines"][1])
            else:after.GetBondBetweenAtoms(4,5).SetBondType(Chem.BondType.DOUBLE)
            with self.assertRaises((ValueError,RuntimeError)):rule.validate(before,after,a,b,site)

    def test_unsigned_internal_cannot_gain_an_invented_local_configuration(self):
        a,n=_species("a",{"name":"S","smiles":"CC=CCC"},1);b,_=_species("b",{"name":"Cl2","smiles":"ClCl"},n)
        site=tuple(rule.sites(a["mol"])[0]);before=_combine([a,b]);editor=Chem.RWMol(before)
        rule.edit(editor,a["mol"],b["mol"],site);after=editor.GetMol()
        after.GetAtomWithIdx(site[0]).SetChiralTag(Chem.ChiralType.CHI_TETRAHEDRAL_CW)
        with self.assertRaises(ValueError):rule.validate(before,after,a["mol"],b["mol"],site)

    def test_invalid_face_and_site_not_accepted(self):
        a,b,site,before,after=self.valid_edit()
        for invalid in [(*site[:2],True),(*site[:2],-1),(0,0,0),(0,1,3)]:
            with self.assertRaises((ValueError,IndexError)):rule.validate(before,after,a,b,invalid)

    def test_stereo_is_not_chosen_by_random_embedding(self):
        with patch("server.chemistry_server.analyze_molfile",side_effect=AssertionError("No coordinate prediction")):
            rs=self.options("C/C=C\\C")[1]
        self.assertEqual({self.local_cips(r) for r in rs},{("R","R"),("S","S")})

    def test_no_complete_chloronium_mechanism_claim(self):
        for r in self.options("C=CC")[1]:
            self.assertEqual(r["information"]["capabilities"]["mappedMechanism"],"unsupported")

    def test_bromination_retains_its_independent_oxygen_scope(self):
        for source in ["C=CCCCCCCCO","C=CCCCCCCCOC"]:
            ref={"smiles":source}
            self.assertEqual(len(service.match_reactions(ref,"bromine",DRY)["reactions"]),2)
            self.assertFalse(self.options(source)[1])
        ref={"smiles":"CC/C=C/CC"}
        self.assertEqual(len(service.match_reactions(ref,"bromine",DRY)["reactions"]),1)
        self.assertEqual(len(service.match_reactions(ref,"hydrogen-bromide")["reactions"]),1)

    def test_selected_ez_consumed_not_copied_to_single_bond(self):
        for r in self.options("C/C=C/C")[1]:
            self.assertEqual(r["stereochemistry"]["product"]["alkenes"],[])
            self.assertEqual(len(r["compatibility"]["consumedDoubleBonds"]),1)

    def test_each_declared_local_assignment_matches_independent_cip(self):
        for source in ["C/C=C/C","C/C=C\\\\C","C1=CCCCC1","C=CC[C@H](C)CC"]:
            for r in self.options(source)[1]:
                m=Chem.MolFromSmiles(r["productSmiles"])
                Chem.AssignCIPLabels(m)
                actual=sorted(a.GetProp("_CIPCode") for a in m.GetAtoms() if a.HasProp("_CIPCode"))
                reported=sorted(c["assignment"] for c in r["stereochemistry"]["product"]["chiralCenters"] if c["specified"])
                self.assertEqual(actual,reported)

    def test_reagent_name_does_not_replace_actual_cl_atoms(self):
        _,rs,_=self.options("C=CC",reagent={"smiles":"ClCl","name":"Not chlorine"})
        self.assertEqual(len(rs),2)
        self.assertEqual({r["productFormula"] for r in rs},{"C3H6Cl2"})

    def test_aqueous_and_alcohol_notes_name_different_chemistry(self):
        for medium,word in [("aqueous-protic","chlorohydrin"),("ethanolic-protic","chloroether")]:
            r=self.options("C=CC",{"solvent":medium})[1][0]
            self.assertIn(word,r["assessment"]["note"])
            self.assertEqual(r["assessment"]["status"],"unevaluated")
            self.assertNotIn("Unfavorable",r["reasoning"]["label"])

    def test_no_alpha_substitution_instead_of_net_addition(self):
        r=self.options("CC(C)=C(C)C")[1][0]
        self.assertEqual(r["productFormula"],"C6H12Cl2")
        self.assertEqual(r["byproducts"],[])

    def test_17_octadiene_remains_explicit_cyclization_rejection(self):
        self.reject("C=CCCCCC=C","cyclization")

    def test_direct_enol_not_misrepresented_as_new_two_membered_ring(self):
        response=self.options("C=C(O)C")[2]
        self.assertFalse(response["reactions"])
        self.assertIn("heteroatom-substituted/enol", " ".join(response["unsupportedReasons"]))
        self.assertNotIn("Potential 2-membered", " ".join(response["unsupportedReasons"]))


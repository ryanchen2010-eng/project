"""Independent epoxide, acid, map and stereo expectations; not visible examples."""
import unittest
from unittest.mock import patch
from rdkit import Chem
from server import chemistry_server as service, epoxidation_rule as rule, epoxidation_mechanism as mechanism
from server.reaction_diagrams import _species, _combine, _finish

DRY={"solvent":"dry","catalyst":"none"}
def canonical(s,stereo=True):return Chem.MolToSmiles(Chem.MolFromSmiles(s),isomericSmiles=stereo)
def parsed(s):
    p=Chem.SmilesParserParams();p.removeHs=False
    return Chem.MolFromSmiles(s,p)
def cips(r):return tuple(c["assignment"] for c in sorted(r["stereochemistry"]["product"]["chiralCenters"],key=lambda c:c["atomMap"]) if c["atomMap"] in r["site"]["atomMaps"])


class EpoxidationCompatibilityTests(unittest.TestCase):
    def options(self,source,conditions=DRY,reagent="peracetic-acid"):
        ref={"smiles":source,"name":"Independent substrate"}
        response=service.match_reactions(ref,reagent,conditions)
        return ref,[r for r in response["reactions"] if r["mechanism"]=="Epoxidation"],response

    def check(self,source,products,count,reagent="peracetic-acid",acid="CC(=O)O"):
        ref,rs,response=self.options(source,reagent=reagent)
        self.assertEqual(len(rs),count,response["unsupportedReasons"])
        self.assertEqual({canonical(r["productSmiles"],False) for r in rs},{canonical(s,False) for s in products})
        self.assertEqual(len({r["productSmiles"] for r in rs}),count)
        for r in rs:
            self.assertTrue(r["assessment"]["canRun"]);self.assertTrue(r["stoichiometry"]["balanced"])
            self.assertEqual([x["coefficient"] for x in r["stoichiometry"]["reactants"]],[1,1])
            self.assertIsNone(r["epoxidationStereo"]["ratios"])
            d=service.reaction_diagram(r["id"],ref,reagent,DRY)
            self.assertEqual(d["products"][1]["smiles"],canonical(acid))
            self.assertEqual(len(d["products"]),2)
            self.assertTrue(d["highlightsAvailable"])
            before=[a for a in d["atoms"] if a["side"]=="reactants"]
            after=[a for a in d["atoms"] if a["side"]=="products"]
            identity=lambda rows:{a["mapId"]:(a["element"],a["formalCharge"]) for a in rows}
            self.assertEqual(identity(before),identity(after));self.assertEqual(len(identity(before)),len(before))
            p=r["site"]["parameters"]
            a,b=p["alkene"];t,h,q,c,o=(p[k] for k in ("transferredOxygen","peracidHydrogen","proximalOxygen","acylCarbon","carbonylOxygen"))
            origins={v["mapId"]:v for v in before}
            self.assertEqual(origins[t]["speciesIndex"],1);self.assertEqual(origins[t]["element"],"O")
            product_maps={v["mapId"] for v in after if v["speciesIndex"]==0}
            acid_maps={v["mapId"] for v in after if v["speciesIndex"]==1}
            self.assertIn(t,product_maps);self.assertNotIn(t,acid_maps)
            self.assertTrue({h,q,c,o}<=acid_maps);self.assertFalse({h,q,c,o}&product_maps)
            edits=lambda rows:{(frozenset(v["atomMaps"]),v["before"],v["after"]) for v in rows}
            expected={(frozenset((a,b)),2,1),(frozenset((q,t)),1,None),(frozenset((t,h)),1,None),
                      (frozenset((a,t)),None,1),(frozenset((b,t)),None,1),(frozenset((c,q)),1,2),
                      (frozenset((c,o)),2,1),(frozenset((o,h)),None,1)}
            self.assertEqual(edits(d["changes"]),expected);self.assertEqual(edits(r["compatibility"]["editContract"]),expected)
            self.assertEqual((len(d["bondsFormed"]),len(d["bondsBroken"]),len(d["bondOrderChanges"])),(3,2,3))
            m=d["mechanism"];self.assertEqual(len(m["steps"]),1);self.assertTrue(m["steps"][0]["concerted"])
            self.assertIsNone(m["steps"][0]["intermediate"]);self.assertEqual(len(m["steps"][0]["electronMoves"]),4)
            self.assertEqual(edits(m["steps"][0]["bondsFormed"]+m["steps"][0]["bondsBroken"]+m["steps"][0]["bondOrderChanges"]),expected)
            model=service.run_curated_reaction(r["id"],ref,reagent,DRY)["product"]
            self.assertEqual(model["smiles"],r["productSmiles"]);self.assertEqual(model["representation"],"3d")
            main=[v for v in after if v["speciesIndex"]==0]
            self.assertEqual([(v["atomIndex"],v["mapId"],v["element"]) for v in main],[(v["index"],v["mapId"],v["element"]) for v in model["atomLinks"]])
            coordinates=Chem.MolFromMolBlock(model["molfile"],removeHs=False)
            for atom in coordinates.GetAtoms():atom.SetAtomMapNum(0)
            Chem.AssignStereochemistryFrom3D(coordinates,replaceExistingTags=True)
            Chem.AssignStereochemistry(coordinates,cleanIt=True,force=True);Chem.AssignCIPLabels(coordinates)
            indexes={v["mapId"]:v["index"] for v in model["atomLinks"]}
            for center in r["stereochemistry"]["product"]["chiralCenters"]:
                if center["specified"]:
                    atom=coordinates.GetAtomWithIdx(indexes[center["atomMap"]])
                    self.assertTrue(atom.HasProp("_CIPCode"));self.assertEqual(atom.GetProp("_CIPCode"),center["assignment"])
        return rs

    def reject(self,source,reason,conditions=DRY):
        _,rs,response=self.options(source,conditions)
        self.assertFalse(rs);self.assertIn(reason," ".join(response["unsupportedReasons"]))

    def test_ethene_no_fictitious_chiral_center(self):self.assertEqual(self.check("C=C",["C1CO1"],1)[0]["epoxidationStereo"]["assignedAtomMaps"],[])
    def test_propene_opposite_face_r_s_alternatives(self):self.assertEqual({cips(r) for r in self.check("C=CC",["CC1CO1"],2)},{("R",),("S",)})
    def test_longer_terminal_chains(self):
        self.check("C=CCCC",["CCCC1CO1"],2);self.check("C=CCCCCCCCCCC",["CCCCCCCCCCC1CO1"],2)
    def test_branched_terminal(self):self.check("C=C(C)CCC",["CCCC1(C)CO1"],2)
    def test_branch_not_a_carbocation_shift_model(self):self.check("C=CC(C)(C)C",["CC(C)(C)C1CO1"],2)
    def test_identical_substituents_not_stereogenic(self):self.check("C=C(C)C",["CC1(C)CO1"],1)
    def test_tetramethyl_epoxide_no_invented_centers(self):self.check("CC(C)=C(C)C",["CC1(C)OC1(C)C"],1)
    def test_branched_internal_one_new_center_without_possible_ez(self):
        self.assertEqual({cips(r) for r in self.check("CC(C)=CC",["CC1OC1(C)C"],2)},{("R",),("S",)})
    def test_unspecified_tetrasubstituted_geometry_stays_unsigned(self):
        r=self.options("CCC(C)=C(C)CCC")[1][0]
        self.assertIn("unknown",r["epoxidationStereo"]["outcome"])
        self.assertTrue(all(not c["specified"] for c in r["stereochemistry"]["product"]["chiralCenters"]))
    def test_unknown_internal_geometry_stays_unsigned(self):
        r=self.check("CC=CCCC",["CCCC1OC1C"],1)[0]
        self.assertTrue(all(not c["specified"] for c in r["stereochemistry"]["product"]["chiralCenters"]))
        self.assertIn("unknown",r["epoxidationStereo"]["outcome"])
    def test_e_butene_trans_epoxide_rr_ss(self):self.assertEqual({cips(r) for r in self.check("C/C=C/C",["CC1OC1C"],2)},{("R","R"),("S","S")})
    def test_z_butene_cis_epoxide_meso_rs(self):
        r=self.check("C/C=C\\C",["CC1OC1C"],1)[0]
        self.assertEqual(set(cips(r)),{"R","S"});self.assertEqual(len(r["site"]["parameters"]["equivalentSiteFaces"]),2)
    def test_e_hexene_enantiomers(self):self.assertEqual({cips(r) for r in self.check("CC/C=C/CC",["CCC1OC1CC"],2)},{("R","R"),("S","S")})
    def test_z_hexene_meso(self):self.assertEqual(set(cips(self.check("CC/C=C\\CC",["CCC1OC1CC"],1)[0])),{"R","S"})
    def test_unsymmetric_e_and_z_not_forced_meso(self):
        for source,expected in [("C/C=C/CC",{("R","R"),("S","S")}),("C/C=C\\CC",{("R","S"),("S","R")})]:
            self.assertEqual({cips(r) for r in self.check(source,["CCC1OC1C"],2)},expected)
    def test_small_cyclic_epoxides_cis_fused_meso(self):
        for source,product in [("C1=CCCC1","C1CCC2OC12"),("C1=CCCCC1","C1CCC2OC2C1"),("C1=CCCCCC1","C1CCC2OC2CC1")]:
            self.assertEqual(set(cips(self.check(source,[product],1)[0])),{"R","S"})
    def test_substituted_cyclic_face_alternatives(self):self.check("CC1=CCCCC1",["CC12CCCCC1O2"],2)
    def test_unvalidated_ring_geometries_rejected(self):
        for source in ["C1=CCC1","C1=CCCCCCC1","C1=CCCCCCCC1","C=C1CCCCC1","C1=CC2CCC1C2"]:
            self.assertFalse(self.options(source)[1])
    def test_styrene_single_new_center(self):self.assertEqual({cips(r) for r in self.check("C=Cc1ccccc1",["c1ccccc1C1CO1"],2)},{("R",),("S",)})
    def test_alpha_methylstyrene(self):self.check("C=C(C)c1ccccc1",["CC1(CO1)c1ccccc1"],2)
    def test_internal_aryl_geometry_retained_not_a_benzylic_cation(self):self.assertEqual({cips(r) for r in self.check("C/C=C/c1ccccc1",["CC1OC1c1ccccc1"],2)},{("R","R"),("S","S")})
    def test_e_stilbene_two_trans_enantiomers(self):self.assertEqual({cips(r) for r in self.check("c1ccccc1/C=C/c1ccccc1",["c1ccccc1C1OC1c1ccccc1"],2)},{("R","R"),("S","S")})
    def test_z_stilbene_cis_meso(self):self.assertEqual(set(cips(self.check("c1ccccc1/C=C\\c1ccccc1",["c1ccccc1C1OC1c1ccccc1"],1)[0])),{"R","S"})
    def test_activated_aryl_environment_not_assumed_inert(self):self.reject("C=Cc1ccc(O)cc1","aromatic")
    def test_remote_primary_alcohol(self):self.check("C=CCCCCCCCO",["OCCCCCCCC1CO1"],2)
    def test_remote_secondary_alcohol(self):self.check("C=CCCCCCCC(O)C",["CC(O)CCCCCCC1CO1"],2)
    def test_remote_ordinary_ether(self):self.check("C=CCCCCCCCOC",["COCCCCCCCC1CO1"],2)
    def test_nearby_alcohol_direction_and_opening_not_ignored(self):
        self.reject("C=CCO","Activated")
        for source in ["C=CCCO","C=CCCCO","C=CCCCCCO"]:self.reject(source,"capture/open")
    def test_nearby_ether_capture_rejected(self):self.reject("C=CCCOC","capture/open")
    def test_acid_labile_oxygen_groups_rejected(self):
        for source in ["C=CCCCCCCCOC(C)(C)C","C=CCCCCCCCOC(OC)C","C=CCCCCCCC(O)(C)C"]:self.reject(source,"acid-labile")
    def test_competing_carbonyl_oxidation_rejected(self):
        for source in ["C=CCCCCCCC=O","C=CCCCCCCC(=O)C","C=CCCCCCCC(=O)O"]:self.reject(source,"peroxyacid compatibility")
    def test_n_s_and_halogen_spectators_not_globally_enabled(self):
        for source in ["C=CCCN","C=CCCS","C=CCCCF"]:self.assertFalse(self.options(source)[1])
    def test_distant_both_physical_configurations_retained(self):
        for tag in ["@","@@"]:
            rs=self.check(f"C=CC[C{tag}H](C)CC",[f"CC[C{tag}H](C)CC1CO1"],2)
            self.assertTrue(all(len(r["stereochemistry"]["product"]["chiralCenters"])==2 for r in rs))
    def test_distant_descriptor_reassigned_not_copied(self):
        rs=self.check("C=CCC[C@H](C)CCC(C)(C)C",["CC(C)(C)CC[C@@H](C)CCC1CO1"],2)
        for r in rs:
            old=r["stereochemistry"]["reactant"]["chiralCenters"][0]
            new=next(c for c in r["stereochemistry"]["product"]["chiralCenters"] if c["atomMap"]==old["atomMap"])
            self.assertEqual((old["assignment"],new["assignment"]),("S","R"))
    def test_adjacent_specified_center_not_discarded(self):self.reject("C=C[C@H](C)CC","Adjacent specified")
    def test_symmetric_multisite_aliases_not_duplicate_products(self):
        rs=self.check("C=CCCCCC=C",["C=CCCCCC1CO1"],2)
        self.assertTrue(all(len(r["site"]["parameters"]["equivalentSiteFaces"])==2 for r in rs))
    def test_distinct_multiple_sites_selectable(self):
        rs=self.check("C=CCCCCC=CC",["C=CCCCCC1OC1C","CC=CCCCCC1CO1"],3)
        self.assertEqual(len({tuple(r["site"]["atomMaps"]) for r in rs}),2)
    def test_nonconjugated_near_pi_sites_not_given_halonium_cyclization_rule(self):self.check("C=CCC=C",["C=CCC1CO1"],2)
    def test_unselected_specified_ez_retained(self):
        rs=self.options("C/C=C/CCCC/C=C\\C")[1]
        self.assertEqual(len(rs),4)
        for r in rs:self.assertEqual(len([b for b in r["stereochemistry"]["product"]["alkenes"] if b["specified"]]),1)
    def test_conjugation_cumulenes_and_enol_rejected(self):
        for source in ["C=CC=C","C=C=C","C=C(O)C"]:self.assertFalse(self.options(source)[1])
    def test_actual_peroxyacid_variants_and_acid_identity(self):
        for peracid,acid in [("O=COO","O=CO"),("CCC(=O)OO","CCC(=O)O"),("O=C(OO)c1ccccc1","O=C(O)c1ccccc1")]:
            self.check("C=CC",["CC1CO1"],2,{"smiles":peracid},acid)
    def test_mcpba_terminal_oxygen_and_actual_chlorobenzoic_acid(self):self.check("C=CCCC",["CCCC1CO1"],2,{"smiles":"O=C(OO)c1cccc(Cl)c1"},"O=C(O)c1cccc(Cl)c1")
    def test_wrong_oxidants_never_inferred_by_name(self):
        for reagent in ["hydrogen-peroxide",{"smiles":"OO","name":"Peracetic acid"},{"smiles":"CC(=O)OOC"},{"smiles":"CC(=O)O"},{"smiles":"OOC(=O)CCC(=O)OO"}]:
            self.assertFalse(self.options("C=CC",reagent=reagent)[1])
    def test_competing_reagent_functionality_rejected(self):
        for reagent in ["OOC(=O)CCC=O","OOC(=O)CCO","C=CC(=O)OO"]:
            self.assertFalse(self.options("C=CC",reagent={"smiles":reagent})[1])
    def test_reagent_charge_stereo_and_isotope_rejected(self):
        for source in ["CC(=O)O[O-]","C[C@H](CCl)C(=O)OO","CC(=O)O[18OH]","OO","CC(=O)OOC"]:
            with self.assertRaises(ValueError):rule.reagent_check(Chem.MolFromSmiles(source))
    def test_size_boundary_counts_transferred_oxygen(self):
        self.assertTrue(self.options("C="+"C"*25)[1]);self.reject("C="+"C"*26,"80 explicit")
    def test_invalid_raw_stereo_is_not_normalized_away(self):
        for source in ["C/C=C","C/C=C1CCCC1"]:self.assertFalse(self.options(source)[1])
    def test_raw_peracid_stereo_cannot_disappear_at_canonicalization(self):
        for reagent in ["C/C(=O)OO","C[C@H](C)C(=O)OO","O=[C@](C)OO","C[C@H](CC)C(=O)OO |&1:1|"]:
            with self.assertRaisesRegex(service.ChemistryError,"stereochemical annotations"):
                self.options("C=CC",reagent={"smiles":reagent})
    def test_actual_peracid_map_labels_are_not_stereo_or_new_atom_identities(self):
        a=self.options("C=CC")[1]
        b=self.options("C=CC",reagent={"smiles":"[CH3:99][C:1](=[O:33])[O:11][OH:4]"})[1]
        self.assertEqual({r["productSmiles"] for r in a},{r["productSmiles"] for r in b})
    def test_conditions_require_compatible_medium(self):
        r=self.options("C=CC",{})[1][0]
        self.assertFalse(r["assessment"]["canRun"]);self.assertEqual(r["assessment"]["status"],"missing")
    def test_capturing_and_unknown_media_only_conditional_2d(self):
        for medium,word in [("aqueous-protic","open"),("ethanolic-protic","opening"),("polar-aprotic","compatibility")]:
            ref,rs,_=self.options("C=CC",{"solvent":medium})
            for r in rs:
                self.assertEqual(r["assessment"]["status"],"unevaluated");self.assertIn(word,r["assessment"]["note"])
                self.assertIsNotNone(service.reaction_diagram(r["id"],ref,"peracetic-acid",{"solvent":medium})["mechanism"])
                with self.assertRaises(service.ChemistryError):service.run_curated_reaction(r["id"],ref,"peracetic-acid",{"solvent":medium})
    def test_added_activation_or_heat_not_a_guaranteed_epoxide(self):
        for settings in [{"catalyst":"acid"},{"catalyst":"metal"},{"temperature":"heated"}]:
            for r in self.options("C=CC",{**DRY,**settings})[1]:self.assertFalse(r["assessment"]["canRun"])
    def test_radical_not_concerted_epoxidation(self):self.reject("C=CC","Radical activation",{**DRY,"catalyst":"radical"})
    def test_reverse_input_provenance_and_slots(self):
        ref={"smiles":"C/C=C/C"};rs=service.match_reactions("peracetic-acid",ref,DRY)["reactions"]
        self.assertEqual(len(rs),2)
        for r in rs:
            self.assertEqual(r["stoichiometry"]["reactants"][0]["formula"],"C2H4O3")
            self.assertTrue(service.run_curated_reaction(r["id"],"peracetic-acid",ref,DRY)["balanced"])
    def test_atom_order_and_user_map_labels_not_cip_priorities(self):
        m=Chem.MolFromSmiles("C/C=C\\CC");expected={r["productSmiles"] for r in self.options(Chem.MolToSmiles(m))[1]}
        for order in [list(reversed(range(m.GetNumAtoms()))),[2,0,4,1,3]]:
            other=Chem.RenumberAtoms(m,order)
            for a in other.GetAtoms():a.SetAtomMapNum(31-a.GetIdx()*3)
            self.assertEqual({r["productSmiles"] for r in self.options(Chem.MolToSmiles(other,canonical=False))[1]},expected)

    def valid_edit(self,source="C/C=C/CCC[C@H](C)CC"):
        a,n=_species("a",{"name":"Substrate","smiles":source},1)
        b,_=_species("b",{"name":"Actual peracid","smiles":"CC(=O)OO"},n)
        site=tuple(rule.sites(a["mol"])[0]);before=_combine([a,b]);editor=Chem.RWMol(before)
        rule.edit(editor,before,a["mol"],b["mol"],site)
        return a["mol"],b["mol"],site,before,_finish(editor)
    def test_wrong_relative_geometry_face_or_erased_tag_rejected(self):
        for tamper in ["invert","face","erase"]:
            a,b,site,before,after=self.valid_edit();center=after.GetAtomWithIdx(site[0])
            if tamper=="invert":center.InvertChirality()
            elif tamper=="erase":center.SetChiralTag(Chem.ChiralType.CHI_UNSPECIFIED)
            else:site=(*site[:2],1-site[2])
            with self.assertRaises(ValueError):rule.validate(before,after,a,b,site)
    def test_distant_configuration_inversion_or_erasure_rejected(self):
        for erase in [False,True]:
            a,b,site,before,after=self.valid_edit()
            atom=next(x for x in after.GetAtoms() if x.GetChiralTag()!=Chem.ChiralType.CHI_UNSPECIFIED and x.GetIdx() not in site[:2])
            if erase:atom.SetChiralTag(Chem.ChiralType.CHI_UNSPECIFIED)
            else:atom.InvertChirality()
            with self.assertRaises(ValueError):rule.validate(before,after,a,b,site)
    def test_old_simplified_acid_proton_mapping_rejected(self):
        a,b,site,before,after=self.valid_edit();p=rule.participants(a,b,site);editor=Chem.RWMol(after)
        idx={x.GetAtomMapNum():x.GetIdx() for x in editor.GetAtoms()}
        editor.RemoveBond(idx[p["carbonylOxygen"]],idx[p["peracidHydrogen"]])
        editor.AddBond(idx[p["proximalOxygen"]],idx[p["peracidHydrogen"]],Chem.BondType.SINGLE)
        editor.GetBondBetweenAtoms(idx[p["acylCarbon"]],idx[p["carbonylOxygen"]]).SetBondType(Chem.BondType.DOUBLE)
        editor.GetBondBetweenAtoms(idx[p["acylCarbon"]],idx[p["proximalOxygen"]]).SetBondType(Chem.BondType.SINGLE)
        wrong=_finish(editor)
        def unmapped(m):
            m=Chem.RemoveHs(Chem.Mol(m))
            for atom in m.GetAtoms():atom.SetAtomMapNum(0)
            return Chem.MolToSmiles(m)
        self.assertEqual(unmapped(wrong),unmapped(after))
        with self.assertRaises(ValueError):rule.validate(before,wrong,a,b,site)
    def test_unaffected_bond_change_rejected(self):
        a,b,site,before,after=self.valid_edit();after.GetBondBetweenAtoms(4,5).SetBondType(Chem.BondType.DOUBLE)
        with self.assertRaises((ValueError,RuntimeError)):rule.validate(before,after,a,b,site)
    def test_atom_identity_charge_and_map_corruption_rejected(self):
        for tamper in ["element","charge","map"]:
            a,b,site,before,after=self.valid_edit();p=rule.participants(a,b,site)
            atom=next(v for v in after.GetAtoms() if v.GetAtomMapNum()==p["transferredOxygen"])
            if tamper=="element":atom.SetAtomicNum(16)
            elif tamper=="charge":atom.SetFormalCharge(1)
            else:atom.SetAtomMapNum(p["proximalOxygen"])
            with self.assertRaises((ValueError,RuntimeError)):rule.validate(before,after,a,b,site)
    def test_invalid_face_or_site_rejected(self):
        a,b,site,before,after=self.valid_edit()
        for invalid in [(*site[:2],True),(*site[:2],-1),(0,0,0),(0,1,3)]:
            with self.assertRaises((ValueError,IndexError)):rule.validate(before,after,a,b,invalid)
    def test_unknown_internal_cannot_gain_random_new_tag(self):
        a,b,site,before,after=self.valid_edit("CC=CCC")
        after.GetAtomWithIdx(site[0]).SetChiralTag(Chem.ChiralType.CHI_TETRAHEDRAL_CW)
        with self.assertRaises(ValueError):rule.validate(before,after,a,b,site)
    def test_no_random_embedding_decides_product_tags(self):
        with patch("server.chemistry_server.analyze_molfile",side_effect=AssertionError("Not a product predictor")):
            rs=self.options("C/C=C/C")[1]
        self.assertEqual({cips(r) for r in rs},{("R","R"),("S","S")})
    def test_full_concerted_electron_sources_and_destinations(self):
        ref,rs,_=self.options("C=CC");r=rs[0];p=r["site"]["parameters"]
        step=service.reaction_diagram(r["id"],ref,"peracetic-acid",DRY)["mechanism"]["steps"][0]
        a,b=p["alkene"];t,h,q,c,o=(p[k] for k in ("transferredOxygen","peracidHydrogen","proximalOxygen","acylCarbon","carbonylOxygen"))
        expected={((a,b),(a,t)),((t,h),(t,b)),((q,t),(c,q)),((c,o),(o,h))}
        self.assertEqual({(tuple(v["source"]["atomMaps"]),tuple(v["destination"]["atomMaps"])) for v in step["electronMoves"]},expected)
        self.assertTrue(all(v["source"]["type"]==v["destination"]["type"]=="bond" for v in step["electronMoves"]))
        self.assertEqual(len(step["protonTransfers"]),2)
    def test_mechanism_tampered_arrow_source_or_destination_rejected(self):
        from copy import deepcopy
        a,b,site,before,after=self.valid_edit();p=rule.participants(a,b,site)
        moves=[{"id":name,"source":{"type":"bond","atomMaps":list(src)},"destination":{"type":"bond","atomMaps":list(dst)}} for name,src,dst,_ in mechanism.electron_contract(p)]
        for field in ["source","destination"]:
            wrong=deepcopy(moves);wrong[0][field]["atomMaps"][0]=p["peracidHydrogen"]
            with self.assertRaises(ValueError):mechanism.validate(before,after,a,b,site,wrong)
        with self.assertRaises(ValueError):mechanism.validate(before,after,a,b,site,moves[:-1])
    def test_mechanism_validation_uses_map_identity_not_output_atom_order(self):
        a,b,site,before,after=self.valid_edit();p=rule.participants(a,b,site)
        moves=[{"id":name,"source":{"type":"bond","atomMaps":list(src)},"destination":{"type":"bond","atomMaps":list(dst)}} for name,src,dst,_ in mechanism.electron_contract(p)]
        reordered=Chem.RenumberAtoms(after,list(reversed(range(after.GetNumAtoms()))))
        mechanism.validate(before,reordered,a,b,site,moves)
    def test_mechanism_no_invented_stable_intermediate_or_energy(self):
        ref,rs,_=self.options("C=CC");m=service.reaction_diagram(rs[0]["id"],ref,"peracetic-acid",DRY)["mechanism"]
        self.assertEqual(len(m["steps"]),1);self.assertIsNone(m["steps"][0]["intermediate"])
        self.assertEqual(m["energyProfile"]["intermediates"],0);self.assertIsNone(m["energyProfile"]["activationEnergies"])
        self.assertEqual(m["solventSpecies"],[])
    def test_independent_cip_recalculation_matches_all_declared_tags(self):
        for source in ["C/C=C/C","C/C=C\\C","C1=CCCCC1","C=CC[C@H](C)CC"]:
            for r in self.options(source)[1]:
                m=Chem.MolFromSmiles(r["productSmiles"]);Chem.AssignCIPLabels(m)
                self.assertEqual(sorted(a.GetProp("_CIPCode") for a in m.GetAtoms() if a.HasProp("_CIPCode")),sorted(c["assignment"] for c in r["stereochemistry"]["product"]["chiralCenters"] if c["specified"]))
    def test_other_pathways_do_not_inherit_epoxide_oxygen_permissions(self):
        ref={"smiles":"C=CCCCCCCCO"}
        self.assertFalse(service.match_reactions(ref,"chlorine",DRY)["reactions"])
        self.assertTrue(service.match_reactions(ref,"bromine",DRY)["reactions"])
    def test_product_validation_failure_cannot_publish_candidate(self):
        with patch("server.epoxidation_rule.validate",side_effect=ValueError("Synthetic validation failure")):
            _,rs,response=self.options("C=CC")
        self.assertFalse(rs);self.assertIn("Synthetic validation failure"," ".join(response["unsupportedReasons"]))

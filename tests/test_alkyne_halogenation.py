"""Independent Phase 4C connectivity, CIP, mapped edits and output permissions."""
import hashlib
import json
import unittest
from pathlib import Path
from rdkit import Chem
from server import chemistry_server as service, alkyne_halogenation_rule as rule, reaction_engine as engine
from server import molecular_graph as graph, stereochemistry as stereo
from server.reaction_diagrams import _species, _combine, _finish, mapped_product_molecule

FIXTURE = json.loads(Path("tests/fixtures/alkyne-halogenation.json").read_text())


def canonical_without_double(smiles):
    mol = Chem.MolFromSmiles(smiles)
    for bond in mol.GetBonds():
        bond.SetStereo(Chem.BondStereo.STEREONONE); bond.SetBondDir(Chem.BondDir.NONE)
    return Chem.MolToSmiles(mol)


def options(smiles, reagent="bromine", stage="one", conditions=None, reverse=False):
    a, b = {"name": "Independent halogenation input", "smiles": smiles}, reagent
    if reverse: a, b = b, a
    conditions = {"solvent": "dry", "additionStage": stage} if conditions is None else conditions
    match = service.match_reactions(a, b, conditions)
    return a, b, conditions, match, [r for r in match["reactionOptions"] if r["mechanism"] == rule.PATHWAY]


def mapped_inputs(source="CC#CC", reagent="BrBr", stage=1):
    a, n = _species("a", {"name": "test", "smiles": source}, 1)
    a["alkyneHalogenAntiModel"] = True
    inputs = [a]
    for _ in range(stage):
        b, n = _species("b", {"name": "test", "smiles": reagent}, n); inputs.append(b)
    return inputs, tuple(graph.find_alkynes(a["mol"])[0]) + (stage,)


def tetra_signature(atom):
    # Independent map-order parity, never a comparison of R/S letters.
    neighbors = [a.GetAtomMapNum() for a in atom.GetNeighbors()]
    inversions = sum(neighbors[i] > neighbors[j] for i in range(len(neighbors)) for j in range(i + 1, len(neighbors)))
    return (atom.GetChiralTag() == Chem.ChiralType.CHI_TETRAHEDRAL_CW) ^ bool(inversions % 2)


class AlkyneHalogenationTests(unittest.TestCase):
    def positive(self, case, halogen, stage):
        reagent = "bromine" if halogen == "Br" else "chlorine"
        for reverse in (False, True):
            a, b, c, match, found = options(case["substrate"], reagent, stage, reverse=reverse)
            expected = {canonical_without_double(p.replace("Br", halogen)) for p in case[stage]}
            self.assertEqual({canonical_without_double(r["productSmiles"]) for r in found}, expected)
            legacy = [r for r in match["reactions"] if r["mechanism"] == rule.PATHWAY]
            self.assertEqual(len(legacy), case.get("legacySites", len(found)))
            for r in found:
                count = 1 if stage == "one" else 2
                allowed = not case.get("bookkeepingOnly") and (halogen == "Br" or stage == "two" and not case.get("oxygen"))
                self.assertEqual(r["assessment"]["canRun"], allowed)
                self.assertNotIn(r["reasoning"]["label"], {"Strong match", "Unfavorable"})
                self.assertEqual(r["assessment"]["evidence"]["experimentalOutcome"], "not-predicted")
                self.assertEqual(r["alkyneHalogenModel"]["equivalents"], count)
                self.assertEqual(r["alkyneHalogenModel"]["halogen"], halogen)
                self.assertEqual(r["byproducts"], [])
                basis = r["stoichiometry"]
                x2 = next(i for i in basis["reactants"] if i["formula"] == halogen + "2")
                self.assertEqual(x2["coefficient"], count)
                self.assertEqual(x2["inputSlot"], 0 if reverse else 1)
                self.assertAlmostEqual(sum(i["molarMass"] * i["coefficient"] for i in basis["reactants"]), basis["product"]["molarMass"], places=6)
                self.assertEqual(basis["context"]["canGenerate3D"], allowed)
                self.assertIn("actual supply", basis["context"]["warning"])
                d = service.reaction_diagram(r["id"], a, b, c)
                self.assertIsNone(d["mechanism"])
                self.assertEqual(r["information"]["capabilities"]["mappedMechanism"], "unsupported")
                self.assertIn("Conditional", d["note"])
                self.assertEqual(len(d["bondsBroken"]), count)
                self.assertEqual(len(d["bondsFormed"]), 2 * count)
                self.assertEqual([(v["before"], v["after"]) for v in d["bondOrderChanges"]], [(3, 3-count)])
                before = [v for v in d["atoms"] if v["side"] == "reactants"]
                after = [v for v in d["atoms"] if v["side"] == "products"]
                identity = lambda xs: {v["mapId"]: (v["element"], v["formalCharge"]) for v in xs}
                self.assertEqual(identity(before), identity(after)); self.assertEqual(len(before), len(after))
                pairs = r["alkyneHalogenModel"]["halogenPairs"]
                self.assertEqual({frozenset(v["atomMaps"]) for v in d["bondsBroken"]}, {frozenset(p) for p in pairs})
                incoming = {m for pair in pairs for m in pair}
                self.assertEqual(len(incoming), 2 * count)
                self.assertEqual(incoming, {m for e in d["bondsFormed"] for m in e["atomMaps"] if m not in r["site"]["atomMaps"]})
                self.assertTrue(all(identity(before)[m][0] == halogen for m in incoming))
                # Recover exact mapped product and check physical spectator parity.
                ids, custom, _ = service._resolve_reactants(a, b)
                catalog = {**service.REACTANTS, **custom}
                reaction = service._reactions_for_pair(*ids, catalog, service._conditions(c))[0][r["id"]]
                product = mapped_product_molecule(reaction, catalog)
                inputs, _ = _species("source", catalog[reaction["reactants"][0]], 1)
                indexed = {v.GetAtomMapNum(): v for v in product.GetAtoms()}
                for atom in inputs["mol"].GetAtoms():
                    if atom.GetChiralTag() in stereo.TETRAHEDRAL:
                        self.assertEqual(tetra_signature(atom), tetra_signature(indexed[atom.GetAtomMapNum()]))
                local = [v for v in r["stereochemistry"]["product"]["alkenes"] if set(v["atomMaps"]) == set(r["site"]["atomMaps"])]
                if stage == "one":
                    self.assertEqual(len(local), 1)
                    self.assertEqual(local[0]["assignment"], "E" if halogen == "Br" else None)
                    if halogen == "Br": self.assertEqual(r["alkyneHalogenModel"]["stereoAssignment"], "E")
                else:
                    self.assertEqual(local, [])
                    self.assertFalse(any(v["atomMap"] in r["site"]["atomMaps"] for v in r["stereochemistry"]["product"]["chiralCenters"]))
                if not allowed:
                    with self.assertRaises(service.ChemistryError): service.run_curated_reaction(r["id"], a, b, c)
                    continue
                result = service.run_curated_reaction(r["id"], a, b, c)["product"]
                self.assertEqual(result["representation"], "3d")
                self.assertEqual(result["smiles"], r["productSmiles"])
                self.assertEqual([(v["atomIndex"],v["mapId"],v["element"]) for v in after],
                                 [(v["index"],v["mapId"],v["element"]) for v in result["atomLinks"]])
                shape = Chem.MolFromMolBlock(result["molfile"], removeHs=False)
                self.assertTrue(shape.GetConformer().Is3D())
                # Independently recover stereo from coordinates, NOT vice versa.
                expected_stereo = stereo.inspect_stereochemistry(product)
                for atom in shape.GetAtoms(): atom.SetChiralTag(Chem.ChiralType.CHI_UNSPECIFIED)
                for bond in shape.GetBonds(): bond.SetStereo(Chem.BondStereo.STEREONONE); bond.SetBondDir(Chem.BondDir.NONE)
                Chem.AssignStereochemistryFrom3D(shape, replaceExistingTags=True)
                measured = stereo.inspect_stereochemistry(shape)
                centers = {v["atomMap"]:v["assignment"] for v in measured["chiralCenters"]}
                for v in expected_stereo["chiralCenters"]:
                    if v["specified"]: self.assertEqual(centers[v["atomMap"]], v["assignment"])
                if halogen == "Br" and stage == "one":
                    self.assertEqual(next(v["assignment"] for v in measured["alkenes"] if set(v["atomMaps"]) == set(r["site"]["atomMaps"])), "E")

    def negative(self, case):
        for reagent in ("bromine", "chlorine"):
            for stage in ("one", "two"):
                _, _, _, match, found = options(case["substrate"], reagent, stage)
                self.assertFalse(found)
                if case.get("reason"): self.assertIn(case["reason"].lower(), " ".join(match["unsupportedReasons"]).lower())

    def test_conditions_and_omissions_are_not_experimental_products(self):
        for c in ({}, {"solvent":"dry"}, {"additionStage":"one"}, {"solvent":"aqueous-protic","additionStage":"one"},
                  {"solvent":"ethanolic-protic","additionStage":"two"}, {"solvent":"polar-aprotic","additionStage":"one"},
                  {"solvent":"dry","additionStage":"one","catalyst":"radical"},
                  {"solvent":"dry","additionStage":"two","catalyst":"acid"},
                  {"solvent":"dry","additionStage":"two","temperature":"heated"}):
            a,b,_,_,found=options("CC#CC",conditions=c)
            self.assertEqual(len(found),1); r=found[0]
            self.assertFalse(r["assessment"]["canRun"])
            self.assertNotIn(r["assessment"]["status"], {"disfavored", "reference-difference"})
            self.assertEqual(r["stoichiometry"]["context"]["canGenerate3D"],False)
            self.assertIsNone(r["alkyneHalogenModel"]["stereoAssignment"])
            self.assertIn("halogen supply", r["assessment"]["evidence"]["unknownConditions"])
            self.assertTrue(service.reaction_diagram(r["id"],a,b,c)["svg"])
            with self.assertRaises(service.ChemistryError): service.run_curated_reaction(r["id"],a,b,c)

    def test_supported_e_geometry_has_independent_golden_structures(self):
        self.assertEqual(options("C#C")[-1][0]["productSmiles"], "Br/C=C/Br")
        self.assertEqual(options("CCC#C")[-1][0]["productSmiles"], "CC/C(Br)=C\\Br")
        self.assertEqual(options("CC#CC")[-1][0]["productSmiles"], "C/C(Br)=C(/C)Br")

    def test_reversed_substrate_numbering_does_not_change_e_relationship(self):
        source=Chem.MolFromSmiles("CCCC#CC")
        source=Chem.RenumberAtoms(source,list(reversed(range(source.GetNumAtoms()))))
        reordered=Chem.MolToSmiles(source, canonical=False)
        self.assertEqual(options("CCCC#CC")[-1][0]["productSmiles"],options(reordered)[-1][0]["productSmiles"])

    def test_stage_or_halogen_switch_cannot_reuse_a_stale_product(self):
        a,b,c,_,rs=options("CC#CC")
        with self.assertRaises(service.ChemistryError): service.reaction_diagram(rs[0]["id"],a,b,{**c,"additionStage":"two"})
        with self.assertRaises(service.ChemistryError): service.run_curated_reaction(rs[0]["id"],a,"chlorine",c)
        # Same stage but loss of medium must lose both permission and E claim.
        replacement=options("CC#CC",conditions={"additionStage":"one"})[-1][0]
        self.assertIsNone(replacement["alkyneHalogenModel"]["stereoAssignment"])
        self.assertFalse(replacement["assessment"]["canRun"])

    def test_wrong_reagent_models_and_unrecognized_conditions(self):
        for reagent in ("hydrogen-bromide","hydrogen-chloride","hydrogen","water",{"smiles":"II"},{"smiles":"FF"},{"smiles":"BrCl"}):
            self.assertFalse(options("CCC#C",reagent)[-1])
        for c in ({"additionStage":"excess"},{"additionStage":"3"},{"catalyst":"light"},{"solvent":"acetic-acid"}):
            with self.assertRaises(service.ChemistryError): options("CC#CC",conditions=c)

    def test_raw_stereo_is_not_silently_normalized_away(self):
        for source in ("C#CC[C@H](C)CC |&1:3|", "C#C[C@H](C)C", "C/C#CC"):
            try:
                _,_,_,m,found=options(source)
                self.assertFalse(found); self.assertTrue(m["unsupportedReasons"])
            except service.ChemistryError:
                pass

    def test_unique_site_aliases_preserve_legacy_mapping(self):
        a,b,c,m,found=options("C#CCCCCC#C")
        self.assertEqual(len(found),1)
        self.assertEqual(found[0]["optionIdentity"]["siteCount"],2)
        for rid in found[0]["optionIdentity"]["sourceReactionIds"]:
            self.assertEqual(service.reaction_diagram(rid,a,b,c)["site"]["siteId"],rid)
        self.assertEqual(len(options("C#CCCCCCC#CC")[-1]),2)

    def test_contract_rejects_wrong_number_or_kind_of_x2(self):
        inputs,site=mapped_inputs(stage=2)
        for reagents in ([inputs[1]["mol"]], [inputs[1]["mol"]]*2):
            with self.assertRaises(ValueError): rule.participants(inputs[0]["mol"],reagents,site)
        for reagent in ("ClBr","Br","[Br-]","II","[81Br][81Br]","[H]Br"):
            inputs,site=mapped_inputs(reagent=reagent)
            with self.assertRaises(ValueError): rule.participants(inputs[0]["mol"],[inputs[1]["mol"]],site)

    def test_validation_catches_wrong_geometry_and_unaffected_edits(self):
        inputs,site=mapped_inputs(source="CCC#CC")
        before=_combine(inputs); product=engine.transform(rule.PATHWAY,inputs,site)[0]
        parser=Chem.SmilesParserParams(); parser.removeHs=False
        restored=Chem.MolFromSmiles(Chem.MolToSmiles(product),parser)
        rule.validate(before,restored,inputs[0]["mol"],[inputs[1]["mol"]],site,anti_model=True)
        for state in (Chem.BondStereo.STEREOZ,Chem.BondStereo.STEREONONE):
            tampered=Chem.Mol(product)
            bond=tampered.GetBondBetweenAtoms(*site[:2]); bond.SetStereo(state)
            with self.assertRaises(ValueError): rule.validate(before,tampered,inputs[0]["mol"],[inputs[1]["mol"]],site,anti_model=True)
        tampered=Chem.RWMol(product)
        old=next(b for b in tampered.GetBonds() if b.GetBeginAtom().GetAtomicNum()==b.GetEndAtom().GetAtomicNum()==6 and b.GetBondType()==Chem.BondType.SINGLE)
        old.SetBondType(Chem.BondType.DOUBLE)
        with self.assertRaises(ValueError): rule.validate(before,tampered,inputs[0]["mol"],[inputs[1]["mol"]],site,anti_model=True)

    def test_size_limits_are_stage_specific_and_not_relaxed(self):
        # C25H48 = 73 explicit atoms; C27H52 =79, plus X2 exceeds80.
        source="C"*26+"#C"
        self.assertFalse(options(source)[-1])
        self.assertIn("80 explicit atoms", " ".join(options(source)[3]["unsupportedReasons"]))
        self.assertIn("incoming halogen", " ".join(options(source)[3]["unsupportedReasons"]))

    def test_fixed_benchmark_unchanged(self):
        self.assertEqual(hashlib.sha256(Path("scripts/audit_reaction_lab.py").read_bytes()).hexdigest(),
                         "1304ec753e0c7986ade09e324cc1f420572e46c8e5ecc8ef3979bdd669c75b55")

    def test_ordinary_remote_saturated_carbocycle_keeps_its_ring_bonds(self):
        source="C#CCCC1CCCCC1"
        original=Chem.MolFromSmiles(source)
        for stage in ("one","two"):
            a,b,c,_,found=options(source,stage=stage)
            self.assertEqual(len(found),1)
            product=Chem.MolFromSmiles(found[0]["productSmiles"])
            self.assertEqual([len(r) for r in product.GetRingInfo().AtomRings()],[6])
            self.assertEqual(sum(b.IsInRing() for b in original.GetBonds()),sum(b.IsInRing() for b in product.GetBonds()))
            self.assertEqual(service.run_curated_reaction(found[0]["id"],a,b,c)["product"]["representation"],"3d")


for i,case in enumerate(FIXTURE["positive"]):
    for halogen in ("Br","Cl"):
        for stage in ("one","two"):
            def positive_test(self, case=case, halogen=halogen, stage=stage): self.positive(case,halogen,stage)
            setattr(AlkyneHalogenationTests,f"test_positive_{i:02d}_{halogen}_{stage}",positive_test)
for i,case in enumerate(FIXTURE["negative"]):
    def negative_test(self, case=case): self.negative(case)
    setattr(AlkyneHalogenationTests,f"test_negative_{i:02d}",negative_test)

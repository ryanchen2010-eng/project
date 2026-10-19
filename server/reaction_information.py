"""Reusable information for implemented mechanisms, not individual molecules.

Existing engine fields remain compatible. This registry is descriptive; only
the structural engine can decide whether a pair/site is eligible.
"""

DEFINITIONS = {
    "Hydrogenation": ("Addition", "Reduction", ["alkene"], ["saturated C–C at the selected site"], "H₂ adds across the selected C=C.", "Basic"),
    "Bromination": ("Addition", None, ["alkene"], ["vicinal dihalide"], "Br adds to each selected alkene carbon.", "Basic"),
    "Chlorination": ("Addition", None, ["alkene"], ["vicinal dihalide"], "Cl adds to each selected alkene carbon.", "Basic"),
    "Hydration": ("Addition", None, ["alkene"], ["alcohol"], "H and OH add across the selected C=C.", "Intermediate"),
    "Hydrohalogenation": ("Addition", None, ["alkene"], ["haloalkane"], "H and halogen add across the selected C=C.", "Intermediate"),
    "Epoxidation": ("Addition", "Oxidation", ["alkene", "peroxyacid"], ["epoxide", "carboxylic acid"], "A peroxyacid transfers oxygen to C=C, forming an epoxide and a carboxylic acid.", "Intermediate"),
    "SN2": ("Substitution", None, ["haloalkane"], ["alcohol"], "OH replaces the leaving group in one concerted step.", "Intermediate"),
    "SN1": ("Substitution", None, ["haloalkane"], ["alcohol"], "Ionization is followed by water capture and proton transfer.", "Intermediate"),
    "E2": ("Elimination", None, ["haloalkane"], ["alkene"], "A beta H and leaving group are removed as C=C forms.", "Intermediate"),
    "E1": ("Elimination", None, ["haloalkane"], ["alkene"], "Ionization is followed by beta-H removal and C=C formation.", "Intermediate"),
    "Alcohol oxidation": ("Oxidation", None, ["alcohol"], ["aldehyde or ketone"], "The selected alcohol becomes a carbonyl at this net stage.", "Intermediate"),
    "Aldehyde oxidation": ("Oxidation", None, ["aldehyde"], ["carboxylic acid"], "The selected aldehyde becomes the neutral acid reporting structure.", "Intermediate"),
    "Carbonyl hydrogenation": ("Reduction", None, ["aldehyde", "ketone"], ["alcohol"], "H₂ adds across an aldehyde or ketone C=O.", "Basic"),
    "Esterification": ("Condensation", None, ["carboxylic acid", "alcohol"], ["ester"], "An acid and alcohol form an ester and water.", "Intermediate"),
    "Ester hydrolysis": ("Hydrolysis", None, ["ester"], ["carboxylic acid", "alcohol or phenol"], "Acid hydrolysis cleaves acyl–O; supported lactones give one connected hydroxy acid.", "Intermediate"),
    "Alcohol dehydration": ("Elimination", None, ["alcohol"], ["alkene"], "Selected OH and beta H leave as water, forming C=C.", "Intermediate"),
    "Alcohol substitution": ("Substitution", None, ["alcohol"], ["haloalkane"], "HX activates OH and replaces it with the actual halogen.", "Intermediate"),
    "Ester saponification": ("Hydrolysis", None, ["ester"], ["carboxylate", "alcohol or phenol"], "Hydroxide cleaves acyl–O; supported lactones give one connected hydroxy carboxylate. No acid work-up.", "Intermediate"),
    "Alkyne hydrogenation": ("Reduction", "Addition", ["alkyne"], ["alkane"], "Two H₂ equivalents fully reduce the selected C≡C.", "Basic"),
    "Alkyne partial hydrogenation": ("Reduction", "Addition", ["alkyne"], ["alkene"], "One H₂/Lindlar reduces a selected isolated acyclic alkyne; internal products are cis/Z.", "Intermediate"),
    "Alkyne halogenation": ("Addition", None, ["alkyne"], ["dihaloalkene or tetrahaloalkane"], "One or two X₂ equivalents add at C≡C.", "Intermediate"),
    "Alkyne hydrohalogenation": ("Addition", None, ["alkyne"], ["vinyl halide or geminal dihalide"], "One or two HX equivalents add in the supported orientation.", "Intermediate"),
    "Alkene dihydroxylation": ("Oxidation", "Addition", ["alkene"], ["vicinal diol"], "An Os-based catalytic net model adds OH to both alkene carbons.", "Intermediate"),
    "Polymerization model": ("Polymerization", "Addition", ["alkene"], ["finite oligomer"], "Defined finite chains grow and combine with explicit phenyl end groups.", "Advanced"),
}


def group_reactions(group):
    return [{"mechanism": name, "classifications": [primary] + ([secondary] if secondary else [])}
            for name, (primary, secondary, reactants, _, _, _) in DEFINITIONS.items() if group in reactants]


def reaction_information(reaction):
    mechanism = reaction["mechanism"]
    primary, secondary, reactants, products, transformation, difficulty = DEFINITIONS[mechanism]
    mechanism_supported = mechanism in {"SN1", "SN2", "E1", "E2", "Epoxidation"}
    ester_cleavage = mechanism in {"Ester hydrolysis", "Ester saponification"}
    site_hydrogenation = mechanism == "Hydrogenation" and bool(reaction.get("compatibility"))
    site_carbonyl = mechanism == "Carbonyl hydrogenation" and bool(reaction.get("compatibility"))
    site_oxidation = mechanism == "Alcohol oxidation" and bool(reaction.get("compatibility"))
    site_sn2 = mechanism == "SN2" and bool(reaction.get("compatibility"))
    site_e2 = mechanism == "E2" and bool(reaction.get("compatibility"))
    site_sn1 = mechanism == "SN1" and bool(reaction.get("compatibility"))
    site_e1 = mechanism == "E1" and bool(reaction.get("compatibility"))
    site_hydration = mechanism == "Hydration" and bool(reaction.get("compatibility"))
    site_hydrohalogenation = mechanism == "Hydrohalogenation" and bool(reaction.get("compatibility"))
    site_epoxidation = mechanism == "Epoxidation" and bool(reaction.get("compatibility"))
    site_chlorination = mechanism == "Chlorination" and bool(reaction.get("compatibility"))
    site_bromination = mechanism == "Bromination" and bool(reaction.get("compatibility"))
    site_diol = mechanism == "Alkene dihydroxylation" and bool(reaction.get("compatibility"))
    result = {
        "version": 1, "name": mechanism, "primaryFamily": primary,
        "classifications": [primary] + ([secondary] if secondary else []),
        "reactantGroups": reactants, "productGroups": products,
        "transformation": transformation, "difficulty": difficulty,
        "requirements": dict(reaction["profile"]),
        "capabilities": {
            "netTransformation": "supported", "mappedMechanism": "supported" if mechanism_supported else "unsupported",
            "regioselectivity": "bounded orientation or separate unsigned constitutional alternatives" if site_hydration or site_hydrohalogenation else "bounded orientation" if mechanism in {"Hydration", "Hydrohalogenation"} else "constitutional alternatives only" if mechanism in {"E1", "E2"} else "not evaluated",
            "stereochemistry": "validated syn OH/OH alternatives, cis monocyclic products and distant physical retention; unknown internal geometry unsigned" if site_diol else "validated same-face oxygen transfer and distant retention; unknown starting geometry stays unsigned" if site_epoxidation else "validated local anti alternatives and distant retention; unknown starting geometry stays unsigned" if site_bromination or site_chlorination else "validated distant retention; reacting center unassigned" if site_sn1 else "validated distant retention; new alkene unassigned" if site_e1 else "specified-center inversion" if mechanism == "SN2" else "validated retention of specified configurations in the net edit" if ester_cleavage else
                               "validated spectator retention; reactive alcohol center becomes planar" if site_oxidation else
                               "validated spectator retention; new centers unassigned" if site_hydrogenation or site_carbonyl or site_hydration or site_hydrohalogenation else "validated distant retention; bounded local anti E/Z" if site_e2 else "geometry utility available; outcome unassigned" if mechanism == "E2" else "unsupported", "energy": "qualitative only" if mechanism_supported else "unsupported",
        },
        "stereochemistry": reaction.get("stereochemistry"),
        **({"carbocationModel": reaction["carbocationModel"]} if site_sn1 or site_e1 else {}),
        "limitations": (["Catalytic Os/H2O2 net model only, with explicit confirmation of aqueous diol release. Peroxide alone, NMO, KMnO4 and oxidative cleavage are not enabled.",
                         "Formal H2O2 O/H mapping balances all explicit species; it is not elementary oxygen provenance or proton exchange through omitted catalyst/work-up species.",
                         "Syn OH/OH relative configurations are validated from E/Z or isolated small-ring geometry. Meso equivalents are grouped; opposite faces have no predicted ratio. Unknown internal geometry stays unsigned.",
                         "Screened remote OH/ethers and unactivated phenyl can be retained; nearby directed/cyclic oxidation, conjugation, complex rings and other competing oxidizable groups fail closed.",
                         "No cyclic osmate, mapped proton transfers, catalyst cycle or complete mechanism is implemented. 2D is net bond changes; 3D is a representative conformer, not experimental selectivity. Further oxidation and actual yields are not predicted."] if site_diol else ["One actual screened peroxyacid transfers its terminal O to the selected C=C. The actual acid coproduct retains the remaining reagent atoms, including the concertedly transferred proton.",
                         "Same-face oxygen transfer preserves named alkene substituent relationships. Validated E/Z and small-ring geometry determine configurations; unknown internal geometry remains unsigned. No facial ratio is assigned.",
                         "Screened remote saturated OH/ethers and unactivated phenyl skeletons are bounded net spectators, not universal inertness. Nearby oxygen capture/direction, conjugation, competing oxidation and unvalidated rings fail closed.",
                         "One formal concerted four-arrow step, no stable intermediate. Electron-pair bookkeeping is not calculated synchronous timing, transition-state geometry, rates or activation energies.",
                         "The acid coproduct can enable later ring opening/rearrangement. Solvent compatibility, buffering, selective mono-epoxidation and isolated yields are not predicted."] if site_epoxidation else ["Actual Cl2 addition only in the neutral non-nucleophilic model; aqueous chlorohydrin, alcohol capture, added activation and radical chlorination are different unimplemented pathways.",
                         "Mapped E/Z or validated small-ring paths determine anti alternatives. Terminal single-center alternatives are offered; unknown internal geometry stays unsigned. Meso and graph-equivalent representations are grouped without ratios.",
                         "Anti is an addition relationship, not a universal trans label. Validated isolated 5–7-membered cyclic products have trans Cl/Cl. Distant physical configurations and independently recalculated CIP labels are retained.",
                         "Nearby second pi bonds including 1,7-octadiene, internal aryl-adjacent sites, activated rings and unvalidated ring environments fail closed. Remote alcohol/ether permissions from Br2 are not transferred to Cl2 without independent compatibility validation.",
                         "This is a mapped net transformation, not a complete chloronium mechanism, experimental protocol, selective mono-chlorination or a prediction from a sampled conformer."] if site_chlorination else ["Actual Br2 addition only in the neutral non-nucleophilic model. Water/alcohol media, unknown aprotic solvent chemistry and added/radical activation are not identical dibromide pathways.",
                         "Specified E/Z or validated cis ring paths define opposite-face alternatives; terminal single-center alternatives are offered. Unknown internal geometry stays unsigned. Meso/equivalent representations are grouped, not duplicated.",
                         "Anti describes approach relative to the starting pi bond, not a universal trans acyclic label. Only validated cyclic relationships are called trans Br/Br. Distant physical configurations and independent CIP are retained; no stereoisomer ratios are predicted.",
                         "Nearby O/pi capture, conjugation, acid-sensitive/activated groups and unvalidated ring environments are excluded. Ordinary screened remote OH/ethers and unactivated phenyl skeletons have bounded net scope, not experimentally proven inertness.",
                         "Internal aryl-adjacent alkenes are excluded where open benzylic-ion stereospecificity is unvalidated. Visualization is mapped net chemistry, not a complete bromonium mechanism or a conformer-derived stereo prediction."] if site_bromination else ["Ionic selected-site addition of actual HCl/HBr/HI only. HX supplies both entering atoms and is consumed; no separate acid catalyst or radical/peroxide anti-Markovnikov model is inferred.",
                         "Substitution/resonance or full-graph equivalence supplies a bounded orientation; equal inequivalent ends have separate constitutional options without major/minor claims. Only proven graph-equivalent site/orientation products are grouped; distinct products stay selectable.",
                         "HBr/HI alcohol substitution and ether cleavage compete and are excluded here. Only screened unactivated primary alcohols and ordinary dialkyl ethers have a qualified, explicitly ambient no-added-activation HCl neutral-reporting scope. Protonation and eventual conversion are not predictions of inertness.",
                         "Adjacent hydride/alkyl shifts, short O/pi capture, direct heteroatoms/conjugation and complex ring cations are excluded. Selected isolated 5–8-membered carbocycles are bounded scope; longer-range migration, polymerization, solvent capture, later addition and experimental selectivity are not generally predicted.",
                         "Selected valid E/Z is consumed; distant physical configurations and unselected geometry must remain. CIP is recomputed; new centers and syn/anti stay unassigned. An optimized 3D conformer is not a stereochemical product distribution. Visualization shows net changes only, not a complete two-step ionic mechanism."] if site_hydrohalogenation else
                        ["Selected isolated C=C or screened phenyl-conjugated site with actual water and required acid activation. Ordinary monocyclic 5–8-membered carbocycles and screened remote saturated OH/ethers are bounded net scopes, not general acid inertness.",
                         "Substitution/resonance can justify an OH orientation. Equal inequivalent ends are separate constitutional capture alternatives with no major/minor claim. Adjacent shift risks and short intramolecular capture are excluded; longer-range migration, isomerization, polymerization and equilibrium conversion are not predicted.",
                         "Only selected E/Z is consumed. Distant physical configurations and independent CIP assignments are checked; new centers and syn/anti outcomes stay unassigned. One 3D conformer is not a guaranteed stereochemical product.",
                         "Acid is regenerated, not consumed; one water equivalent supplies net H/OH. H maps track the balanced net graph, not proton/isotope exchange with the acid. No stepwise hydration mechanism is implemented yet."] if site_hydration else
                        ["Water-only screened tertiary/benzylic, narrow Me/Me or Me/Et secondary and symmetric terminal-equivalent allyl solvolysis. Ordinary primary/methyl, other secondary aliphatic, general allylic and ring-bound carbocations remain outside the model.",
                         "Only reacting-center configuration is lost upon planar carbocation formation; product configuration and any racemization/facial ratio remain unassigned. Unaffected mapped configurations and independent CIP labels are checked.",
                         "Exact ionization, water capture and solvent deprotonation edits/charges are validated separately. Benzylic/allylic cations are drawn as one resonance contributor, not a localized charge-density prediction.",
                         "E1/SN2, hydride/alkyl migration, oxygen capture/cyclization, acid-sensitive cleavage and selective mono-conversion are not generally predicted. Unsupported competitors fail closed; missing/mismatched conditions are qualitative alternatives, not protocols.",
                         "Net HX is an acid-equivalent reporting form; the aqueous mechanism shows hydronium plus halide with explicit solvent water. A 3D conformer is one representative shape, not an enantiomeric mixture or assigned experimental configuration."] if site_sn1 else
                        ["Water-only screened tertiary/benzylic, narrow Me/Me or Me/Et secondary and H-free-central-pi allylic E1 sites. Actual saturated beta C–H required; ring-bound, arbitrary primary/secondary, cumulene and unvalidated competing environments remain excluded.",
                         "Exact ionization gives a positive unassigned planar alpha carbon before solvent water removes beta H. Alpha/beta configuration loss and distant physical retention are separately checked, including serialized structures and independent CIP labels.",
                         "Constitutional beta positions are separate options, not Zaitsev/Hofmann ratios or selective mono-elimination. New E/Z remains unassigned; E2 anti geometry or a single 3D conformer does not assign E1 outcomes.",
                         "SN1 capture, cationic shifts, cyclization, acid-sensitive cleavage and later conversion may compete; the absence of an SN1 option is not proof of no substitution. No rearranged products or experimental conditions/outcomes are predicted.",
                         "Net HX reports released acid. The aqueous mechanism uses explicit water and shows hydronium plus halide; solvent water is excluded from net reaction-amount arithmetic. Medium/temperature selectors are qualitative, not a solvent/pH or kinetic model."] if site_e1 else
                        ["Hydroxide-only acyclic alpha/beta E2; actual beta C–H and C–Cl/Br/I are required. Ring-bound, allylic, geminal/near-oxygen and unvalidated competing environments remain excluded.",
                         "Only participating alpha/beta centers become planar; distant mapped configurations must remain. A unique anti E/Z relationship is assigned only from two specified local tetrahedra and one beta H; unsigned alternatives stay unassigned.",
                         "A sampled non-anti conformer does not prove elimination impossible. Constructed acyclic anti rotation is kinematic, not an energy/clash search, transition state or reaction-rate prediction.",
                         "Separate one-site constitutional options are not product ratios or selective mono-conversion. Substitution, alcohol deprotonation/cyclization and later eliminations may compete."] if site_e2 else
                        ["SN2 inversion applies only to specified tetrahedral centers; a change in CIP priorities need not change the R/S letter.",
                         "Hydroxide-only, screened remote OH/ether groups and existing methyl/primary/selected secondary/benzylic sites. Ring-bound, allylic, tertiary and neopentyl-type sites remain excluded.",
                         "Mapped reacting-center inversion and distant retention are checked. Unsupported stereo loss fails closed; unsigned centers remain unassigned.",
                         "One-site net substitution is not selective mono-substitution, efficient secondary SN2 or an experimental protocol. Hydroxide can also eliminate or deprotonate; alcohol proton equilibria, cyclization and product ratios are not generally predicted."] if site_sn2 else
                        ["SN2 inversion applies only to specified tetrahedral centers; a change in CIP priorities need not change the R/S letter."] if mechanism == "SN2" else
                        ["One-site acyl cleavage only; isolated saturated five/six-membered lactones and carbocyclic aryl esters are supported. Unspecified stereo remains unassigned.",
                         "Mapped retention does not predict epimerization, competing pathways or isolated stereochemistry.",
                         "Saponification reports carboxylate with one OH⁻ equivalent; excess-base OH deprotonation and acid work-up are separate, unimplemented stages."] if ester_cleavage else
                        ["Isolated C=C plus screened remote aliphatic alcohols only; other functional groups need separate, catalyst-specific validation.",
                         "Distant specified configurations are checked for retention. Geometry at the reduced C=C disappears; new stereocenters remain unassigned.",
                         "One H₂ equivalent per selected site is a net option, not a prediction of selective partial hydrogenation, syn face selection or isolated stereochemistry."] if site_hydrogenation else
                        ["Selected ordinary aldehyde/ketone plus screened alcohols, ethers and carbocyclic aromatic skeletons only; competing and unvalidated groups are rejected.",
                         "Distant specified configurations are checked for retention. Newly formed alcohol stereocenters remain unassigned; epimerization and facial selectivity are not predicted.",
                         "One H₂ per selected C=O is a net option, not selective partial reduction or a verified Pd/Pt protocol. Ring reduction, deoxygenation and catalyst-dependent side reactions are not predicted."] if site_carbonyl else
                        ["Selected ordinary primary/secondary alcohol with screened ethers/alcohols and bounded carbocyclic aromatic skeletons only; other oxidizable groups need separate validation.",
                         "Unaffected mapped configurations are checked; a specified reactive alcohol center loses its tetrahedral configuration only because it becomes a planar C=O. Near-site epimerization is not predicted.",
                         "One hypochlorite formula unit gives a balanced net stage, not a validated uncatalyzed protocol or selective mono-oxidation. Primary alcohol aldehyde-stage reporting does not guarantee isolation; further oxidation is a separate pathway.",
                         "pH, chlorination, oxidative cleavage, catalyst requirements and real reagent selectivity are not resolved. Do not mix household chemicals."] if site_oxidation else ["Connectivity model: no assigned stereochemical outcome."]) + [
                        "No rates, experimental yields, product ratios or measured energies are predicted."],
        "references": [{"title": "Chemistry reference", "url": reaction["sourceUrl"]}] +
                      ([{"title": "Concerted peracid oxygen/proton/carbonyl roles", "url": "https://chem.ucalgary.ca/courses/351/Carey5th/Ch06/ch6-9.html"},
                        {"title": "Textbook arrow model versus calculated electron-flow timing", "url": "https://pmc.ncbi.nlm.nih.gov/articles/PMC6769425/"}] if site_epoxidation else []) +
                      ([{"title": "Competing aqueous halohydrin pathway", "url": "https://openstax.org/books/organic-chemistry/pages/8-3-halohydrins-from-alkenes-addition-of-ho-x"}] if site_chlorination else []) +
                      ([{"title": "Halohydrin/solvent capture", "url": "https://openstax.org/books/organic-chemistry/pages/8-3-halohydrins-from-alkenes-addition-of-ho-x"},
                        {"title": "Intramolecular oxygen-capture examples (different reagents, not a universal Br2 protocol)", "url": "https://www.orgsyn.org/Content/pdfs/procedures/v89p0409.pdf"}] if site_bromination else
                       [{"title": "HX protonation and halide capture", "url": "https://openstax.org/books/organic-chemistry/pages/7-7-electrophilic-addition-reactions-of-alkenes"},
                        {"title": "HX-dependent ether cleavage", "url": "https://openstax.org/books/organic-chemistry/pages/18-3-reactions-of-ethers-acidic-cleavage"},
                        {"title": "Competing alcohol-to-halide chemistry", "url": "https://openstax.org/books/organic-chemistry/pages/17-6-reactions-of-alcohols"},
                        {"title": "Carbocation rearrangement risks", "url": "https://openstax.org/books/organic-chemistry/pages/7-11-evidence-for-the-mechanism-of-electrophilic-additions-carbocation-rearrangements"}] if site_hydrohalogenation else
                       [{"title": "Carbocation rearrangement risks", "url": "https://openstax.org/books/organic-chemistry/pages/7-11-evidence-for-the-mechanism-of-electrophilic-additions-carbocation-rearrangements"},
                        {"title": "Acid-sensitive ether cleavage", "url": "https://openstax.org/books/organic-chemistry/pages/18-3-reactions-of-ethers-acidic-cleavage"}] if site_hydration else
                       [{"title": "Resonance, nucleophile and solvent limits", "url": "https://openstax.org/books/organic-chemistry/pages/11-5-characteristics-of-the-sn1-reaction"},
                        {"title": "Screened secondary solvolysis and competing E1", "url": "https://www2.chemistry.msu.edu/faculty/reusch/VirtTxtJml/alhalrx3.htm"},
                        {"title": "Carbocation rearrangement risks", "url": "https://openstax.org/books/organic-chemistry/pages/7-11-evidence-for-the-mechanism-of-electrophilic-additions-carbocation-rearrangements"},
                        {"title": "Acid-sensitive ether cleavage", "url": "https://openstax.org/books/organic-chemistry/pages/18-3-reactions-of-ethers-acidic-cleavage"}] if site_sn1 else
                       [{"title": "Secondary/allylic solvolysis scope and competing pathways", "url": "https://www2.chemistry.msu.edu/faculty/reusch/VirtTxtJml/alhalrx3.htm"},
                        {"title": "Carbocation rearrangement risks", "url": "https://openstax.org/books/organic-chemistry/pages/7-11-evidence-for-the-mechanism-of-electrophilic-additions-carbocation-rearrangements"},
                        {"title": "Acid-sensitive ether cleavage", "url": "https://openstax.org/books/organic-chemistry/pages/18-3-reactions-of-ethers-acidic-cleavage"}] if site_e1 else
                       [{"title": "Ring-specific E2 conformational requirements", "url": "https://openstax.org/books/organic-chemistry/pages/11-9-the-e2-reaction-and-cyclohexane-conformation"}] if site_e2 else
                       [{"title": "Catalyst-specific aldehyde hydrogenation examples", "url": "https://doi.org/10.1002/cssc.200700086"}] if site_carbonyl else
                       [{"title": "Condition-specific hypochlorite oxidation and competing stages", "url": "https://www.orgsyn.org/demo.aspx?prep=CV8P0367"}] if site_oxidation else
                       [{"title": "Base-induced intramolecular ether competition", "url": "https://openstax.org/books/organic-chemistry/pages/18-4-cyclic-ethers-epoxides"}] if site_sn2 else []),
    }
    if mechanism == "Alkyne hydrohalogenation":
        result["alkyneHxModel"] = reaction["alkyneHxModel"]
        result["regioselectivity"] = reaction["regioselectivity"]
        result["capabilities"]["stereochemistry"] = reaction["stereochemistry"]["effect"]
        result["limitations"] = [
            "Actual selected HCl/HBr/HI supplies each entering H and X and is consumed. One equivalent gives vinyl halide, two give a geminal dihalide with both X on the chosen target. This is not X2 addition or a surrogate donor model.",
            "Terminal Markovnikov orientation is bounded. Symmetric orientations are grouped only under whole-graph chirality-aware equivalence. Unsymmetric internal targets are separate constitutional possibilities; no major/minor ratio or guaranteed complete addition is predicted.",
            "Internal first-stage E/Z is deliberately unassigned: generic ionic HX is not automatically anti/trans, E or Z. This blocks a single-geometry 3D assertion. Terminal CH2 products have no E/Z; saturated geminal endpoints have no local C=C configuration or new center.",
            "Distant mapped physical configurations survive the edit/serialization and CIP is recomputed, not copied. Specified propargylic configurations and adjacent highly branched or ring environments need separate validation.",
            "Screened remote primary alcohols/ordinary ethers have conditional 2D preserve-only equations, not proof they are inert toward HX. Oxygen substitution/cleavage and multi-alkyne competition block selective 3D. Nearby capture, carbonyls, peroxides, conjugation, cyclic alkynes and unvalidated groups remain excluded.",
            "HBr dry compatible-medium/explicit ambient net conformers have a bounded policy. HCl activation/formulation and two-equivalent HI compatibility are not established by current selectors; those stay 2D. Actual medium, supply, light/peroxide absence, stopping, kinetics and experimental yields remain unknown.",
            "No complete mapped vinyl-carbocation, elementary concerted or radical mechanism is implemented. Net H identities do not establish proton exchange, isotope histories or a catalytic mechanism.",
        ]
        result["references"].extend([
            {"title":"Formulation-specific HBr addition and competing ether cleavage (not a DMPU implementation)","url":"https://pmc.ncbi.nlm.nih.gov/articles/PMC5682921/"},
            {"title":"Catalyst/formulation-dependent alkyne hydrochlorination; transfer chemistry not implemented","url":"https://pmc.ncbi.nlm.nih.gov/articles/PMC7028031/"}])
    if mechanism == "Alkyne halogenation":
        result["alkyneHalogenModel"] = reaction["alkyneHalogenModel"]
        result["capabilities"]["stereochemistry"] = reaction["stereochemistry"]["effect"]
        result["limitations"] = [
            "One or two actual Br2/Cl2 equivalents are independently mapped. One gives C=C with one X per carbon; two give C–C with two identical X per carbon. No HX rule or mixed-halogen mode is inferred.",
            "In the bounded first-stage Br2 anti net model, incoming Br atoms lie opposite and CIP is independently reassigned, including terminal substrates. This does not claim exclusive E product or a stereoisomer ratio.",
            "Cl2 first-stage stereospecificity is not reliably established by these generic selectors: E/Z stays unsigned, conditional 2D only. Additional oxygen groups also need independent Cl2/capture validation.",
            "Selected saturation has no E/Z or newly specified local centers; unaffected physical configurations and mapped serialization must be preserved even when CIP letters change.",
            "Nearby nucleophilic O, cyclic/conjugated alkynes, competing alkenes/aromatic groups and unscreened functionality remain excluded. Multiple isolated alkynes retain only hypothetical one-site 2D equations; selective 3D is blocked.",
            "A dry compatible non-nucleophilic medium and explicit equivalent stage are model requirements, not full experimental conditions. Supply, stopping, kinetics, yields, light exposure and product ratios are unknown. Nucleophilic media, added activation and radical/heated conditions are not the same product model.",
            "Net transformation only: no complete mapped halonium intermediate or stable vinyl-carbocation mechanism is implemented.",
        ]
        result["references"].append({"title": "Chlorination side chemistry and stereochemical limitations (different photo-conditions, not permission for this model)", "url": "https://doi.org/10.1016/S0040-4020(01)82137-2"})
    if mechanism == "Alkyne partial hydrogenation":
        result["capabilities"]["stereochemistry"] = "validated internal cis/Z net syn addition; terminal E/Z not applicable; distant physical configurations retained and CIP reassigned"
        result["alkynePartialStereo"] = reaction["alkynePartialStereo"]
        result["limitations"] = [
            "One actual H2 per selected isolated acyclic C≡C with required Lindlar activation. Ordinary unpoisoned metal catalysts can continue to alkane; dissolving-metal trans reduction is not implemented.",
            "Internal cis/Z geometry is constructed from net syn addition and independently CIP-checked. Terminal products receive no E/Z label; distant mapped physical configurations must remain, even if their CIP letters change.",
            "Screened remote saturated aliphatic OH/ethers are bounded net spectators. Nearby oxygen, carbonyls, alkenes, aromatic/conjugated systems, cyclic alkynes and unvalidated directed environments remain excluded.",
            "Other well-separated C≡C sites remain unchanged in a theoretical one-site option, not predicted experimental mono-reduction. Equivalent choices are grouped with all original mapped site IDs retained.",
            "No mapped catalytic surface mechanism or discrete ionic/radical intermediates. Hydrogen maps describe net H2 provenance, not surface exchange. Pressure, solvent-specific performance, stopping, over-reduction, yields and product ratios are not predicted.",
        ]
        result["references"].append({"title": "Lindlar catalyst and partial reduction limitations", "url": "https://www.orgsyn.org/demo.aspx?prep=CV5P0880"})
    if mechanism == "Alkyne hydrogenation":
        result["capabilities"]["stereochemistry"] = "selected bond becomes saturated without E/Z or new local centers; distant physical configurations retained and CIP reassigned"
        result["alkyneCompleteModel"] = reaction["alkyneCompleteModel"]
        result["limitations"] = [
            "Two actual H2 equivalents saturate the selected isolated acyclic C≡C, adding two H to each carbon. The active-metal Pd/Pt selector is not the selective Lindlar model; no separate Ni/dissolving-metal catalyst profile is added.",
            "Screened remote saturated aliphatic OH/ethers and distant specified configurations are bounded net spectators. Conjugation, cyclic alkynes, alkenes, carbonyls, aromatic systems and nearby reactive environments remain excluded.",
            "Other isolated C≡C sites can also hydrogenate under active-metal conditions: independently selectable one-site equations are 2D bookkeeping only and block a selective 3D claim. No all-sites reduction product or experimental site distribution is invented.",
            "Former alkyne carbons are CH2/CH3, with no E/Z or newly assigned stereocenters. Distant physical configuration is checked independently of CIP letter changes and survives mapped serialization.",
            "H2 maps account for the four incoming H in the balanced net equation, not actual surface exchange. No discrete ionic/radical intermediate or catalytic surface mechanism is implemented.",
            "Hydrogen supply, catalyst support/loading, pressure, time, temperature dependence, solvent-specific performance, experimental completion and yields are not predicted. Calculated amounts are theoretical, not a protocol.",
        ]
        result["references"].append({"title": "Surface hydrogenation and competing unsaturation", "url": "https://openstax.org/books/organic-chemistry/pages/8-6-reduction-of-alkenes-hydrogenation"})
    if mechanism == "Alcohol dehydration":
        result["dehydrationModel"] = reaction["dehydrationModel"]
        result["capabilities"].update(regioselectivity="separate constitutional beta alternatives; no ratios", stereochemistry=reaction["stereochemistry"]["effect"], mappedMechanism="unsupported", energy="unsupported")
        result["limitations"] = [
            "Existing actual sulfuric acid is regenerated and excluded from net stoichiometry. Required acid/heated settings are bounded model assumptions, not a validated laboratory protocol.",
            reaction["dehydrationModel"]["mechanism"] + ". Alcohol protonation activates water departure; bare OH is not a valid elementary leaving group. No complete mapped acid cycle or primary-carbocation mechanism is displayed.",
            "Distinct beta products remain alternatives; no major/minor or E/Z ratio is assigned. Unresolved E/Z and remote oxygen competition keep conditional 2D and block a single selective 3D assertion.",
            "Exact net edits, neutral water inventory, unaffected bonds and physical spectator configurations are checked through serialization. Catalytic proton exchange, isotope histories, ether formation, isomerization and eventual conversion are not predicted.",
            "Cyclic, conjugated, nearby capture/cleavage, shift-prone and other unvalidated functional environments remain outside this bounded acyclic model."]
    if mechanism == "Alcohol substitution":
        result["alcoholSubstitutionModel"] = reaction["alcoholSubstitutionModel"]
        result["capabilities"].update(stereochemistry=reaction["stereochemistry"]["effect"], mappedMechanism="unsupported", energy="unsupported")
        result["limitations"] = [
            "Actual neutral HBr/HI activate methyl/primary/screened secondary/tertiary alcohol sites; the existing HCl scope stays tertiary only. Bare halide, HF, SOCl2 and PBr3 are not new activating modes.",
            reaction["alcoholSubstitutionModel"]["mode"] + ". Protonation makes water a suitable leaving group. No complete mapped activation mechanism is displayed and no bare OH displacement is claimed.",
            "No universal secondary-alcohol SN1/SN2 partition is assumed. Unresolved secondary/benzylic mode, reacting product configuration or other oxygen-site chemistry keeps conditional 2D and blocks an asserted 3D outcome.",
            "HX is consumed 1:1, contributing the product halogen and a net water hydrogen. Acid activation is not equivalent to a purely catalytic amount; exact solution proton/isotope exchange is not modeled.",
            "Unchanged mapped bonds and distant physical configurations are checked with independent CIP reassignment. No R/S letter-flipping rule, exact racemization ratio or conformer-derived configuration is used.",
            "Rearrangement, short intramolecular oxygen capture, complex ring/allylic pathways, heated tertiary elimination and ether formation are screened or explicitly unresolved. Other eligible sites are theoretical alternatives, not experimental selective conversion or additive yields."]
        result["references"].append({"title": "HX-dependent ether cleavage and formulation dependence", "url": "https://pubs.rsc.org/en/content/articlelanding/2017/ob/c7ob01096f"})
    if reaction.get("primaryOxidationModel"):
        result["primaryOxidationModel"] = reaction["primaryOxidationModel"]
        result["capabilities"].update(mappedMechanism="unsupported", energy="unsupported", oxidationEndpoint="unresolved; conditional first-stage net graph only")
        result["limitations"] = [
            "Primary aldehyde-stage net structure only. No aldehyde-selective hypochlorite profile is implemented; generic aqueous medium and First stage do not establish isolation or stopping before further oxidation.",
            "The preserved Phase 2C C–O-to-C=O edit retains original alcohol oxygen. One C–H and O–H form water with actual hypochlorite oxygen; the actual alkali chloride is represented. Formal atom/charge balance is not experimental isotope provenance or a complete catalyst mechanism.",
            "Other primary/secondary OH groups can oxidize; separate site choices are not experimentally selective mono-oxidation. Nearby closure, cleavage, unsaturation, aromatic chlorination, sensitive spectators and invalid stereo remain screened or unresolved, not automatically declared inert.",
            "Distant physical configurations and independently recalculated CIP are retained in the formal net graph. Alpha-carbonyl epimerization, selective endpoint chemistry and experimental product distributions are not established by conformer generation.",
            "No PCC, Dess–Martin, TEMPO, chromate, periodinane, hydride-transfer or radical mechanism was added. No H2 gas or direct primary-alcohol-to-acid product is generated. Do not mix household chemicals.",
            reaction["primaryOxidationModel"]["endpointLimitation"]]
    if reaction.get("secondaryOxidationModel"):
        result["secondaryOxidationModel"]=reaction["secondaryOxidationModel"]
        result["capabilities"].update(mappedMechanism="unsupported",energy="unsupported",oxidationEndpoint="conditional secondary ketone net model; condition and scope gates apply")
        result["limitations"]=[
            "Secondary C–OH becomes its original-oxygen planar ketone. The reacting center loses any tetrahedral configuration; distant physical stereo is retained and CIP recomputed.",
            "Only the explicit sodium hypochlorite/acetic-acid profile with bounded saturated mono-oxygen substrate scope and required settings can qualify theoretical 3D. Generic water is not that formulation. Other alcohols/ethers, aromatic groups and unvalidated counterions or rings remain conditional.",
            "Prolonged/excess oxidant, different pH, alpha-halogenation/haloform/cleavage and isolated product recovery are not predicted. Diol release is not ketone workup; no rates, yields or site selectivity are claimed.",
            "The net water/chloride accounting is not a complete hypochlorite ester or proton-exchange mechanism. No H2 gas, new oxidant or reagent-derived intermediate is invented. Do not mix household chemicals.",
            *reaction["secondaryOxidationModel"]["qualificationLimitations"]]
        result["references"].append({"title":"Stevens–Chapman–Weller secondary NaOCl oxidation, JOC 1980, 45, 2030–2032","url":reaction["secondaryOxidationModel"]["sourceUrl"]})
    if mechanism == "Aldehyde oxidation":
        result["limitations"] = [
            "Neutral acid reporting graph only: pH, acid/carboxylate speciation and isolated acid work-up are not established. No acidification or carboxylate transformation is implemented.",
            "Explicit unsupported activation, temperature, work-up or unknown condition fields block 3D; eligible net connectivity can still be inspected in conditional 2D.",
            "Other oxidizable sites may compete. Theoretical amounts assume complete conversion, not experimental yield or selective one-site oxidation.",
            "No complete mapped oxidation mechanism, hydrate/proton-transfer cycle or experimental isotope provenance is implemented.",
        ]
    return result

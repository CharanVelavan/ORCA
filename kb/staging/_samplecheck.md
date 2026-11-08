# Sample check (cross-model), kb/staging

Checked by a second model family against `corpus/raw/**/*.txt`. Checks what exact matching cannot: is the legal-status claim true, does the page or clause hold, is the quote relevant to its gap. Nothing was marked `verified: true`. No other file was edited.

Page convention: `\f` splits pages (uncollapsed, as in `_quotecheck.yaml`). Exception: `intl-3gpp-tr-38821.txt` contains 199,824 form feeds, so its page numbers are only meaningful after collapsing runs; the checker's pages for it match that collapsed count.

## Summary

| Check | Items | Verdict counts |
|---|---|---|
| 1. binding_basis fails (legal status) | 43 docs | binding_status CORRECT 26 (of which 6 have a basis that is contradicted or wrong in detail), CANNOT TELL 17, WRONG 0 |
| 2. page mismatches | 20 quotes | staged page WRONG 20/20; checker's found page CONFIRMED 20/20; clause number present on found page 18, unverified 1 (TRAI "paragraph 7(i)"), no clause 1 (UNOOSA) |
| 3. random sample of passing quotes (seed 8, n=30 of 450) | 30 quotes | RELEVANT 4, WEAK 13, WRONG-GAP 13; 6 quotes carry the placeholder why "Relevant wording located in extracted text..."; 1 why contradicts its quote (#6, "24/7") |

Global examples carry most of the problems: 22 of the 30 sampled quotes are global (19 of the 26 non-relevant verdicts are global), and all 11 3GPP TS and both 3GPP TR basis problems are global.

---

## Check 1. binding_basis fails (43)

Column "status" is the staged `binding_status`. "Basis" says whether the staged `binding_basis` is usable.

### Global (31)

| Doc | Staged status | Verdict | Verbatim words found in the document (page) | Basis fix |
|---|---|---|---|---|
| intl-3gpp-tr-22822 | advisory | CORRECT status, basis WRONG | "The present document has not been subject to any approval process by the 3GPP Organizational Partners and shall not be implemented. This Report is provided for future development work within 3GPP only." (p1) | The staged basis says TRs are "approved by 3GPP Technical Specification Groups". The document says the opposite (not approved, not for implementation). Replace the basis with the p1 sentence above. |
| intl-3gpp-tr-38821 | advisory | CORRECT status, basis WRONG | "...has not been subject to any approval process by the 3GPP Organizational Partners and shall not be implemented. This Specification is provided for future development work within 3GPP only." (p5) | Same as above. Use p5. Re-extract the .txt (form-feed run problem). |
| intl-3gpp-ts-22153 | advisory | CANNOT TELL | Not stated in the document. Only the ETSI "Important notice" and trademark boilerplate. "voluntary industry consensus standards" not found. | Source outside the corpus (3GPP/ETSI policy) or mark unverified. |
| intl-3gpp-ts-22261 | advisory | CANNOT TELL | Not stated (as above). | As above. |
| intl-3gpp-ts-23273 | advisory | CANNOT TELL | Not stated (as above). | As above. |
| intl-3gpp-ts-23501 | advisory | CANNOT TELL | Not stated (as above). | As above. |
| intl-3gpp-ts-23502 | advisory | CANNOT TELL | Not stated (as above). | As above. |
| intl-3gpp-ts-28541 | advisory | CANNOT TELL | Not stated (as above). | As above. |
| intl-3gpp-ts-32541 | advisory | CANNOT TELL | Not stated (as above). | As above. |
| intl-3gpp-ts-33501 | advisory | CANNOT TELL | Not stated (ETSI "Important notice", p2). | As above. |
| intl-3gpp-ts-33511 | advisory | CANNOT TELL | Not stated (as above). | As above. |
| intl-3gpp-ts-38300 | advisory | CANNOT TELL | Not stated (as above). | As above. |
| intl-3gpp-ts-38401 | advisory | CANNOT TELL | Not stated (as above). | As above. |
| enisa-eecc-incident-reporting-guideline | advisory | CORRECT (basis fix) | "This publication should not be construed to be a legal action of ENISA ... unless adopted pursuant to the Regulation (EU) No 2019/881." (p2); "we provide guidance to national authorities supervising security in the electronic communications" (p5) | Staged sentence "This document is not binding..." is not in the text. Use the p2 or p5 sentence. |
| enisa-eecc-security-measures-guideline | advisory | CORRECT (basis fix) | "Neither the high-level security objectives nor the detailed security measures should be seen as binding recommendations about which are appropriate security measures for providers to take." (p6) | Use the p6 sentence. (p5 "non-binding technical guidelines" refers to the 2014 Art. 13a guidelines, not this one.) |
| enisa-space-threat-landscape-2025 | advisory | CORRECT (basis fix) | "It does not endorse a regulatory obligation of ENISA or of ENISA bodies pursuant to the Regulation (EU) No 2019/881." (p3) | Use p3 sentence. |
| eu-5g-cybersecurity-toolbox-2020 | advisory | CANNOT TELL | Document does not state its legal status. It describes the Commission Recommendation of 26 March 2019 (p3). | Mark "not stated in the document" or cite the Recommendation's own status. |
| eu-cer-2022-2557 | binding | CORRECT (basis split) | "This Directive shall enter into force on the twentieth day following that of its publication in the Official Journal of the European Union." (p29, Art. 28); "This Directive is addressed to the Member States." (p29, Art. 29) | The two sentences are verbatim but separated by the heading "Article 29 Addressees", so the joined string fails. Quote them separately. |
| eu-cer-article-13-guidelines-2026 | advisory | CORRECT (basis fix) | "This Communication is not legally binding and does not affect the interpretation of EU law by the Court of Justice of the European Union." (p1, para 4) | Staged "These guidelines are non-binding." is not in the text. Use p1 para 4. |
| eu-eecc-2018-1972 | binding | CORRECT | "Article 126 Entry into force This Directive shall enter into force on the third day following..." (p154); "Article 127 Addressees This Directive is addressed to the Member States." (p154) | Quote the two sentences separately. |
| eu-nis2-2022 | binding | CORRECT | "Article 45 Entry into force This Directive shall enter into force on the twentieth day..." and "Article 46 Addressees This Directive is addressed to the Member States." (p1) | Single-page web extract, so page 1 is the only page. |
| eu-space-act-proposal-2025 | draft | CORRECT (basis fix) | "Proposal for a REGULATION OF THE EUROPEAN PARLIAMENT AND OF THE COUNCIL ... COM(2025) 335 final 2025/0335(COD)" (p1) | Staged "COM/2025/" is not verbatim; use "COM(2025) 335 final 2025/0335(COD)". |
| itu-d-netp-guidelines-2020 | advisory | CANNOT TELL | "not legally binding" not found. p9: "This guide is intended primarily for national authorities responsible for the development and implementation of the NETP". | Use the p9 sentence and mark the legal status as not stated. |
| itu-e108-2016 | advisory | CORRECT (basis fix) | "Compliance with this Recommendation is voluntary. However, the Recommendation may contain certain mandatory provisions..." (p4) | Staged "non-binding international standards adopted by consensus" not in text. Use p4. |
| itu-x1056-2020 | advisory | CORRECT (basis fix) | Same p4 sentence. | As E.108. |
| itu-x1060-2021 | advisory | CORRECT (basis fix) | Same p4 sentence. | As E.108. |
| itu-x1812-2023 | advisory | CORRECT (basis fix) | Same p4 sentence. | As E.108. |
| itu-r-res644-2019 | binding | CANNOT TELL | Document is the RR Resolutions and Recommendations 2024 edition. p5 conventions refer to "the texts of the Resolutions included in Volume 3". No statement that they are binding. | Also an ID problem: see fix list item 5 (id says res644; YAML title says Res 646/647; the .txt has 0 hits for "Resolution 644" and 0 for "Resolution 647"). |
| itu-radio-regulations-app10 | binding | CANNOT TELL | p5: "This revision of the Radio Regulations, complementing the Constitution and the Convention of the International Telecommunication Union..." No "binding" or "Article 4" wording found. | Constitution is in corpus (`itu-constitution-art40`, p47-48, "ARTICLE 4 Instruments of the Union"). The sentence "bind all Member States" was not found in it. Quote the Art. 4 text from the Constitution file, or mark unverified. |
| us-fcc-mdri-order-2022 | binding | CORRECT status, basis WRONG (date) | "Adopted: June 27, 2022 Released: July 6, 2022" (p1). "Add § 4.17 to read as follows" and "The authority citation for part 4 continues to read as follows" (p23). | Staged "Adopted: June 28" is wrong (June 27). Use p1 and p23 text. |
| us-fcc-part-4-outage | binding | CORRECT (basis not in this doc) | Staged "Authority: 47 U.S.C..." line is in the MDRI order (p23), not in this file. This file: "the Federal Communications Commission is setting forth requirements pertinent to the reporting of disruptions" (p1, §4.1(a)). | Replace with §4.1(a) sentence. |

### India (12)

| Doc | Staged status | Verdict | Verbatim words found (page) | Basis fix |
|---|---|---|---|---|
| in-ctir-2024 | binding | CORRECT (basis abridged) | "Now, therefore, in exercise of the powers conferred by sub-section (4) of section 22 read with clause (w) of sub-section (2) of section 56 of the Telecommunications Act, 2023 (44 of 2023), the Central Government hereby makes the following rules, namely:-" (p6). "These rules may be called the Telecommunications (Critical T..." (p6) | Staged text drops "clause (w) of sub-section (2)" and uses capital "In". Use the p6 sentence. |
| in-dot-ctir-2024 | binding | CORRECT, DUPLICATE | Byte-identical .txt to in-ctir-2024 (same sha256 in both YAMLs). | Remove one entry or make one a pointer. |
| in-dot-telecom-standards-rules-2025 | binding | CORRECT (basis abridged) | "...in exercise of the powers conferred by section 19 read with clause (zj)..." and "the Central Government hereby makes the following rules, namely" (p6). | Final title on p6 is "Telecommunications (Framework to Notify Standards, Conformity Assessment and Certification) Rules, 2025". The staged basis uses the draft wording. |
| in-tcsr-2024 | binding | CORRECT (basis abridged) | "Now, therefore, in exercise of the powers conferred by sub-section (1) of section 22 read with clause (v) to sub-section (2) of section 56..." and "the Central Government hereby makes the following rules, namely:-" (p2). | Staged "section 22 read with section 56" is not verbatim. Use p2. |
| in-dot-unified-licence | binding | CORRECT (basis paraphrase) | Template text, p2: "LICENSE AGREEMENT FOR UNIFIED LICENSE This Agreement is made on the _______ day of ..." Binding conditions: "Any order passed under these statutes shall be binding on the licensee." (p17). | Staged "This Licence Agreement is made on this day ... Department of Telecommunications and the Licensee" is not verbatim. The file is a blank template, not an executed licence. Say so. |
| in-mha-ners-guidelines-2015 | advisory | CORRECT (basis paraphrase) | "These guidelines would provide clarity to the State Governments/UT Administrations on the implementation aspect of the entire project." (p3) | Use p3 sentence. |
| in-national-cyber-security-policy-2013 | advisory | CANNOT TELL | Document calls itself a policy. Closest text, p1: "providing right kind of focus for creating secure computing environment and adequate trust & confidence in electronic transactions..." Legal status not stated. | Mark "not stated" (a non-statutory policy). |
| in-ndma-communication-guidelines | advisory | CANNOT TELL | "under the Disaster Management Act, 2005" is not a stated legal basis. The Act is only mentioned as context (p46-47). "formulation of these Guidelines" (p16). | Remove the legal-basis claim or mark "not stated". |
| in-rbi-it-outsourcing-directions-2023 | binding | CORRECT (basis fix) | "the finalised Reserve Bank of India (Outsourcing of Information Technology Services) Directions, 2023 are enclosed herewith" and "the enclosed Directions shall come into effect from October 1, 2023" (p1). Header: "RBI/2023-24/102 DoS.CO.CSITEG/SEC.1/31.01.015/2023-24 April 10, 2023" (p1). | Use these sentences. The file is a single-page web capture. |
| in-space-policy-2023 | advisory | CORRECT status, basis WRONG | Staged "approved by the Cabinet Committee on Security" is not in the text. p5: "...the reform vision approved by Cabinet." Binding sentence: "the decisions of IN-SPACe shall be binding on the operators of such facilities" (p8). | Use p5 for approval wording. Status as a policy is correct. |
| in-trai-ppdr-consultation-2017 | advisory | CORRECT status, basis WRONG (number) | p1: "Consultation Paper No. 15/2017 ... Next Generation Public Protection and Disaster Relief (PPDR) communication networks", 9 October 2017. p9: "as per Section 11(a) of TRAI Act, 1997". | Staged "No. 12/2017" is wrong: use 15/2017. Staged "issued under the TRAI Act" is supported by p9. |
| inspace-ngp-2024 | binding | CORRECT in part, basis WRONG | p151: "IN-SPACe shall periodically issue guidelines and procedures, that would among other things promote ease of doing business." ("and provide regulatory certainty" is NOT in the text.) p152: "the decisions of IN-SPACe shall be binding on the operators of such facilities." p19: "must be in strict conformity with the applicable laws, rules, and regulations of India." | Drop "and provide regulatory certainty". Use the p152 binding sentence for the binding claim. |

**Binding verdict totals (43):** CORRECT 26, CANNOT TELL 17, WRONG 0. Of the 26, six have a staged basis that is contradicted or wrong in detail: intl-3gpp-tr-22822, intl-3gpp-tr-38821, in-space-policy-2023, in-trai-ppdr-consultation-2017, us-fcc-mdri-order-2022, inspace-ngp-2024. In-dot-ctir-2024 is a duplicate.

---

## Check 2. Page mismatches (20)

Staged page is wrong in all 20. The checker's `found_on_pages` is confirmed by an independent search. "Clause" = whether the staged clause number appears on the found page (weak where the number also appears in a TOC).

| Doc | n | Staged page | Correct page | Clause | Note |
|---|---|---|---|---|---|
| intl-3gpp-tr-22822 | 0 | 13 | 5 | 5.4.1 on p5: still right | |
| intl-3gpp-tr-22822 | 1 | 13 | 5 | 5.4.1 on p5: still right | |
| intl-3gpp-tr-22822 | 2 | 26 | 5 | 6.2 on p5: still right | Quote says PR 6.2.006 |
| intl-3gpp-tr-38821 | 0 | 19 | 10 | 5.1.1 on p10: still right | Form-feed run file |
| intl-3gpp-tr-38821 | 1 | 19 | 10 | 5.1.1 on p10: still right | Form-feed run file |
| intl-3gpp-tr-38821 | 2 | 22 | 10 | 5.2.1.1 on p10: still right | GAP-IN-05 label, see item 3 of fix list |
| intl-3gpp-ts-22261 | 0 | 27 | 5 | 6.7.2 on p5: still right | |
| intl-3gpp-ts-22261 | 1 | 22 | 5 | 6.3.2.3 on p5: still right | |
| intl-3gpp-ts-22261 | 2 | 51 | 5 | 6.31.2.1 on p5: still right | Number may be TOC-only; check |
| intl-3gpp-ts-23273 | 0 | 15 | 4 | 4.1a.1 on p4: still right | |
| intl-3gpp-ts-23273 | 1 | 44 | 4 | 5.11 on p4: still right | |
| intl-3gpp-ts-23273 | 2 | 44 | 4 | 5.11 on p4: still right | |
| intl-3gpp-ts-24501 | 0 | 64 | 5 | 4.4.4.1 on p5: still right | |
| intl-3gpp-ts-24501 | 1 | 36 | 4 | 3.1 on p4: plausible | "3.1" occurs on many pages; weak |
| intl-3gpp-ts-24501 | 2 | 36 | 4 | 3.1 on p4: plausible | As above |
| intl-3gpp-ts-33511 | 0 | 7 | 5 | 4.2.2.1.1 on p5: still right | |
| intl-3gpp-ts-33511 | 1 | 7 | 5 | 4.2.2.1.1 on p5: still right | |
| intl-3gpp-ts-33511 | 2 | 23 | 5 | 4.4.4 on p5: still right | |
| intl-unoosa-debris-guidelines-2007 | 0 | 1 | 5 (uncollapsed); 4 if runs collapsed | none ("not stated") | gap None. Quote is about UN debris history, not any listed gap. Drop. |
| india/in-trai-direction-cellular-outages-2024 | 0 | 17 | 3 | "paragraph 7(i)": NOT found in text | Quote is on p3 (Annexure-II). Also an outage clock, not a cyber clock. Fix clause. |

---

## Check 3. Random sample of passing quotes (seed 8, 30 of 450)

Population: the 450 `result: pass` quotes in file order; `random.seed(8)`, `random.sample(..., 30)`.

Verdict key: RELEVANT = supports its gap and why matches. WEAK = true and on-topic, but does not show the gap. WRONG-GAP = quote is about a different subject than the gap label.

| # | Doc | n | Gap (staged) | Verdict | Reason |
|---|---|---|---|---|---|
| 1 | intl-3gpp-ts-38300 | 0 | 05 | WEAK | True (UE is GNSS-capable in Rel-17 NTN), but a capability rule, not a gap; GAP-IN-05 not in the spec list. |
| 2 | global/sg-imda-cop-tsr | 1 | None | WEAK | Penalty power shows binding force of a resilience code; no listed gap. |
| 3 | uk-dsit-space-ground-cloud-cyber | 1 | 06 | WRONG-GAP | Quote is GOV.UK navigation text; topic is ground-segment cloud, not feeder/ISL security. Placeholder why. |
| 4 | eu-nis2-2022 | 1 | 01 | RELEVANT | 24-hour early-warning clock for significant incidents; why matches. |
| 5 | intl-3gpp-ts-23502 | 0 | 05 | WEAK | True TAC rule for satellite cells; not a listed gap. |
| 6 | india/in-mha-ners-guidelines-2015 | 2 | 03 | WRONG-GAP | PSAP definition; nothing on backup capacity. Why says "24/7", which is not in the quote. |
| 7 | au-telecom-consumer-protection-act | 2 | 03 | WRONG-GAP | Garbled schedule clause on breach of a standard; nothing on capacity priority. Placeholder why. |
| 8 | eu-cer-article-13-guidelines-2026 | 2 | 08 | WEAK | Hot/warm/cold DR sites; not a clean-path check before failover. |
| 9 | eu-space-act-proposal-2025 | 1 | 09 | RELEVANT | Recital: space cyber not comprehensively covered by general EU law; supports "no binding satellite baseline". It is a draft, so it shows the gap, not a binding rule. |
| 10 | intl-esa-cyber-resilience-framework | 1 | None | WEAK | Describes ESA's cyber centre scope; no gap link. |
| 11 | india/in-telact-2023 | 1 | 03 | WEAK | Power to take temporary possession of networks in an emergency; a reallocation power, not a priority ranking. |
| 12 | india/in-abdm-health-data-management-policy | 0 | 08 | WRONG-GAP | Generic information-security programme; nothing on failover path checks. |
| 13 | intl-3gpp-ts-32541 | 0 | 07 | WEAK | Accurate self-healing purpose (on-topic for ORCA); GAP-IN-07 not in the spec list. |
| 14 | us-cisa-circia-nprm-2024 | 2 | 02 | WRONG-GAP | Supplemental reports to CISA are incident reporting (GAP-01), not a duty to warn dependent services. Proposed rule. |
| 15 | india/in-dot-telecom-cyber-security-amendment-rules-2025 | 1 | None | WEAK | Suspension power over identifiers; containment, no listed gap. |
| 16 | au-acma-emergency-call-determination-2019 | 0 | 02 | WEAK | Quote is a page title with raw HTML markup; no substance. Placeholder why. |
| 17 | us-fcc-part-4-outage | 0 | 01 | RELEVANT | 120-minute notification for satellite outages, including inter-satellite links (also supports GAP-06). |
| 18 | us-nist-ir-8441-2023 | 2 | 06 | WRONG-GAP | Statement of regulatory status ("voluntary", "no statutory authority"); belongs to GAP-09. |
| 19 | us-fcc-mdri-order-2022 | 0 | 03 | WEAK | Mandatory disaster procedures for mobile providers; capacity-sharing context, no priority ranking. |
| 20 | uk-ofcom-backup-power-emergency-guidance | 2 | 03 | WRONG-GAP | Consumer backup power for emergency calls on broadband; belongs to GAP-04 (battery hours). Guidance is non-binding. Placeholder why. |
| 21 | us-whitehouse-nsm22-2024 | 0 | 03 | WEAK | Defines critical infrastructure; a precondition for priority, not a ranking. |
| 22 | india/in-dot-ctir-2024 | 1 | 01 | RELEVANT | Six-hour security incident intimation to Central Government; correct. Duplicate of in-ctir-2024. |
| 23 | india/in-tn-disaster-management-agency | 2 | 02 | WRONG-GAP | State disaster authority functions; not a duty to warn. Quote is untranslated Tamil. |
| 24 | us-cisa-cpgs-2023 | 0 | 06 | WRONG-GAP | Definition of performance goals; not link security. |
| 25 | eu-commission-reg-2023-894 | 1 | 02 | WRONG-GAP | Revises incident reporting templates: at most GAP-01. Placeholder why. |
| 26 | us-nist-ir-8441-2023 | 1 | 08 | WEAK | Trust levels across HSN components; relevant to path trust, not a clean-path check before failover. |
| 27 | intl-3gpp-ts-38401 | 0 | 06 | WRONG-GAP | gNB-CU/DU architecture; not link security. |
| 28 | india/in-rbi-psos-cyber-resilience-2024 | 3 | 08 | WEAK | Separate seismic-zone DR site; geographic resilience, not a clean-path check. Page not found; clause "Paragraph 23" unverified. |
| 29 | ae-tdra-interconnection-2006 | 1 | 03 | WRONG-GAP | Universal-call interoperability principle; not priority ranking. Placeholder why. |
| 30 | india/in-mha-ners-guidelines-2015 | 0 | 03 | WRONG-GAP | Committee recommendation for an emergency response system; not priority ranking. |

**Sample totals:** RELEVANT 4 (#4, #9, #17, #22), WEAK 13, WRONG-GAP 13. Six placeholder whys (#3, #7, #16, #20, #25, #29). One why contradicts its quote (#6).

---

## Fix list (highest impact first; global first)

Global examples first, since their accuracy is scored as critical.

1. **Global 3GPP TR 22.822 and TR 38.821: basis contradicts the document.** Staged text says "approved by 3GPP Technical Specification Groups". Both say the document "has not been subject to any approval process ... and shall not be implemented" (p1 and p5). Replace the basis. Re-extract `intl-3gpp-tr-38821.txt`, which has 199,824 form feeds.
2. **Global sample relevance: 26 of 30 passing quotes do not support their gap.** Re-map these labels before using them. Clear mis-maps:
   - #18 (NIST IR 8441 "voluntary" status statement): belongs to GAP-09, not GAP-06.
   - #20 (Ofcom backup power): GAP-04, not GAP-03.
   - #14 (CISA CIRCIA supplemental reports) and #25 (EU Reg 2023/894): GAP-01, not GAP-02.
   - #3, #24, #27: not GAP-06.
   - #12 (ABDM): not GAP-08.
   - Remove the six placeholder "Relevant wording located..." rows, and fix the #6 "24/7" why.
   - The UNOOSA item (gap None, page mismatch) should be dropped.
3. **Global 3GPP TS (11 docs): "voluntary consensus standards" is not in any of them.** Legal status is not stated in the corpus. Either source it outside the corpus or mark the status unverified. Do not mark it as verified from these files. Also the TS 38.300 and TS 23.502 quotes are true, but GAP-IN-05 and 07 are not in the spec list.
4. **Global ITU and EU basis statements not in the text.** ITU-D NETP, ITU RR Appendix 10 (Constitution Art. 4 is in corpus, but "bind all Member States" was not found in it), EU 5G Toolbox: all CANNOT TELL. ITU-T E.108, X.1056, X.1060, X.1812 need the p4 sentence "Compliance with this Recommendation is voluntary...". EU CER/EECC/NIS2 need the two sentences quoted separately (they are split by an Article heading).
5. **ITU RR Resolutions file: ID and content do not match.** Filename `itu-r-res644-2019`, YAML title "Resolution 647 (Rev. WRC-19) & Resolution 646", but the .txt has 0 mentions of "Resolution 644" and 0 of "Resolution 647", and 7 of "Resolution 646". Confirm which resolution the quotes come from and rename the entry.
6. **Page numbers: all 20 staged pages are wrong.** Use the found pages listed in Check 2. Staged page for UNOOSA is 1; correct is 5.
7. **India duplicate:** `in-ctir-2024` and `in-dot-ctir-2024` are byte-identical (same sha256 in both YAMLs). Remove one.
8. **India basis errors:**
   - TRAI PPDR consultation: "No. 12/2017" should be "No. 15/2017".
   - Indian Space Policy 2023: "approved by the Cabinet Committee on Security" should be "approved by Cabinet" (p5).
   - FCC MDRI order: "Adopted June 28" should be June 27, 2022.
   - Telecom standards 2025: final title is "Framework to Notify Standards, Conformity Assessment and Certification".
   - IN-SPACe NGP: drop "and provide regulatory certainty".
   - NDMA guidelines: the Disaster Management Act is not stated as their legal basis.
   - TRAI outage direction: clause "paragraph 7(i)" not found in the text.
9. **Unverified statements to keep as CANNOT TELL:** National Cyber Security Policy 2013, NDMA guidelines, ITU-D NETP.

Not changed in any file: `verified` remains false everywhere; no commit.

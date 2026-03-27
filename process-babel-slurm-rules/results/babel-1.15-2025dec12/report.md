# Babel 1.15 SLURM Run Analysis Report

*Generated: 2026-02-27 18:12*


## 1. Run Summary

| Run | Start | End | Duration | Total Jobs | Succeeded | Failed | Status |
|-----|-------|-----|----------|------------|-----------|--------|--------|
| run-1 | 2025-12-08 21:09 | 2025-12-09 20:54 | 23h 44m | 219 | 212 | 7 | ✗ failed |
| run-2 | 2025-12-09 22:58 | 2025-12-09 23:29 | 31m | 55 | 53 | 2 | ✗ failed |
| run-3 | 2025-12-10 03:49 | 2025-12-11 02:00 | 22h 10m | 27 | 26 | 1 | ✗ failed |
| run-4 | 2025-12-11 04:49 | 2025-12-11 05:21 | 32m | 1 | 0 | 1 | ✗ failed |
| run-5 | 2025-12-11 06:18 | 2025-12-11 06:28 | 9m | 1 | 0 | 1 | ✗ failed |
| run-6 | 2025-12-11 08:53 | 2025-12-11 22:10 | 13h 17m | 63 | 61 | 2 | ✗ failed |
| run-7 | 2025-12-12 21:49 | 2025-12-13 00:41 | 2h 52m | 32 | 32 | 0 | ✓ completed |

## 2. Failed Rules Report

| Rule | Run | SLURM Job ID | Error Type | Error Message | Eventually Succeeded? |
|------|-----|--------------|------------|---------------|----------------------|
| check_for_identically_labeled_cliques | run-6 | 75261 | — | — | Yes |
| check_synonyms_gzipped_files | run-6 | 75255 | AssertionError | Expected files in directory babel_outputs/synonyms to be equal to {'Macromolecul | Yes |
| chemical_chebi_ids | run-1 | 74159 | HTTPError | HTTP Error 503: Service Temporarily Unavailable | Yes |
| disease_manual_concord | run-1 | 74074 | RuntimeError | Found 1 elements on line UMLS:C0011847 oio:exactMatch MONDO:0005148 | Yes |
| get_HMDB | run-1 | 74071 | HTTPError | HTTP Error 504: Gateway Time-out | Yes |
| get_anatomy_obo_relationships | run-1 | 74149 | JSONDecodeError | Invalid control character at: line 2909294 column 46 (char 81477655) | Yes |
| get_chemical_unichem_relationships | run-1 | 74271 | EOFError | Compressed file ended before the end-of-stream marker was reached | Yes |
| get_chemical_unichem_relationships | run-2 | 74606 | EOFError | Compressed file ended before the end-of-stream marker was reached | Yes |
| get_chemical_unichem_relationships | run-3 | 74677 | EOFError | Compressed file ended before the end-of-stream marker was reached | Yes |
| get_ensembl | run-1 | 74085 | _BiomartException | Query ERROR: caught BioMart::Exception::Usage: Too many attributes selected for  | Yes |
| get_ensembl | run-2 | 74582 | _BiomartException | No internet connection available! | Yes |
| get_unichem | run-4 | 74978 | RuntimeError | Could not download and verify http://ftp.ebi.ac.uk/pub/databases/chembl/UniChem/ | Yes |
| get_unichem | run-5 | 75001 | RuntimeError | Could not download and verify http://ftp.ebi.ac.uk/pub/databases/chembl/UniChem/ | Yes |
| pubchem_rxnorm_annotations | run-1 | 74155 | ConnectionError | HTTPSConnectionPool(host='pubchem.ncbi.nlm.nih.gov', port=443): Max retries exce | Yes |

## 3. Job Timing Report

*Jobs where actual duration was >90% of allocated runtime are marked **⚠ UNDER** (may need more); <10% are marked **💤 OVER** (may be over-provisioned).*

| Rule | Run | Wildcards | Allocated (min) | Actual (min) | % Used | Status |
|------|-----|-----------|-----------------|--------------|--------|--------|
| get_ensembl | run-3 |  | 360 | 347.1 | 96.4% ⚠ UNDER | success |
| chemical | run-6 |  | 120 | 114.3 | 95.3% ⚠ UNDER | success |
| generate_pubmed_compendia | run-7 |  | 120 | 101.0 | 84.2% | success |
| generate_pubmed_concords | run-1 |  | 1440 | 1180.3 | 82.0% | success |
| generate_pubmed_compendia | run-1 |  | 120 | 96.6 | 80.5% | success |
| geneprotein_conflated_synonyms | run-3 |  | 360 | 288.4 | 80.1% | success |
| chemical_compendia | run-6 |  | 360 | 267.7 | 74.4% | success |
| protein_compendia | run-3 |  | 720 | 406.6 | 56.5% | success |
| gene_compendia | run-3 |  | 360 | 201.6 | 56.0% | success |
| untyped_chemical_compendia | run-6 |  | 120 | 63.5 | 53.0% | success |
| download_pubmed | run-1 |  | 120 | 60.6 | 50.5% | success |
| drugchemical_conflated_synonyms | run-6 |  | 360 | 166.8 | 46.3% | success |
| generate_kgx | run-6 | filename=SmallMolecule | 360 | 157.9 | 43.9% | success |
| gene | run-3 |  | 120 | 49.7 | 41.4% | success |
| chemical_unichem_concordia | run-6 |  | 120 | 45.5 | 37.9% | success |
| generate_sapbert_training_data | run-3 | filename=GeneProteinConflated.txt | 360 | 134.8 | 37.4% | success |
| protein | run-3 |  | 360 | 128.1 | 35.6% | success |
| geneprotein_conflation | run-3 |  | 120 | 42.2 | 35.2% | success |
| generate_kgx | run-3 | filename=Protein | 360 | 114.8 | 31.9% | success |
| get_uniprotkb_trembl | run-1 |  | 120 | 37.9 | 31.6% | success |
| leftover_umls | run-6 |  | 120 | 37.4 | 31.2% | success |
| leftover_umls | run-7 |  | 120 | 37.0 | 30.9% | success |
| generate_sapbert_training_data | run-3 | filename=Protein.txt | 360 | 104.8 | 29.1% | success |
| generate_sapbert_training_data | run-6 | filename=DrugChemicalConflated.txt | 360 | 97.6 | 27.1% | success |
| generate_content_report_for_compendium_Protein | run-3 |  | 120 | 29.7 | 24.8% | success |
| chembl_labels_and_smiles | run-1 |  | 120 | 25.6 | 21.3% | success |
| drugchemical_conflation | run-6 |  | 120 | 25.5 | 21.3% | success |
| generate_kgx | run-1 | filename=Publication | 360 | 70.1 | 19.5% | success |
| check_protein | run-3 |  | 120 | 23.2 | 19.3% | success |
| generate_kgx | run-7 | filename=Publication | 360 | 68.9 | 19.1% | success |
| generate_by_clique_report | run-6 |  | 120 | 22.5 | 18.8% | success |
| get_anatomy_obo_relationships | run-2 |  | 120 | 21.8 | 18.2% | success |
| check_protein_completeness | run-3 |  | 120 | 21.7 | 18.1% | success |
| get_unichem | run-1 |  | 120 | 20.6 | 17.1% | success |
| geneprotein_uniprot_relationships | run-1 |  | 120 | 19.7 | 16.4% | success |
| extract_taxon_ids_from_uniprotkb | run-1 |  | 120 | 19.1 | 15.9% | success |
| get_protein_uniprotkb_ensembl_relationships | run-1 |  | 120 | 19.0 | 15.9% | success |
| generate_content_report_for_compendium_SmallMolecule | run-6 |  | 120 | 19.0 | 15.8% | success |
| get_chemical_unichem_relationships | run-6 |  | 120 | 18.0 | 15.0% | success |
| generate_by_clique_report | run-7 |  | 120 | 17.9 | 14.9% | success |
| get_uniprotkb_idmapping | run-1 |  | 120 | 17.5 | 14.6% | success |
| get_protein_pr_uniprotkb_relationships | run-1 |  | 120 | 17.5 | 14.6% | success |
| export_synonyms_to_duckdb | run-3 | filename=GeneProteinConflated | 120 | 17.2 | 14.3% | success |
| get_uniprotkb_labels | run-1 |  | 120 | 16.5 | 13.8% | success |
| verify_pubmed | run-1 |  | 120 | 16.5 | 13.8% | success |
| check_chemical_completeness | run-6 |  | 120 | 16.0 | 13.3% | success |
| check_small_molecule | run-6 |  | 120 | 16.0 | 13.3% | success |
| generate_kgx | run-3 | filename=Gene | 360 | 47.9 | 13.3% | success |
| export_synonyms_to_duckdb | run-3 | filename=Protein | 120 | 14.2 | 11.8% | success |
| download_umls | run-1 |  | 120 | 13.3 | 11.1% | success |
| export_compendia_to_duckdb | run-3 | filename=Protein | 360 | 39.7 | 11.0% | success |
| get_HMDB | run-2 |  | 120 | 12.9 | 10.8% | success |
| check_for_duplicate_clique_leaders | run-6 |  | 120 | 12.5 | 10.4% | success |
| generate_sapbert_training_data | run-3 | filename=Gene.txt | 360 | 35.5 | 9.9% 💤 OVER | success |
| hmdb_labels_and_synonyms | run-2 |  | 120 | 11.3 | 9.5% 💤 OVER | success |
| check_for_duplicate_clique_leaders | run-7 |  | 120 | 11.3 | 9.5% 💤 OVER | success |
| get_obo_synonyms | run-1 |  | 120 | 11.2 | 9.3% 💤 OVER | success |
| generate_content_report_for_compendium_Gene | run-3 |  | 120 | 10.7 | 8.9% 💤 OVER | success |
| get_ncbigene_labels_synonyms_and_taxa | run-1 |  | 120 | 10.6 | 8.8% 💤 OVER | success |
| get_obo_labels | run-1 |  | 120 | 10.5 | 8.7% 💤 OVER | success |
| get_unichem | run-2 |  | 120 | 10.4 | 8.7% 💤 OVER | success |
| export_synonyms_to_duckdb | run-6 | filename=DrugChemicalConflated | 120 | 10.2 | 8.5% 💤 OVER | success |
| export_compendia_to_duckdb | run-6 | filename=SmallMolecule | 360 | 29.2 | 8.1% 💤 OVER | success |
| generate_curie_report | run-6 |  | 120 | 8.8 | 7.4% 💤 OVER | success |
| generate_curie_report | run-7 |  | 120 | 8.8 | 7.4% 💤 OVER | success |
| check_for_identically_labeled_cliques | run-7 |  | 120 | 8.8 | 7.4% 💤 OVER | success |
| check_for_duplicate_curies | run-6 |  | 120 | 8.2 | 6.8% 💤 OVER | success |
| check_for_duplicate_curies | run-7 |  | 120 | 8.2 | 6.8% 💤 OVER | success |
| check_gene | run-3 |  | 120 | 8.2 | 6.8% 💤 OVER | success |
| check_gene_completeness | run-3 |  | 120 | 8.2 | 6.8% 💤 OVER | success |
| get_icrdf | run-1 |  | 120 | 7.8 | 6.5% 💤 OVER | success |
| keggcompound_labels | run-1 |  | 120 | 7.3 | 6.1% 💤 OVER | success |
| generate_content_report_for_compendium_Publication | run-1 |  | 120 | 7.0 | 5.8% 💤 OVER | success |
| generate_content_report_for_compendium_Publication | run-7 |  | 120 | 7.0 | 5.8% 💤 OVER | success |
| taxon_compendia | run-1 |  | 120 | 6.8 | 5.7% 💤 OVER | success |
| anatomy_compendia | run-2 |  | 120 | 6.8 | 5.7% 💤 OVER | success |
| chemical_pubchem_ids | run-1 |  | 120 | 6.7 | 5.6% 💤 OVER | success |
| filter_unichem | run-6 |  | 120 | 6.4 | 5.4% 💤 OVER | success |
| filter_unichem | run-1 |  | 120 | 6.2 | 5.2% 💤 OVER | success |
| filter_unichem | run-2 |  | 120 | 6.2 | 5.1% 💤 OVER | success |
| get_obo_descriptions | run-1 |  | 120 | 6.0 | 5.0% 💤 OVER | success |
| generate_kgx | run-6 | filename=MolecularMixture | 360 | 17.5 | 4.9% 💤 OVER | success |
| disease_compendia | run-2 |  | 120 | 5.7 | 4.7% 💤 OVER | success |
| check_publications | run-1 |  | 120 | 5.7 | 4.7% 💤 OVER | success |
| check_publications | run-7 |  | 120 | 5.7 | 4.7% 💤 OVER | success |
| pubchem_labels | run-1 |  | 120 | 5.3 | 4.4% 💤 OVER | success |
| get_gene_ncbigene_relationships | run-1 |  | 120 | 5.0 | 4.2% 💤 OVER | success |
| check_publications_completeness | run-1 |  | 120 | 5.0 | 4.2% 💤 OVER | success |
| export_synonyms_to_duckdb | run-3 | filename=Gene | 120 | 5.0 | 4.2% 💤 OVER | success |
| check_publications_completeness | run-7 |  | 120 | 5.0 | 4.2% 💤 OVER | success |
| get_chembl | run-1 |  | 120 | 4.6 | 3.9% 💤 OVER | success |
| process_compendia | run-1 |  | 120 | 4.2 | 3.5% 💤 OVER | success |
| export_compendia_to_duckdb | run-3 | filename=Gene | 360 | 11.3 | 3.2% 💤 OVER | success |
| umls_relationships | run-1 |  | 120 | 3.5 | 2.9% 💤 OVER | success |
| pubchem_synonyms | run-1 |  | 120 | 3.3 | 2.8% 💤 OVER | success |
| anatomy_uberon_ids | run-1 |  | 120 | 3.3 | 2.7% 💤 OVER | success |
| export_compendia_to_duckdb | run-1 | filename=Publication | 360 | 9.5 | 2.6% 💤 OVER | success |
| export_compendia_to_duckdb | run-7 | filename=Publication | 360 | 9.5 | 2.6% 💤 OVER | success |
| taxon | run-1 |  | 120 | 3.0 | 2.5% 💤 OVER | success |
| get_gene_ncbigene_ensembl_relationships | run-1 |  | 120 | 2.8 | 2.4% 💤 OVER | success |
| get_mesh_labels | run-1 |  | 120 | 2.7 | 2.2% 💤 OVER | success |
| chemical_mesh_ids | run-1 |  | 120 | 2.7 | 2.2% 💤 OVER | success |
| generate_content_report_for_compendium_MolecularMixture | run-6 |  | 120 | 2.7 | 2.2% 💤 OVER | success |
| protein_uniprotkb_ids | run-1 |  | 120 | 2.5 | 2.1% 💤 OVER | success |
| disease_mesh_ids | run-1 |  | 120 | 2.0 | 1.7% 💤 OVER | success |
| anatomy_mesh_ids | run-1 |  | 120 | 2.0 | 1.7% 💤 OVER | success |
| taxon_mesh_ids | run-1 |  | 120 | 2.0 | 1.7% 💤 OVER | success |
| get_taxon_relationships | run-1 |  | 120 | 2.0 | 1.7% 💤 OVER | success |
| get_chemical_mesh_relationships | run-1 |  | 120 | 2.0 | 1.7% 💤 OVER | success |
| get_chemical_pubchem_cas_concord | run-1 |  | 120 | 2.0 | 1.7% 💤 OVER | success |
| check_molecular_mixture | run-6 |  | 120 | 2.0 | 1.7% 💤 OVER | success |
| get_pubchem_structures | run-1 |  | 120 | 1.9 | 1.6% 💤 OVER | success |
| chemical_drugbank_ids | run-2 |  | 120 | 1.5 | 1.3% 💤 OVER | success |
| genefamily_compendia | run-1 |  | 120 | 1.5 | 1.2% 💤 OVER | success |
| macromolecular_complex_compendia | run-1 |  | 120 | 1.5 | 1.2% 💤 OVER | success |
| cell_line_compendia | run-1 |  | 120 | 1.5 | 1.2% 💤 OVER | success |
| chemical_drugbank_ids | run-1 |  | 120 | 1.5 | 1.2% 💤 OVER | success |
| gene_ensembl_ids | run-3 |  | 120 | 1.5 | 1.2% 💤 OVER | success |
| protein_ensembl_ids | run-3 |  | 120 | 1.5 | 1.2% 💤 OVER | success |
| chemical_drugbank_ids | run-6 |  | 120 | 1.5 | 1.2% 💤 OVER | success |
| ncbitaxon_labels_and_synonyms | run-1 |  | 120 | 1.4 | 1.2% 💤 OVER | success |
| get_mesh | run-1 |  | 120 | 1.4 | 1.1% 💤 OVER | success |
| disease | run-2 |  | 120 | 1.4 | 1.1% 💤 OVER | success |
| generate_kgx | run-6 | filename=ChemicalEntity | 360 | 4.0 | 1.1% 💤 OVER | success |
| get_umls_labels_and_synonyms | run-1 |  | 120 | 1.3 | 1.1% 💤 OVER | success |
| gene_umls_ids | run-1 |  | 120 | 1.3 | 1.1% 💤 OVER | success |
| get_protein_ncit_umls_relationships | run-1 |  | 120 | 1.3 | 1.1% 💤 OVER | success |
| get_protein_umls_relationships | run-1 |  | 120 | 1.3 | 1.1% 💤 OVER | success |
| get_disease_umls_relationships | run-1 |  | 120 | 1.3 | 1.1% 💤 OVER | success |
| get_chemical_umls_relationships | run-1 |  | 120 | 1.3 | 1.1% 💤 OVER | success |
| get_anatomy_umls_relationships | run-1 |  | 120 | 1.3 | 1.1% 💤 OVER | success |
| get_process_umls_relationships | run-1 |  | 120 | 1.3 | 1.1% 💤 OVER | success |
| get_taxon_umls_relationships | run-1 |  | 120 | 1.3 | 1.1% 💤 OVER | success |
| check_chemical_entity | run-6 |  | 120 | 1.3 | 1.1% 💤 OVER | success |
| compress_umls | run-7 |  | 120 | 1.3 | 1.1% 💤 OVER | success |
| disease_ncit_ids | run-1 |  | 120 | 1.3 | 1.1% 💤 OVER | success |
| download_rxnorm | run-1 |  | 120 | 1.2 | 1.0% 💤 OVER | success |
| get_disease_obo_relationships | run-1 |  | 120 | 1.2 | 1.0% 💤 OVER | success |
| get_pubchem | run-1 |  | 120 | 1.2 | 1.0% 💤 OVER | success |
| export_compendia_to_duckdb | run-6 | filename=MolecularMixture | 360 | 3.3 | 0.9% 💤 OVER | success |
| generate_summary_content_report_for_compendia | run-6 |  | 120 | 1.1 | 0.9% 💤 OVER | success |
| export_all_compendia_to_duckdb | run-6 |  | 120 | 1.1 | 0.9% 💤 OVER | success |
| generate_kgx | run-1 | filename=OrganismTaxon | 360 | 2.2 | 0.6% 💤 OVER | success |
| anatomy_go_ids | run-1 |  | 120 | 0.7 | 0.6% 💤 OVER | success |
| get_gene_medgen_relationships | run-1 |  | 120 | 0.7 | 0.6% 💤 OVER | success |
| get_rhea_labels | run-1 |  | 120 | 0.7 | 0.6% 💤 OVER | success |
| process_reactome_ids | run-1 |  | 120 | 0.7 | 0.6% 💤 OVER | success |
| get_EC_labels | run-1 |  | 120 | 0.7 | 0.6% 💤 OVER | success |
| unii_labels_and_synonyms | run-1 |  | 120 | 0.7 | 0.6% 💤 OVER | success |
| disease_efo_ids | run-1 |  | 120 | 0.7 | 0.6% 💤 OVER | success |
| get_orphanet_labels_and_synonyms | run-1 |  | 120 | 0.7 | 0.6% 💤 OVER | success |
| get_hgncfamily_labels | run-1 |  | 120 | 0.7 | 0.6% 💤 OVER | success |
| get_drugcentral | run-1 |  | 120 | 0.7 | 0.6% 💤 OVER | success |
| gtopdb_labels_and_synonyms | run-1 |  | 120 | 0.7 | 0.6% 💤 OVER | success |
| get_complexportal_labels_and_synonyms | run-1 |  | 120 | 0.7 | 0.6% 💤 OVER | success |
| chemical_unii_ids | run-1 |  | 120 | 0.7 | 0.6% 💤 OVER | success |
| get_clo_ids | run-1 |  | 120 | 0.7 | 0.6% 💤 OVER | success |
| get_gtopdb_inchikey_concord | run-1 |  | 120 | 0.7 | 0.6% 💤 OVER | success |
| get_CLO_labels | run-1 |  | 120 | 0.7 | 0.6% 💤 OVER | success |
| chemical_gtopdb_ids | run-1 |  | 120 | 0.7 | 0.6% 💤 OVER | success |
| get_doid | run-1 |  | 120 | 0.7 | 0.6% 💤 OVER | success |
| get_mods_labels | run-1 |  | 120 | 0.7 | 0.6% 💤 OVER | success |
| get_SMPDB_labels | run-1 |  | 120 | 0.7 | 0.6% 💤 OVER | success |
| get_hgnc | run-1 |  | 120 | 0.7 | 0.6% 💤 OVER | success |
| anatomy_ncit_ids | run-1 |  | 120 | 0.7 | 0.6% 💤 OVER | success |
| get_panther_pathway_labels | run-1 |  | 120 | 0.7 | 0.6% 💤 OVER | success |
| get_process_rhea_relationships | run-1 |  | 120 | 0.7 | 0.6% 💤 OVER | success |
| get_protein_ncit_uniprotkb_relationships | run-1 |  | 120 | 0.7 | 0.6% 💤 OVER | success |
| gene_mods_ids | run-1 |  | 120 | 0.7 | 0.6% 💤 OVER | success |
| genefamily | run-1 |  | 120 | 0.7 | 0.6% 💤 OVER | success |
| all_reports | run-7 |  | 120 | 0.7 | 0.6% 💤 OVER | success |
| export_all_to_kgx | run-7 |  | 120 | 0.7 | 0.6% 💤 OVER | success |
| generate_sapbert_training_data | run-1 | filename=OrganismTaxon.txt | 360 | 2.0 | 0.6% 💤 OVER | success |
| get_reactome_labels | run-1 |  | 120 | 0.7 | 0.6% 💤 OVER | success |
| disease_omim_ids | run-1 |  | 120 | 0.7 | 0.6% 💤 OVER | success |
| gene_omim_ids | run-1 |  | 120 | 0.7 | 0.6% 💤 OVER | success |
| get_pantherfamily_labels | run-1 |  | 120 | 0.7 | 0.6% 💤 OVER | success |
| rxnorm_relationships | run-1 |  | 120 | 0.7 | 0.6% 💤 OVER | success |
| get_chebi_concord | run-1 |  | 120 | 0.7 | 0.6% 💤 OVER | success |
| get_doid_labels_and_synonyms | run-1 |  | 120 | 0.7 | 0.6% 💤 OVER | success |
| process_rhea_ids | run-1 |  | 120 | 0.7 | 0.6% 💤 OVER | success |
| get_EFO_labels | run-1 |  | 120 | 0.7 | 0.6% 💤 OVER | success |
| process_ec_ids | run-1 |  | 120 | 0.7 | 0.6% 💤 OVER | success |
| taxon_ncbi_ids | run-1 |  | 120 | 0.7 | 0.6% 💤 OVER | success |
| get_chemical_rxnorm_relationships | run-1 |  | 120 | 0.7 | 0.6% 💤 OVER | success |
| disease_doid_ids | run-1 |  | 120 | 0.7 | 0.6% 💤 OVER | success |
| get_chemical_pubchem_mesh_concord | run-1 |  | 120 | 0.7 | 0.6% 💤 OVER | success |
| chemical_kegg_ids | run-1 |  | 120 | 0.7 | 0.6% 💤 OVER | success |
| gene_ncbi_ids | run-1 |  | 120 | 0.7 | 0.6% 💤 OVER | success |
| protein_umls_ids | run-1 |  | 120 | 0.7 | 0.6% 💤 OVER | success |
| anatomy_umls_ids | run-1 |  | 120 | 0.7 | 0.6% 💤 OVER | success |
| disease_umls_ids | run-1 |  | 120 | 0.7 | 0.6% 💤 OVER | success |
| taxon_umls_ids | run-1 |  | 120 | 0.7 | 0.6% 💤 OVER | success |
| process_umls_ids | run-1 |  | 120 | 0.7 | 0.6% 💤 OVER | success |
| chemical_umls_ids | run-1 |  | 120 | 0.7 | 0.6% 💤 OVER | success |
| get_gene_umls_relationships | run-1 |  | 120 | 0.7 | 0.6% 💤 OVER | success |
| generate_content_report_for_compendium_GeneFamily | run-1 |  | 120 | 0.7 | 0.6% 💤 OVER | success |
| check_genefamily | run-1 |  | 120 | 0.7 | 0.6% 💤 OVER | success |
| check_genefamily_completeness | run-1 |  | 120 | 0.7 | 0.6% 💤 OVER | success |
| check_macromolecular_complex_completeness | run-1 |  | 120 | 0.7 | 0.6% 💤 OVER | success |
| generate_content_report_for_compendium_CellLine | run-1 |  | 120 | 0.7 | 0.6% 💤 OVER | success |
| generate_content_report_for_compendium_MacromolecularComplex | run-1 |  | 120 | 0.7 | 0.6% 💤 OVER | success |
| check_cell_line_completeness | run-1 |  | 120 | 0.7 | 0.6% 💤 OVER | success |
| check_macromolecular_complex | run-1 |  | 120 | 0.7 | 0.6% 💤 OVER | success |
| cell_line | run-1 |  | 120 | 0.7 | 0.6% 💤 OVER | success |
| macromolecular_complex | run-1 |  | 120 | 0.7 | 0.6% 💤 OVER | success |
| export_synonyms_to_duckdb | run-1 | filename=GeneFamily | 120 | 0.7 | 0.6% 💤 OVER | success |
| export_synonyms_to_duckdb | run-1 | filename=MacromolecularComplex | 120 | 0.7 | 0.6% 💤 OVER | success |
| export_synonyms_to_duckdb | run-1 | filename=CellLine | 120 | 0.7 | 0.6% 💤 OVER | success |
| generate_content_report_for_compendium_BiologicalProcess | run-1 |  | 120 | 0.7 | 0.6% 💤 OVER | success |
| check_pathway | run-1 |  | 120 | 0.7 | 0.6% 💤 OVER | success |
| check_activity | run-1 |  | 120 | 0.7 | 0.6% 💤 OVER | success |
| check_process_completeness | run-1 |  | 120 | 0.7 | 0.6% 💤 OVER | success |
| generate_content_report_for_compendium_Pathway | run-1 |  | 120 | 0.7 | 0.6% 💤 OVER | success |
| generate_content_report_for_compendium_MolecularActivity | run-1 |  | 120 | 0.7 | 0.6% 💤 OVER | success |
| check_process | run-1 |  | 120 | 0.7 | 0.6% 💤 OVER | success |
| process | run-1 |  | 120 | 0.7 | 0.6% 💤 OVER | success |
| export_synonyms_to_duckdb | run-1 | filename=BiologicalProcess | 120 | 0.7 | 0.6% 💤 OVER | success |
| export_synonyms_to_duckdb | run-1 | filename=Pathway | 120 | 0.7 | 0.6% 💤 OVER | success |
| export_synonyms_to_duckdb | run-1 | filename=MolecularActivity | 120 | 0.7 | 0.6% 💤 OVER | success |
| check_taxon | run-1 |  | 120 | 0.7 | 0.6% 💤 OVER | success |
| check_taxon_completeness | run-1 |  | 120 | 0.7 | 0.6% 💤 OVER | success |
| generate_content_report_for_compendium_OrganismTaxon | run-1 |  | 120 | 0.7 | 0.6% 💤 OVER | success |
| export_synonyms_to_duckdb | run-1 | filename=OrganismTaxon | 120 | 0.7 | 0.6% 💤 OVER | success |
| chemical_chembl_ids | run-1 |  | 120 | 0.7 | 0.6% 💤 OVER | success |
| publications | run-1 |  | 120 | 0.7 | 0.6% 💤 OVER | success |
| pubchem_rxnorm_relationships | run-2 |  | 120 | 0.7 | 0.6% 💤 OVER | success |
| export_synonyms_to_duckdb | run-2 | filename=Disease | 120 | 0.7 | 0.6% 💤 OVER | success |
| export_synonyms_to_duckdb | run-2 | filename=PhenotypicFeature | 120 | 0.7 | 0.6% 💤 OVER | success |
| chemical_hmdb_ids | run-2 |  | 120 | 0.7 | 0.6% 💤 OVER | success |
| check_gross_anatomical_structure | run-2 |  | 120 | 0.7 | 0.6% 💤 OVER | success |
| generate_content_report_for_compendium_CellularComponent | run-2 |  | 120 | 0.7 | 0.6% 💤 OVER | success |
| check_anatomy_completeness | run-2 |  | 120 | 0.7 | 0.6% 💤 OVER | success |
| check_anatomical_entity | run-2 |  | 120 | 0.7 | 0.6% 💤 OVER | success |
| check_cellular_component | run-2 |  | 120 | 0.7 | 0.6% 💤 OVER | success |
| generate_content_report_for_compendium_Cell | run-2 |  | 120 | 0.7 | 0.6% 💤 OVER | success |
| generate_content_report_for_compendium_GrossAnatomicalStructure | run-2 |  | 120 | 0.7 | 0.6% 💤 OVER | success |
| anatomy | run-2 |  | 120 | 0.7 | 0.6% 💤 OVER | success |
| export_synonyms_to_duckdb | run-2 | filename=AnatomicalEntity | 120 | 0.7 | 0.6% 💤 OVER | success |
| export_synonyms_to_duckdb | run-2 | filename=CellularComponent | 120 | 0.7 | 0.6% 💤 OVER | success |
| export_synonyms_to_duckdb | run-2 | filename=Cell | 120 | 0.7 | 0.6% 💤 OVER | success |
| export_synonyms_to_duckdb | run-2 | filename=GrossAnatomicalStructure | 120 | 0.7 | 0.6% 💤 OVER | success |
| geneprotein | run-3 |  | 120 | 0.7 | 0.6% 💤 OVER | success |
| check_chemical_mixture | run-6 |  | 120 | 0.7 | 0.6% 💤 OVER | success |
| generate_content_report_for_compendium_Polypeptide | run-6 |  | 120 | 0.7 | 0.6% 💤 OVER | success |
| check_drug | run-6 |  | 120 | 0.7 | 0.6% 💤 OVER | success |
| generate_content_report_for_compendium_ComplexMolecularMixture | run-6 |  | 120 | 0.7 | 0.6% 💤 OVER | success |
| generate_content_report_for_compendium_ChemicalEntity | run-6 |  | 120 | 0.7 | 0.6% 💤 OVER | success |
| generate_content_report_for_compendium_ChemicalMixture | run-6 |  | 120 | 0.7 | 0.6% 💤 OVER | success |
| check_polypeptide | run-6 |  | 120 | 0.7 | 0.6% 💤 OVER | success |
| generate_content_report_for_compendium_Drug | run-6 |  | 120 | 0.7 | 0.6% 💤 OVER | success |
| check_complex_mixture | run-6 |  | 120 | 0.7 | 0.6% 💤 OVER | success |
| compress_umls | run-6 |  | 120 | 0.7 | 0.6% 💤 OVER | success |
| generate_content_report_for_compendium_umls | run-6 |  | 120 | 0.7 | 0.6% 💤 OVER | success |
| export_synonyms_to_duckdb | run-6 | filename=umls | 120 | 0.7 | 0.6% 💤 OVER | success |
| export_all_to_kgx | run-6 |  | 120 | 0.7 | 0.6% 💤 OVER | success |
| drugchemical | run-6 |  | 120 | 0.7 | 0.6% 💤 OVER | success |
| all_outputs | run-6 |  | 120 | 0.7 | 0.6% 💤 OVER | success |
| check_compendia_files | run-6 |  | 120 | 0.7 | 0.6% 💤 OVER | success |
| check_conflation_files | run-6 |  | 120 | 0.7 | 0.6% 💤 OVER | success |
| export_all_synonyms_to_duckdb | run-6 |  | 120 | 0.7 | 0.6% 💤 OVER | success |
| export_all_to_duckdb | run-6 |  | 120 | 0.7 | 0.6% 💤 OVER | success |
| export_all_to_sapbert_training | run-6 |  | 120 | 0.7 | 0.6% 💤 OVER | success |
| publications | run-7 |  | 120 | 0.7 | 0.6% 💤 OVER | success |
| generate_content_report_for_compendium_umls | run-7 |  | 120 | 0.7 | 0.6% 💤 OVER | success |
| generate_summary_content_report_for_compendia | run-7 |  | 120 | 0.7 | 0.6% 💤 OVER | success |
| export_all_compendia_to_duckdb | run-7 |  | 120 | 0.7 | 0.6% 💤 OVER | success |
| all_outputs | run-7 |  | 120 | 0.7 | 0.6% 💤 OVER | success |
| export_synonyms_to_duckdb | run-7 | filename=umls | 120 | 0.7 | 0.6% 💤 OVER | success |
| check_compendia_files | run-7 |  | 120 | 0.7 | 0.6% 💤 OVER | success |
| check_synonyms_gzipped_files | run-7 |  | 120 | 0.7 | 0.6% 💤 OVER | success |
| check_conflation_files | run-7 |  | 120 | 0.7 | 0.6% 💤 OVER | success |
| export_all_synonyms_to_duckdb | run-7 |  | 120 | 0.7 | 0.6% 💤 OVER | success |
| export_all_to_sapbert_training | run-7 |  | 120 | 0.7 | 0.6% 💤 OVER | success |
| export_all_to_duckdb | run-7 |  | 120 | 0.7 | 0.6% 💤 OVER | success |
| all_duckdb_reports | run-7 |  | 120 | 0.7 | 0.6% 💤 OVER | success |
| all | run-7 |  | 120 | 0.7 | 0.6% 💤 OVER | success |
| genefamily_pantherfamily_ids | run-1 |  | 120 | 0.7 | 0.5% 💤 OVER | success |
| chemical_rxnorm_ids | run-1 |  | 120 | 0.7 | 0.5% 💤 OVER | success |
| get_hgnc_labels_and_synonyms | run-1 |  | 120 | 0.7 | 0.5% 💤 OVER | success |
| process_smpdb_ids | run-1 |  | 120 | 0.7 | 0.5% 💤 OVER | success |
| gene_hgnc_ids | run-1 |  | 120 | 0.7 | 0.5% 💤 OVER | success |
| process_panther_ids | run-1 |  | 120 | 0.7 | 0.5% 💤 OVER | success |
| get_disease_doid_relationships | run-1 |  | 120 | 0.7 | 0.5% 💤 OVER | success |
| macromolecular_complex_ids | run-1 |  | 120 | 0.7 | 0.5% 💤 OVER | success |
| get_disease_efo_relationships | run-1 |  | 120 | 0.7 | 0.5% 💤 OVER | success |
| chemical_drugcentral_ids | run-1 |  | 120 | 0.7 | 0.5% 💤 OVER | success |
| disease_orphanet_ids | run-1 |  | 120 | 0.7 | 0.5% 💤 OVER | success |
| check_cell_line | run-1 |  | 120 | 0.7 | 0.5% 💤 OVER | success |
| check_disease | run-2 |  | 120 | 0.7 | 0.5% 💤 OVER | success |
| generate_content_report_for_compendium_Disease | run-2 |  | 120 | 0.7 | 0.5% 💤 OVER | success |
| check_phenotypic_feature | run-2 |  | 120 | 0.7 | 0.5% 💤 OVER | success |
| generate_content_report_for_compendium_PhenotypicFeature | run-2 |  | 120 | 0.7 | 0.5% 💤 OVER | success |
| check_disease_completeness | run-2 |  | 120 | 0.7 | 0.5% 💤 OVER | success |
| check_cell | run-2 |  | 120 | 0.7 | 0.5% 💤 OVER | success |
| generate_content_report_for_compendium_AnatomicalEntity | run-2 |  | 120 | 0.7 | 0.5% 💤 OVER | success |
| genefamily_hgncfamily_ids | run-1 |  | 120 | 0.6 | 0.5% 💤 OVER | success |
| get_chemical_drugcentral_relationships | run-1 |  | 120 | 0.6 | 0.5% 💤 OVER | success |
| get_mesh_synonyms | run-1 |  | 120 | 0.6 | 0.5% 💤 OVER | success |
| protein_pr_ids | run-1 |  | 120 | 0.6 | 0.5% 💤 OVER | success |
| disease_hp_ids | run-1 |  | 120 | 0.6 | 0.5% 💤 OVER | success |
| get_process_go_relationships | run-1 |  | 120 | 0.6 | 0.5% 💤 OVER | success |
| get_drugbank_labels_and_synonyms | run-1 |  | 120 | 0.6 | 0.5% 💤 OVER | success |
| get_EFO | run-1 |  | 120 | 0.6 | 0.5% 💤 OVER | success |
| get_wikidata_cell_relationships | run-1 |  | 120 | 0.6 | 0.5% 💤 OVER | success |
| get_pantherfamily | run-1 |  | 120 | 0.6 | 0.5% 💤 OVER | success |
| get_gtopdb | run-1 |  | 120 | 0.6 | 0.5% 💤 OVER | success |
| get_omim | run-1 |  | 120 | 0.6 | 0.5% 💤 OVER | success |
| get_complexportal | run-1 |  | 120 | 0.6 | 0.5% 💤 OVER | success |
| get_chebi | run-1 |  | 120 | 0.6 | 0.5% 💤 OVER | success |
| get_hgncfamily | run-1 |  | 120 | 0.6 | 0.5% 💤 OVER | success |
| get_clo | run-1 |  | 120 | 0.6 | 0.5% 💤 OVER | success |
| get_unii | run-1 |  | 120 | 0.6 | 0.5% 💤 OVER | success |
| get_uniprotkb_sprot | run-1 |  | 120 | 0.6 | 0.5% 💤 OVER | success |
| get_orphanet | run-1 |  | 120 | 0.6 | 0.5% 💤 OVER | success |
| disease_manual_concord | run-2 |  | 120 | 0.6 | 0.5% 💤 OVER | success |
| generate_sapbert_training_data | run-6 | filename=umls.txt | 360 | 1.7 | 0.5% 💤 OVER | success |
| get_ncbitaxon | run-1 |  | 120 | 0.6 | 0.5% 💤 OVER | success |
| get_reactome | run-1 |  | 120 | 0.6 | 0.5% 💤 OVER | success |
| process_go_ids | run-1 |  | 120 | 0.6 | 0.5% 💤 OVER | success |
| anatomy_cl_ids | run-1 |  | 120 | 0.6 | 0.5% 💤 OVER | success |
| get_rhea | run-1 |  | 120 | 0.6 | 0.5% 💤 OVER | success |
| get_chemical_wikipedia_relationships | run-1 |  | 120 | 0.6 | 0.5% 💤 OVER | success |
| get_ncbigene | run-1 |  | 120 | 0.6 | 0.5% 💤 OVER | success |
| disease_mondo_ids | run-1 |  | 120 | 0.6 | 0.5% 💤 OVER | success |
| get_EC | run-1 |  | 120 | 0.6 | 0.5% 💤 OVER | success |
| get_umls_gene_protein_mappings | run-1 |  | 120 | 0.6 | 0.5% 💤 OVER | success |
| get_ncit | run-1 |  | 120 | 0.6 | 0.5% 💤 OVER | success |
| get_SMPDB | run-1 |  | 120 | 0.6 | 0.5% 💤 OVER | success |
| get_panther_pathways | run-1 |  | 120 | 0.6 | 0.5% 💤 OVER | success |
| get_mods | run-1 |  | 120 | 0.6 | 0.5% 💤 OVER | success |
| pubchem_rxnorm_annotations | run-2 |  | 120 | 0.6 | 0.5% 💤 OVER | success |
| chemical_chebi_ids | run-2 |  | 120 | 0.6 | 0.5% 💤 OVER | success |
| generate_kgx | run-2 | filename=Disease | 360 | 1.3 | 0.4% 💤 OVER | success |
| export_compendia_to_duckdb | run-6 | filename=ChemicalEntity | 360 | 1.3 | 0.4% 💤 OVER | success |
| generate_sapbert_training_data | run-7 | filename=umls.txt | 360 | 1.3 | 0.4% 💤 OVER | success |
| export_compendia_to_duckdb | run-1 | filename=GeneFamily | 360 | 0.7 | 0.2% 💤 OVER | success |
| generate_kgx | run-1 | filename=GeneFamily | 360 | 0.7 | 0.2% 💤 OVER | success |
| export_compendia_to_duckdb | run-1 | filename=MacromolecularComplex | 360 | 0.7 | 0.2% 💤 OVER | success |
| generate_kgx | run-1 | filename=CellLine | 360 | 0.7 | 0.2% 💤 OVER | success |
| generate_kgx | run-1 | filename=MacromolecularComplex | 360 | 0.7 | 0.2% 💤 OVER | success |
| generate_sapbert_training_data | run-1 | filename=CellLine.txt | 360 | 0.7 | 0.2% 💤 OVER | success |
| generate_sapbert_training_data | run-1 | filename=GeneFamily.txt | 360 | 0.7 | 0.2% 💤 OVER | success |
| generate_sapbert_training_data | run-1 | filename=MacromolecularComplex.txt | 360 | 0.7 | 0.2% 💤 OVER | success |
| export_compendia_to_duckdb | run-1 | filename=BiologicalProcess | 360 | 0.7 | 0.2% 💤 OVER | success |
| generate_kgx | run-1 | filename=Pathway | 360 | 0.7 | 0.2% 💤 OVER | success |
| generate_kgx | run-1 | filename=MolecularActivity | 360 | 0.7 | 0.2% 💤 OVER | success |
| export_compendia_to_duckdb | run-1 | filename=Pathway | 360 | 0.7 | 0.2% 💤 OVER | success |
| export_compendia_to_duckdb | run-1 | filename=MolecularActivity | 360 | 0.7 | 0.2% 💤 OVER | success |
| generate_kgx | run-1 | filename=BiologicalProcess | 360 | 0.7 | 0.2% 💤 OVER | success |
| generate_sapbert_training_data | run-1 | filename=Pathway.txt | 360 | 0.7 | 0.2% 💤 OVER | success |
| generate_sapbert_training_data | run-1 | filename=MolecularActivity.txt | 360 | 0.7 | 0.2% 💤 OVER | success |
| generate_sapbert_training_data | run-1 | filename=BiologicalProcess.txt | 360 | 0.7 | 0.2% 💤 OVER | success |
| export_compendia_to_duckdb | run-1 | filename=OrganismTaxon | 360 | 0.7 | 0.2% 💤 OVER | success |
| generate_sapbert_training_data | run-2 | filename=Disease.txt | 360 | 0.7 | 0.2% 💤 OVER | success |
| generate_sapbert_training_data | run-2 | filename=PhenotypicFeature.txt | 360 | 0.7 | 0.2% 💤 OVER | success |
| export_compendia_to_duckdb | run-2 | filename=CellularComponent | 360 | 0.7 | 0.2% 💤 OVER | success |
| generate_kgx | run-2 | filename=AnatomicalEntity | 360 | 0.7 | 0.2% 💤 OVER | success |
| generate_kgx | run-2 | filename=CellularComponent | 360 | 0.7 | 0.2% 💤 OVER | success |
| export_compendia_to_duckdb | run-2 | filename=GrossAnatomicalStructure | 360 | 0.7 | 0.2% 💤 OVER | success |
| export_compendia_to_duckdb | run-2 | filename=Cell | 360 | 0.7 | 0.2% 💤 OVER | success |
| generate_kgx | run-2 | filename=Cell | 360 | 0.7 | 0.2% 💤 OVER | success |
| generate_sapbert_training_data | run-2 | filename=AnatomicalEntity.txt | 360 | 0.7 | 0.2% 💤 OVER | success |
| generate_sapbert_training_data | run-2 | filename=CellularComponent.txt | 360 | 0.7 | 0.2% 💤 OVER | success |
| generate_sapbert_training_data | run-2 | filename=Cell.txt | 360 | 0.7 | 0.2% 💤 OVER | success |
| generate_sapbert_training_data | run-2 | filename=GrossAnatomicalStructure.txt | 360 | 0.7 | 0.2% 💤 OVER | success |
| export_compendia_to_duckdb | run-6 | filename=ChemicalMixture | 360 | 0.7 | 0.2% 💤 OVER | success |
| generate_kgx | run-6 | filename=ComplexMolecularMixture | 360 | 0.7 | 0.2% 💤 OVER | success |
| export_compendia_to_duckdb | run-6 | filename=Drug | 360 | 0.7 | 0.2% 💤 OVER | success |
| generate_kgx | run-6 | filename=ChemicalMixture | 360 | 0.7 | 0.2% 💤 OVER | success |
| generate_kgx | run-6 | filename=Drug | 360 | 0.7 | 0.2% 💤 OVER | success |
| export_compendia_to_duckdb | run-6 | filename=Polypeptide | 360 | 0.7 | 0.2% 💤 OVER | success |
| export_compendia_to_duckdb | run-6 | filename=ComplexMolecularMixture | 360 | 0.7 | 0.2% 💤 OVER | success |
| generate_kgx | run-6 | filename=Polypeptide | 360 | 0.7 | 0.2% 💤 OVER | success |
| generate_kgx | run-6 | filename=umls | 360 | 0.7 | 0.2% 💤 OVER | success |
| export_compendia_to_duckdb | run-6 | filename=umls | 360 | 0.7 | 0.2% 💤 OVER | success |
| generate_kgx | run-7 | filename=umls | 360 | 0.7 | 0.2% 💤 OVER | success |
| export_compendia_to_duckdb | run-7 | filename=umls | 360 | 0.7 | 0.2% 💤 OVER | success |
| export_compendia_to_duckdb | run-1 | filename=CellLine | 360 | 0.7 | 0.2% 💤 OVER | success |
| export_compendia_to_duckdb | run-2 | filename=Disease | 360 | 0.7 | 0.2% 💤 OVER | success |
| export_compendia_to_duckdb | run-2 | filename=PhenotypicFeature | 360 | 0.7 | 0.2% 💤 OVER | success |
| generate_kgx | run-2 | filename=PhenotypicFeature | 360 | 0.7 | 0.2% 💤 OVER | success |
| generate_kgx | run-2 | filename=GrossAnatomicalStructure | 360 | 0.7 | 0.2% 💤 OVER | success |
| export_compendia_to_duckdb | run-2 | filename=AnatomicalEntity | 360 | 0.7 | 0.2% 💤 OVER | success |

## 4. CPU Efficiency Report

*Jobs where SLURM reported low CPU efficiency.*

| Rule | Run | SLURM Job ID | CPU Efficiency | Allocated CPUs |
|------|-----|--------------|----------------|----------------|
| all_duckdb_reports | run-7 | 75427 | 0.0% | 4 |
| all_outputs | run-6 | 75253 | 0.0% | 4 |
| all_outputs | run-7 | 75412 | 0.0% | 4 |
| all_reports | run-7 | 75421 | 0.0% | 4 |
| anatomy | run-2 | 74628 | 0.0% | 4 |
| anatomy_compendia | run-2 | 74609 | 0.0% | 4 |
| check_anatomical_entity | run-2 | 74622 | 0.0% | 4 |
| check_anatomy_completeness | run-2 | 74618 | 0.0% | 4 |
| check_cell | run-2 | 74613 | 0.0% | 4 |
| check_cellular_component | run-2 | 74624 | 0.0% | 4 |
| check_chemical_completeness | run-6 | 75140 | 0.0% | 4 |
| check_chemical_entity | run-6 | 75161 | 0.0% | 4 |
| check_chemical_mixture | run-6 | 75134 | 0.0% | 4 |
| check_compendia_files | run-6 | 75254 | 0.0% | 4 |
| check_compendia_files | run-7 | 75415 | 0.0% | 4 |
| check_complex_mixture | run-6 | 75157 | 0.0% | 4 |
| check_conflation_files | run-6 | 75256 | 0.0% | 4 |
| check_conflation_files | run-7 | 75417 | 0.0% | 4 |
| check_disease | run-2 | 74587 | 0.0% | 4 |
| check_disease_completeness | run-2 | 74595 | 0.0% | 4 |
| check_drug | run-6 | 75139 | 0.0% | 4 |
| check_for_duplicate_clique_leaders | run-6 | 75262 | 0.0% | 4 |
| check_for_duplicate_clique_leaders | run-7 | 75425 | 0.0% | 4 |
| check_for_duplicate_curies | run-6 | 75259 | 0.0% | 4 |
| check_for_duplicate_curies | run-7 | 75422 | 0.0% | 4 |
| check_for_identically_labeled_cliques | run-6 | 75261 | 0.0% | 4 |
| check_for_identically_labeled_cliques | run-7 | 75424 | 0.0% | 4 |
| check_gene | run-3 | 74760 | 0.0% | 4 |
| check_gene_completeness | run-3 | 74762 | 0.0% | 4 |
| check_gross_anatomical_structure | run-2 | 74615 | 0.0% | 4 |
| check_molecular_mixture | run-6 | 75144 | 0.0% | 4 |
| check_phenotypic_feature | run-2 | 74591 | 0.0% | 4 |
| check_polypeptide | run-6 | 75152 | 0.0% | 4 |
| check_protein | run-3 | 74814 | 0.0% | 4 |
| check_protein_completeness | run-3 | 74818 | 0.0% | 4 |
| check_publications | run-1 | 74525 | 0.0% | 4 |
| check_publications | run-7 | 75403 | 0.0% | 4 |
| check_publications_completeness | run-1 | 74523 | 0.0% | 4 |
| check_publications_completeness | run-7 | 75399 | 0.0% | 4 |
| check_small_molecule | run-6 | 75148 | 0.0% | 4 |
| check_synonyms_gzipped_files | run-6 | 75255 | 0.0% | 4 |
| check_synonyms_gzipped_files | run-7 | 75416 | 0.0% | 4 |
| chemical | run-6 | 75168 | 0.0% | 4 |
| chemical_chebi_ids | run-2 | 74581 | 0.0% | 4 |
| chemical_compendia | run-6 | 75064 | 0.0% | 4 |
| chemical_drugbank_ids | run-2 | 74605 | 0.0% | 4 |
| chemical_drugbank_ids | run-6 | 75028 | 0.0% | 4 |
| chemical_hmdb_ids | run-2 | 74610 | 0.0% | 4 |
| chemical_unichem_concordia | run-6 | 75034 | 0.0% | 4 |
| compress_umls | run-6 | 75181 | 0.0% | 4 |
| compress_umls | run-7 | 75407 | 0.0% | 4 |
| disease | run-2 | 74596 | 0.0% | 4 |
| disease_compendia | run-2 | 74583 | 0.0% | 4 |
| disease_manual_concord | run-2 | 74578 | 0.0% | 4 |
| drugchemical | run-6 | 75252 | 0.0% | 4 |
| drugchemical_conflated_synonyms | run-6 | 75219 | 0.0% | 4 |
| drugchemical_conflation | run-6 | 75154 | 0.0% | 4 |
| export_all_compendia_to_duckdb | run-6 | 75187 | 0.0% | 4 |
| export_all_compendia_to_duckdb | run-7 | 75411 | 0.0% | 4 |
| export_all_synonyms_to_duckdb | run-6 | 75257 | 0.0% | 4 |
| export_all_synonyms_to_duckdb | run-7 | 75418 | 0.0% | 4 |
| export_all_to_duckdb | run-6 | 75258 | 0.0% | 4 |
| export_all_to_duckdb | run-7 | 75420 | 0.0% | 4 |
| export_all_to_kgx | run-6 | 75223 | 0.0% | 4 |
| export_all_to_kgx | run-7 | 75428 | 0.0% | 4 |
| export_all_to_sapbert_training | run-6 | 75270 | 0.0% | 4 |
| export_all_to_sapbert_training | run-7 | 75419 | 0.0% | 4 |
| export_compendia_to_duckdb | run-1 | 74524 | 0.0% | 4 |
| export_compendia_to_duckdb | run-2 | 74588 | 0.0% | 4 |
| export_compendia_to_duckdb | run-2 | 74592 | 0.0% | 4 |
| export_compendia_to_duckdb | run-2 | 74612 | 0.0% | 4 |
| export_compendia_to_duckdb | run-2 | 74617 | 0.0% | 4 |
| export_compendia_to_duckdb | run-2 | 74621 | 0.0% | 4 |
| export_compendia_to_duckdb | run-2 | 74623 | 0.0% | 4 |
| export_compendia_to_duckdb | run-3 | 74758 | 0.0% | 4 |
| export_compendia_to_duckdb | run-3 | 74817 | 0.0% | 4 |
| export_compendia_to_duckdb | run-6 | 75131 | 0.0% | 4 |
| export_compendia_to_duckdb | run-6 | 75136 | 0.0% | 4 |
| export_compendia_to_duckdb | run-6 | 75143 | 0.0% | 4 |
| export_compendia_to_duckdb | run-6 | 75147 | 0.0% | 4 |
| export_compendia_to_duckdb | run-6 | 75150 | 0.0% | 4 |
| export_compendia_to_duckdb | run-6 | 75155 | 0.0% | 4 |
| export_compendia_to_duckdb | run-6 | 75159 | 0.0% | 4 |
| export_compendia_to_duckdb | run-6 | 75183 | 0.0% | 4 |
| export_compendia_to_duckdb | run-7 | 75400 | 0.0% | 4 |
| export_compendia_to_duckdb | run-7 | 75409 | 0.0% | 4 |
| export_synonyms_to_duckdb | run-2 | 74597 | 0.0% | 4 |
| export_synonyms_to_duckdb | run-2 | 74598 | 0.0% | 4 |
| export_synonyms_to_duckdb | run-2 | 74629 | 0.0% | 4 |
| export_synonyms_to_duckdb | run-2 | 74630 | 0.0% | 4 |
| export_synonyms_to_duckdb | run-2 | 74633 | 0.0% | 4 |
| export_synonyms_to_duckdb | run-2 | 74634 | 0.0% | 4 |
| export_synonyms_to_duckdb | run-3 | 74781 | 0.0% | 4 |
| export_synonyms_to_duckdb | run-3 | 74844 | 0.0% | 4 |
| export_synonyms_to_duckdb | run-3 | 74945 | 0.0% | 4 |
| export_synonyms_to_duckdb | run-6 | 75185 | 0.0% | 4 |
| export_synonyms_to_duckdb | run-6 | 75250 | 0.0% | 4 |
| export_synonyms_to_duckdb | run-7 | 75414 | 0.0% | 4 |
| filter_unichem | run-2 | 74603 | 0.0% | 4 |
| filter_unichem | run-6 | 75026 | 0.0% | 4 |
| gene | run-3 | 74764 | 0.0% | 4 |
| gene_compendia | run-3 | 74728 | 0.0% | 4 |
| gene_ensembl_ids | run-3 | 74726 | 0.0% | 4 |
| geneprotein | run-3 | 74946 | 0.0% | 4 |
| geneprotein_conflated_synonyms | run-3 | 74843 | 0.0% | 4 |
| geneprotein_conflation | run-3 | 74816 | 0.0% | 4 |
| generate_by_clique_report | run-6 | 75263 | 0.0% | 4 |
| generate_by_clique_report | run-7 | 75426 | 0.0% | 4 |
| generate_content_report_for_compendium_AnatomicalEntity | run-2 | 74614 | 0.0% | 4 |
| generate_content_report_for_compendium_Cell | run-2 | 74625 | 0.0% | 4 |
| generate_content_report_for_compendium_CellularComponent | run-2 | 74616 | 0.0% | 4 |
| generate_content_report_for_compendium_ChemicalEntity | run-6 | 75146 | 0.0% | 4 |
| generate_content_report_for_compendium_ChemicalMixture | run-6 | 75149 | 0.0% | 4 |
| generate_content_report_for_compendium_ComplexMolecularMixture | run-6 | 75142 | 0.0% | 4 |
| generate_content_report_for_compendium_Disease | run-2 | 74590 | 0.0% | 4 |
| generate_content_report_for_compendium_Drug | run-6 | 75153 | 0.0% | 4 |
| generate_content_report_for_compendium_Gene | run-3 | 74761 | 0.0% | 4 |
| generate_content_report_for_compendium_GrossAnatomicalStructure | run-2 | 74627 | 0.0% | 4 |
| generate_content_report_for_compendium_MolecularMixture | run-6 | 75158 | 0.0% | 4 |
| generate_content_report_for_compendium_PhenotypicFeature | run-2 | 74594 | 0.0% | 4 |
| generate_content_report_for_compendium_Polypeptide | run-6 | 75137 | 0.0% | 4 |
| generate_content_report_for_compendium_Protein | run-3 | 74815 | 0.0% | 4 |
| generate_content_report_for_compendium_Publication | run-1 | 74526 | 0.0% | 4 |
| generate_content_report_for_compendium_Publication | run-7 | 75404 | 0.0% | 4 |
| generate_content_report_for_compendium_SmallMolecule | run-6 | 75133 | 0.0% | 4 |
| generate_content_report_for_compendium_umls | run-6 | 75182 | 0.0% | 4 |
| generate_content_report_for_compendium_umls | run-7 | 75408 | 0.0% | 4 |
| generate_curie_report | run-6 | 75260 | 0.0% | 4 |
| generate_curie_report | run-7 | 75423 | 0.0% | 4 |
| generate_kgx | run-1 | 74522 | 0.0% | 4 |
| generate_kgx | run-2 | 74589 | 0.0% | 4 |
| generate_kgx | run-2 | 74593 | 0.0% | 4 |
| generate_kgx | run-2 | 74611 | 0.0% | 4 |
| generate_kgx | run-2 | 74619 | 0.0% | 4 |
| generate_kgx | run-2 | 74620 | 0.0% | 4 |
| generate_kgx | run-2 | 74626 | 0.0% | 4 |
| generate_kgx | run-3 | 74759 | 0.0% | 4 |
| generate_kgx | run-3 | 74819 | 0.0% | 4 |
| generate_kgx | run-6 | 75132 | 0.0% | 4 |
| generate_kgx | run-6 | 75138 | 0.0% | 4 |
| generate_kgx | run-6 | 75141 | 0.0% | 4 |
| generate_kgx | run-6 | 75145 | 0.0% | 4 |
| generate_kgx | run-6 | 75151 | 0.0% | 4 |
| generate_kgx | run-6 | 75156 | 0.0% | 4 |
| generate_kgx | run-6 | 75160 | 0.0% | 4 |
| generate_kgx | run-6 | 75180 | 0.0% | 4 |
| generate_kgx | run-7 | 75402 | 0.0% | 4 |
| generate_kgx | run-7 | 75406 | 0.0% | 4 |
| generate_pubmed_compendia | run-1 | 74503 | 0.0% | 4 |
| generate_pubmed_compendia | run-7 | 75397 | 0.0% | 4 |
| generate_pubmed_concords | run-1 | 74287 | 0.0% | 4 |
| generate_sapbert_training_data | run-2 | 74599 | 0.0% | 4 |
| generate_sapbert_training_data | run-2 | 74600 | 0.0% | 4 |
| generate_sapbert_training_data | run-2 | 74631 | 0.0% | 4 |
| generate_sapbert_training_data | run-2 | 74632 | 0.0% | 4 |
| generate_sapbert_training_data | run-2 | 74635 | 0.0% | 4 |
| generate_sapbert_training_data | run-2 | 74636 | 0.0% | 4 |
| generate_sapbert_training_data | run-3 | 74780 | 0.0% | 4 |
| generate_sapbert_training_data | run-3 | 74842 | 0.0% | 4 |
| generate_sapbert_training_data | run-3 | 74944 | 0.0% | 4 |
| generate_sapbert_training_data | run-6 | 75184 | 0.0% | 4 |
| generate_sapbert_training_data | run-6 | 75251 | 0.0% | 4 |
| generate_sapbert_training_data | run-7 | 75413 | 0.0% | 4 |
| generate_summary_content_report_for_compendia | run-6 | 75186 | 0.0% | 4 |
| generate_summary_content_report_for_compendia | run-7 | 75410 | 0.0% | 4 |
| get_HMDB | run-2 | 74577 | 0.0% | 4 |
| get_anatomy_obo_relationships | run-2 | 74576 | 0.0% | 4 |
| get_chemical_unichem_relationships | run-2 | 74606 | 0.0% | 4 |
| get_chemical_unichem_relationships | run-6 | 75029 | 0.0% | 4 |
| get_ensembl | run-2 | 74582 | 0.0% | 4 |
| get_ensembl | run-3 | 74676 | 0.0% | 4 |
| get_unichem | run-2 | 74580 | 0.0% | 4 |
| get_unichem | run-4 | 74978 | 0.0% | 4 |
| get_unichem | run-5 | 75001 | 0.0% | 4 |
| hmdb_labels_and_synonyms | run-2 | 74604 | 0.0% | 4 |
| leftover_umls | run-6 | 75135 | 0.0% | 4 |
| leftover_umls | run-7 | 75401 | 0.0% | 4 |
| protein | run-3 | 74824 | 0.0% | 6 |
| protein_compendia | run-3 | 74729 | 0.0% | 4 |
| protein_ensembl_ids | run-3 | 74727 | 0.0% | 4 |
| pubchem_rxnorm_annotations | run-2 | 74579 | 0.0% | 4 |
| pubchem_rxnorm_relationships | run-2 | 74584 | 0.0% | 4 |
| publications | run-1 | 74528 | 0.0% | 4 |
| publications | run-7 | 75405 | 0.0% | 4 |
| untyped_chemical_compendia | run-6 | 75050 | 0.0% | 4 |

## 5. Rules Needing Retries

*Rules that ran in multiple sbatch runs (indicating earlier failures).*

| Rule | Runs | Final Status |
|------|------|--------------|
| all_outputs | run-6, run-7 | success |
| check_compendia_files | run-6, run-7 | success |
| check_conflation_files | run-6, run-7 | success |
| check_for_duplicate_clique_leaders | run-6, run-7 | success |
| check_for_duplicate_curies | run-6, run-7 | success |
| check_for_identically_labeled_cliques | run-6, run-7 | success |
| check_publications | run-1, run-7 | success |
| check_publications_completeness | run-1, run-7 | success |
| check_synonyms_gzipped_files | run-6, run-7 | success |
| chemical_chebi_ids | run-1, run-2 | success |
| chemical_drugbank_ids | run-1, run-2, run-6 | success |
| compress_umls | run-6, run-7 | success |
| disease_manual_concord | run-1, run-2 | success |
| export_all_compendia_to_duckdb | run-6, run-7 | success |
| export_all_synonyms_to_duckdb | run-6, run-7 | success |
| export_all_to_duckdb | run-6, run-7 | success |
| export_all_to_kgx | run-6, run-7 | success |
| export_all_to_sapbert_training | run-6, run-7 | success |
| export_compendia_to_duckdb | run-1, run-2, run-3, run-6, run-7 | success |
| export_synonyms_to_duckdb | run-1, run-2, run-3, run-6, run-7 | success |
| filter_unichem | run-1, run-2, run-6 | success |
| generate_by_clique_report | run-6, run-7 | success |
| generate_content_report_for_compendium_Publication | run-1, run-7 | success |
| generate_content_report_for_compendium_umls | run-6, run-7 | success |
| generate_curie_report | run-6, run-7 | success |
| generate_kgx | run-1, run-2, run-3, run-6, run-7 | success |
| generate_pubmed_compendia | run-1, run-7 | success |
| generate_sapbert_training_data | run-1, run-2, run-3, run-6, run-7 | success |
| generate_summary_content_report_for_compendia | run-6, run-7 | success |
| get_HMDB | run-1, run-2 | success |
| get_anatomy_obo_relationships | run-1, run-2 | success |
| get_chemical_unichem_relationships | run-1, run-2, run-3, run-6 | success |
| get_ensembl | run-1, run-2, run-3 | success |
| get_unichem | run-1, run-2, run-4, run-5 | success |
| leftover_umls | run-6, run-7 | success |
| pubchem_rxnorm_annotations | run-1, run-2 | success |
| publications | run-1, run-7 | success |

## 6. Logging Improvement Suggestions

The following improvements to the Babel pipeline would make future log analysis significantly easier:

### 6.1 Add `onsuccess`/`onerror` Snakemake hooks

Add `onsuccess` and `onerror` hooks to the main Snakefile that write a structured `run_summary.json` file listing failed rules, total job counts, and run duration. This eliminates the need to parse unstructured logs for basic run statistics.

### 6.2 Explicit resource declarations in snakefiles

Currently, resources come from a SLURM profile rather than individual rule declarations. Adding `resources: mem_mb=..., runtime=...` directly to each rule in `data/src/snakefiles/*.snakefile` makes resource tuning visible in code review and auditable. It also enables per-rule tuning based on observed actual usage.

### 6.3 Post-job `sacct` capture for actual memory/CPU usage

Wrap SLURM job scripts to run `sacct -j $SLURM_JOB_ID --format=MaxRSS,Elapsed,CPUTimeRAW -n` on completion and append actual resource usage to the rule's log file. This enables true memory utilization analysis (currently impossible from these logs alone).

### 6.4 Log output file sizes at rule completion

Add a `shell` snippet or Python statement at the end of each rule to log the sizes of key output files. This catches silent failures (0-byte or truncated outputs) before downstream rules consume bad data.

### 6.5 Timestamp rule log completion explicitly

Rule log files currently only contain failure timestamps; success is only recorded in the sbatch controller log. Adding an explicit completion line to each rule (e.g., via a Snakemake wrapper script) would make rule logs self-contained and simplify per-rule duration analysis.

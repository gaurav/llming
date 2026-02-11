# CTD MeSH IDs Enrichment Project

## Overview

This project contains a Python script (`enrich_mesh_types.py`) that enriches MeSH (Medical Subject Headings) identifiers from the CTD (Comparative Toxicogenomics Database) with hierarchical classification information from the NLM MeSH API.

## What the Script Does

### Input
- Reads `data/ctd-mesh-ids.tsv` - a TSV file with MeSH identifiers in the format "MESH:D012345" or "MESH:C012345"
- Original columns: CTD-ASSIGNED CONCEPT ID, CTD-ASSIGNED CONCEPT NAME, CTD-ASSIGNED CONCEPT CATEGORY

### Output
- Creates `data/ctd-mesh-ids-enriched.tsv` with five additional columns:
  1. **MESH_LABEL**: Official concept name from MeSH API
  2. **MESH_TREE_NUMBERS**: Full hierarchical tree positions (e.g., "D04.345.566;D12.644.641")
  3. **MESH_TREE_LABELS**: Descriptor labels for those tree positions (e.g., "Peptides, Cyclic")
  4. **MESH_TREE_TOP_CODES**: Top-level category codes (e.g., "D04;D12")
  5. **MESH_TREE_TOP_LABELS**: Labels for top-level categories (e.g., "Polycyclic Compounds;Amino Acids, Peptides, and Proteins")

### How It Works

1. **Primary Lookup**: Queries the MeSH API at `https://id.nlm.nih.gov/mesh/{id}.json` for each identifier
2. **Supplementary Concept Handling**: Many CTD concepts are supplementary records (C-numbers) that don't have tree numbers. For these, the script:
   - Looks for the `preferredMappedTo` field
   - Follows the mapping to the preferred descriptor
   - Uses that descriptor's tree numbers and label
3. **Tree Label Extraction**: Tree numbers belong to descriptors; all tree numbers for a descriptor share that descriptor's label
4. **Top-Level Label Lookup**: Uses SPARQL queries against `https://id.nlm.nih.gov/mesh/sparql` to find which descriptor exists at each top-level tree position

### Technical Details

- **Dependencies**: requests, click, tqdm
- **Rate Limiting**: 0.2s delay between rows (configurable with `--delay`)
- **Caching**: Uses `@lru_cache` for tree descriptor labels to reduce API calls
- **Progress**: tqdm progress bar with time estimates
- **Logging**: Configurable log levels (DEBUG, INFO, WARNING, ERROR)
- **Performance**: Processes ~2.9 rows/second, ~773 rows in ~4.5 minutes

### Usage

```bash
# Basic usage
uv run enrich_mesh_types.py

# Custom output file
uv run enrich_mesh_types.py -o custom-output.tsv

# Adjust rate limiting (faster, but be respectful to API)
uv run enrich_mesh_types.py --delay 0.1

# Debug mode (see all API interactions)
uv run enrich_mesh_types.py --log-level DEBUG

# Quiet mode (only errors)
uv run enrich_mesh_types.py --log-level ERROR
```

## Current Results

On the current dataset (773 MeSH identifiers):
- **87% (672)** successfully enriched with tree numbers
- **13% (101)** have no tree numbers even after checking preferredMappedTo
- Most successful enrichments use preferredMappedTo (supplementary concepts mapping to descriptors)

## Known Issues & Limitations

1. **Supplementary Concepts**: Many C-numbers don't have tree numbers and no preferredMappedTo mapping, leaving them unenriched
2. **API Response Formats**: MeSH API returns data in multiple JSON-LD formats that require careful parsing
3. **Performance**: SPARQL queries for tree top labels add significant overhead (~10s of API calls per row in worst case)
4. **Tree Number URIs**: Tree numbers can be returned as full URIs (`http://id.nlm.nih.gov/mesh/D04.345.566`) or bare codes (`D04.345.566`) requiring normalization

## Suggested Improvements for Future Sessions

### Performance Optimizations
1. **Batch SPARQL Queries**: Instead of querying each tree top code individually, collect all unique top-level codes and query them in a single SPARQL request
2. **Persistent Cache**: Save tree label cache to disk (JSON/SQLite) to avoid re-querying across runs
3. **Parallel Processing**: Use `concurrent.futures` or `asyncio` to query multiple MeSH IDs simultaneously (respect rate limits)
4. **Resume Capability**: Track processed IDs to allow resuming interrupted runs

### Enhanced Functionality
1. **Full Tree Path**: Extract complete hierarchical path with labels at each level (not just top-level)
2. **Alternative Mappings**: If preferredMappedTo fails, try `mappedTo` field (broader mappings)
3. **Descriptor Types**: Add column indicating whether concept is a Descriptor, SCR_Chemical, SCR_Disease, etc.
4. **Relationship Data**: Extract broader/narrower terms, related concepts
5. **Historical Data**: Track dateIntroduced, lastUpdated fields

### Robustness
1. **Retry Logic**: Add exponential backoff for failed API calls
2. **Validation**: Check that tree numbers follow expected patterns (e.g., letter followed by numbers and dots)
3. **Output Validation**: Verify all rows were written, check for data corruption
4. **Error Recovery**: Save problem IDs to separate file for manual review

### User Experience
1. **Dry Run Mode**: Preview what will be enriched without making API calls
2. **Summary Report**: Generate markdown/HTML report with statistics, charts of coverage by category
3. **Diff Mode**: Compare two enrichment runs to see what changed
4. **Interactive Mode**: Prompt for confirmation on ambiguous mappings

### Code Quality
1. **Type Hints**: Add comprehensive type annotations throughout
2. **Unit Tests**: Test label extraction, tree number parsing, SPARQL query building
3. **Documentation**: Add docstring examples, improve inline comments
4. **Configuration File**: Support YAML/TOML config for default options

## MeSH API Endpoints Reference

- **Descriptor/Concept**: `https://id.nlm.nih.gov/mesh/{id}.json`
- **SPARQL Endpoint**: `https://id.nlm.nih.gov/mesh/sparql?query={encoded_query}&format=JSON`
- **Tree Number**: `https://id.nlm.nih.gov/mesh/{tree_number}.json` (returns TreeNumber object, not descriptor)

## Data Notes

- **Descriptor IDs**: Start with D (e.g., D010456)
- **Supplementary Concept IDs**: Start with C (e.g., C471568)
- **Tree Numbers**: Hierarchical codes like "D04.345.566" where:
  - First letter = top category (A=Anatomy, B=Organisms, C=Diseases, D=Chemicals, etc.)
  - Numbers before first dot = second-level category
  - Subsequent numbers = deeper hierarchy

## Related Files

- `data/ctd-mesh-ids.tsv` - Input file with CTD MeSH identifiers
- `data/ctd-mesh-ids-enriched.tsv` - Output file with enriched data
- `enrich_mesh_types.py` - Main enrichment script

## Session Context

This script was developed to help understand and classify chemical entities and other biomedical concepts from CTD by mapping them to the standardized MeSH hierarchy. The enriched tree numbers enable:
- Grouping concepts by therapeutic/chemical class
- Understanding hierarchical relationships
- Filtering by specific branches of the MeSH tree
- Integration with other systems that use MeSH classifications

#!/usr/bin/env python3
# /// script
# requires-python = ">=3.8"
# dependencies = [
#     "requests",
#     "click",
#     "tqdm",
# ]
# ///
"""
Script to enrich MeSH identifiers with detailed hierarchical information.

Reads a TSV file with MeSH IDs and outputs a CSV file with the following additional columns:
- MESH_LABEL: The primary label/name for the MeSH concept
- MESH_TREE_NUMBERS: Full tree numbers (semicolon-separated if multiple)
- MESH_TREE_LABELS: Labels for each tree number (semicolon-separated)
- MESH_TREE_TOP_CODES: First part of tree numbers before '.' (semicolon-separated)
- MESH_TREE_TOP_LABELS: Labels for the top-level tree codes (semicolon-separated)
"""

import csv
import sys
import time
import logging
import click
import requests
from tqdm import tqdm
from typing import Dict, List, Tuple, Optional
from collections import defaultdict
from functools import lru_cache

@lru_cache(maxsize=1000)
def get_tree_descriptor_label(tree_number: str) -> Optional[str]:
    """
    Query MeSH SPARQL endpoint to find the descriptor at a tree position and get its label.

    Args:
        tree_number: MeSH tree number (e.g., 'D03.633' or 'D04')

    Returns:
        Label for the descriptor at this tree position, or None if not found
    """
    try:
        # Build SPARQL query to find descriptor with this tree number
        sparql_query = f"""PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
PREFIX meshv: <http://id.nlm.nih.gov/mesh/vocab#>
PREFIX mesh: <http://id.nlm.nih.gov/mesh/>

SELECT ?label
FROM <http://id.nlm.nih.gov/mesh>

WHERE {{
  ?descriptor meshv:treeNumber mesh:{tree_number} .
  ?descriptor rdfs:label ?label
}}"""

        # Query the SPARQL endpoint
        url = "https://id.nlm.nih.gov/mesh/sparql"
        params = {
            'query': sparql_query,
            'format': 'JSON',
            'limit': 1,
            'inference': 'true'
        }

        response = requests.get(url, params=params, timeout=10)

        if response.status_code == 200:
            data = response.json()

            # Extract label from SPARQL results
            if 'results' in data and 'bindings' in data['results']:
                bindings = data['results']['bindings']
                if bindings and len(bindings) > 0:
                    label_binding = bindings[0].get('label')
                    if label_binding and 'value' in label_binding:
                        return label_binding['value']

        return None

    except Exception as e:
        logging.debug(f"Error looking up tree descriptor label for {tree_number}: {e}")
        return None


def extract_tree_number_from_uri(tree_value: str) -> str:
    """
    Extract tree number from URI or return as-is if already a tree number.

    Args:
        tree_value: Either a URI like "http://id.nlm.nih.gov/mesh/D04.345.566" or "D04.345.566"

    Returns:
        Clean tree number like "D04.345.566"
    """
    if tree_value.startswith('http://') or tree_value.startswith('https://'):
        # Extract the last part of the URI
        return tree_value.split('/mesh/')[-1]
    return tree_value


def get_tree_numbers_from_concept(clean_id: str) -> Tuple[Optional[List[str]], Optional[str], Optional[dict]]:
    """
    Fetch tree numbers and label for a MeSH concept.

    Args:
        clean_id: Clean MeSH identifier without prefix

    Returns:
        Tuple of (tree_numbers list, concept label, full data dict) or (None, None, None) if not found
    """
    url = f"https://id.nlm.nih.gov/mesh/{clean_id}.json"

    try:
        response = requests.get(url, timeout=10)
        if response.status_code != 200:
            return None, None, None

        data = response.json()

        # Extract the label
        label = None
        if 'label' in data:
            if isinstance(data['label'], dict):
                label = data['label'].get('@value') or data['label'].get('en')
            else:
                label = data['label']
        elif 'name' in data:
            label = data['name']
        elif '@graph' in data and len(data['@graph']) > 0:
            graph_label = data['@graph'][0].get('label')
            if isinstance(graph_label, dict):
                label = graph_label.get('@value') or graph_label.get('en')
            else:
                label = graph_label

        # Extract tree numbers (can be in various formats)
        tree_numbers_raw = []
        if 'treeNumber' in data:
            tree_numbers_raw = data['treeNumber']
        elif 'treeNumbers' in data:
            tree_numbers_raw = data['treeNumbers']
        elif '@graph' in data and len(data['@graph']) > 0:
            tree_numbers_raw = data['@graph'][0].get('treeNumber', [])

        # Convert to list if single value
        if isinstance(tree_numbers_raw, str):
            tree_numbers_raw = [tree_numbers_raw]

        # Extract clean tree numbers from URIs
        tree_numbers = [extract_tree_number_from_uri(tn) for tn in tree_numbers_raw]

        return tree_numbers if tree_numbers else None, label, data

    except Exception:
        return None, None, None


def get_mesh_info(mesh_id: str) -> Tuple[Optional[dict], Optional[str]]:
    """
    Query MeSH API for comprehensive information about a MeSH identifier.

    Args:
        mesh_id: MeSH identifier (e.g., 'D015059' or 'C471568')

    Returns:
        Tuple of (dict with mesh info, error message)
        Dict contains: label, tree_numbers, tree_labels, tree_top_codes, tree_top_labels,
                      used_mapped_concept (bool)
    """
    # Remove MESH: prefix if present
    clean_id = mesh_id.replace('MESH:', '').strip()

    # Build API URL
    url = f"https://id.nlm.nih.gov/mesh/{clean_id}.json"

    try:
        response = requests.get(url, timeout=10)

        if response.status_code == 404:
            return None, f"MeSH ID not found: {mesh_id}"

        if response.status_code != 200:
            return None, f"API error (status {response.status_code}): {mesh_id}"

        data = response.json()

        # Extract the label/name
        label = None
        if 'label' in data:
            if isinstance(data['label'], dict):
                label = data['label'].get('@value') or data['label'].get('en')
            else:
                label = data['label']
        elif 'name' in data:
            if isinstance(data['name'], dict):
                label = data['name'].get('@value') or data['name'].get('en')
            else:
                label = data['name']
        elif '@graph' in data and len(data['@graph']) > 0:
            # Sometimes the data is in @graph format
            graph_data = data['@graph'][0]
            graph_label = graph_data.get('label') or graph_data.get('name')
            if isinstance(graph_label, dict):
                label = graph_label.get('@value') or graph_label.get('en')
            else:
                label = graph_label

        if not label:
            return None, f"No label found for: {mesh_id}"

        # Extract tree numbers
        tree_numbers_raw = []
        used_mapped_concept = False

        if 'treeNumber' in data:
            tree_numbers_raw = data['treeNumber']
        elif 'treeNumbers' in data:
            tree_numbers_raw = data['treeNumbers']
        elif '@graph' in data and len(data['@graph']) > 0:
            tree_numbers_raw = data['@graph'][0].get('treeNumber', [])

        # Convert to list if single value
        if isinstance(tree_numbers_raw, str):
            tree_numbers_raw = [tree_numbers_raw]

        # Extract clean tree numbers from URIs
        tree_numbers = [extract_tree_number_from_uri(tn) for tn in tree_numbers_raw] if tree_numbers_raw else []

        # Track the descriptor label for tree numbers
        descriptor_label_for_trees = label  # Default to the concept's own label

        # If no tree numbers found, try preferredMappedTo
        if not tree_numbers:
            logging.debug(f"No tree numbers for {mesh_id}, checking preferredMappedTo")

            # Look for preferredMappedTo in various locations
            mapped_to = None
            if 'preferredMappedTo' in data:
                mapped_to = data['preferredMappedTo']
            elif '@graph' in data and len(data['@graph']) > 0:
                mapped_to = data['@graph'][0].get('preferredMappedTo')

            if mapped_to:
                # mapped_to can be a single URI or a list
                if isinstance(mapped_to, str):
                    mapped_to = [mapped_to]

                # Try each mapped concept until we find tree numbers
                for mapped_uri in mapped_to:
                    # Extract the ID from the URI (e.g., http://id.nlm.nih.gov/mesh/D123456 -> D123456)
                    if '/' in mapped_uri:
                        mapped_id = mapped_uri.split('/')[-1]
                    else:
                        mapped_id = mapped_uri

                    logging.debug(f"Trying mapped concept: {mapped_id}")
                    mapped_tree_numbers, mapped_label, _ = get_tree_numbers_from_concept(mapped_id)

                    if mapped_tree_numbers:
                        tree_numbers = mapped_tree_numbers
                        descriptor_label_for_trees = mapped_label or label
                        used_mapped_concept = True
                        logging.debug(f"Found tree numbers from mapped concept {mapped_id}")
                        break

        if not tree_numbers:
            return None, f"No tree numbers found for: {mesh_id} (even after checking preferredMappedTo)"

        # Tree labels: all tree numbers for a descriptor share the same label (the descriptor's label)
        tree_labels = [descriptor_label_for_trees] * len(tree_numbers)

        # Extract top-level tree codes (before first dot)
        tree_top_codes = []
        tree_top_labels = []
        seen_tops = set()

        for tree_num in tree_numbers:
            if '.' in tree_num:
                top_code = tree_num.split('.')[0]
            else:
                top_code = tree_num

            if top_code not in seen_tops:
                seen_tops.add(top_code)
                tree_top_codes.append(top_code)

                # Try to get label for top-level code
                # Note: MeSH API doesn't provide an easy reverse lookup from tree number to descriptor
                # So these labels may often be empty
                top_label = get_tree_descriptor_label(top_code)
                if not top_label or top_label == top_code:
                    # If we can't find a meaningful label, leave it empty
                    tree_top_labels.append("")
                else:
                    tree_top_labels.append(top_label)

        result = {
            'label': label,
            'tree_numbers': tree_numbers,
            'tree_labels': tree_labels,
            'tree_top_codes': tree_top_codes,
            'tree_top_labels': tree_top_labels,
            'used_mapped_concept': used_mapped_concept
        }

        return result, None

    except requests.exceptions.Timeout:
        return None, f"Timeout querying API for: {mesh_id}"
    except requests.exceptions.RequestException as e:
        return None, f"Network error for {mesh_id}: {str(e)}"
    except Exception as e:
        return None, f"Unexpected error for {mesh_id}: {str(e)}"


@click.command()
@click.argument('input_file', type=click.Path(exists=True), default='./data/ctd-mesh-ids.tsv')
@click.option('-o', '--output', 'output_file',
              type=click.Path(),
              default='./data/ctd-mesh-ids-enriched.csv',
              help='Output file path (default: ./data/ctd-mesh-ids-enriched.csv)')
@click.option('-d', '--delay',
              type=float,
              default=0.2,
              help='Delay between rows in seconds (default: 0.2). Note: multiple API calls may be made per row.')
@click.option('--log-level',
              type=click.Choice(['DEBUG', 'INFO', 'WARNING', 'ERROR'], case_sensitive=False),
              default='INFO',
              help='Set logging level (default: INFO)')
def main(input_file, output_file, delay, log_level):
    """
    Enrich MeSH identifiers with top-level type information.

    Reads INPUT_FILE (TSV with MeSH IDs) and outputs a CSV file with type identifier and label columns.
    """
    # Configure logging
    logging.basicConfig(
        level=getattr(logging, log_level.upper()),
        format='%(levelname)s: %(message)s',
        stream=sys.stderr
    )
    # Track statistics
    total = 0
    success = 0
    errors = 0
    concepts_without_tree_numbers = 0
    concepts_using_mapped = 0
    error_messages = defaultdict(int)

    try:
        # First, count total rows for accurate progress estimation
        logging.debug(f"Counting rows in {input_file}")
        with open(input_file, 'r', encoding='utf-8') as count_file:
            # Count non-header rows
            total_rows = sum(1 for _ in count_file) - 1  # Subtract 1 for header
        logging.debug(f"Found {total_rows} rows to process")

        with open(input_file, 'r', encoding='utf-8') as infile, \
             open(output_file, 'w', encoding='utf-8', newline='') as outfile:

            reader = csv.DictReader(infile, delimiter='\t')

            if not reader.fieldnames:
                logging.error("Could not read header from input file")
                sys.exit(1)

            # Add new columns for MeSH information
            fieldnames = list(reader.fieldnames) + [
                'MESH_LABEL',
                'MESH_TREE_NUMBERS',
                'MESH_TREE_LABELS',
                'MESH_TREE_TOP_CODES',
                'MESH_TREE_TOP_LABELS'
            ]
            writer = csv.DictWriter(outfile, fieldnames=fieldnames)
            writer.writeheader()

            # Wrap reader with tqdm for progress bar with total
            for row in tqdm(reader, desc="Processing MeSH IDs", unit=" rows", total=total_rows):
                total += 1
                mesh_id = row.get('CTD-ASSIGNED CONCEPT ID', '')

                if not mesh_id or not mesh_id.startswith('MESH:'):
                    warning = f"Invalid or missing MeSH ID in row {total}: {mesh_id}"
                    logging.warning(warning)
                    error_messages[warning] += 1
                    errors += 1
                    row['MESH_LABEL'] = ''
                    row['MESH_TREE_NUMBERS'] = ''
                    row['MESH_TREE_LABELS'] = ''
                    row['MESH_TREE_TOP_CODES'] = ''
                    row['MESH_TREE_TOP_LABELS'] = ''
                    writer.writerow(row)
                    continue

                # Query MeSH API
                mesh_info, error = get_mesh_info(mesh_id)

                if error:
                    logging.warning(error)
                    error_messages[error[:50]] += 1  # Group similar errors
                    errors += 1
                    # Track if error was due to no tree numbers
                    if "No tree numbers found" in error:
                        concepts_without_tree_numbers += 1
                    row['MESH_LABEL'] = ''
                    row['MESH_TREE_NUMBERS'] = ''
                    row['MESH_TREE_LABELS'] = ''
                    row['MESH_TREE_TOP_CODES'] = ''
                    row['MESH_TREE_TOP_LABELS'] = ''
                else:
                    # Populate new columns with MeSH information
                    row['MESH_LABEL'] = mesh_info['label']
                    row['MESH_TREE_NUMBERS'] = ';'.join(mesh_info['tree_numbers'])
                    row['MESH_TREE_LABELS'] = ';'.join(mesh_info['tree_labels'])
                    row['MESH_TREE_TOP_CODES'] = ';'.join(mesh_info['tree_top_codes'])
                    row['MESH_TREE_TOP_LABELS'] = ';'.join(mesh_info['tree_top_labels'])

                    # Track if we used a mapped concept
                    if mesh_info.get('used_mapped_concept', False):
                        concepts_using_mapped += 1

                    success += 1

                writer.writerow(row)

                # Rate limiting: be nice to the API
                time.sleep(delay)

        # Final summary
        logging.info("="*60)
        logging.info("Processing complete!")
        logging.info(f"Total rows: {total}")
        logging.info(f"Successful: {success}")
        logging.info(f"Errors: {errors}")
        logging.info(f"Concepts without tree numbers: {concepts_without_tree_numbers}")
        logging.info(f"Concepts using preferredMappedTo: {concepts_using_mapped}")
        logging.info(f"Output written to: {output_file}")

        if error_messages:
            logging.info("\nError summary:")
            for msg, count in sorted(error_messages.items(), key=lambda x: -x[1])[:10]:
                logging.info(f"  {count}x: {msg}")

    except FileNotFoundError:
        logging.error(f"Input file not found: {input_file}")
        sys.exit(1)
    except Exception as e:
        logging.error(f"Unexpected error: {str(e)}")
        sys.exit(1)


if __name__ == '__main__':
    main()

#!/usr/bin/env python3
/// script
requires-python = ">=3.8"
dependencies = [
    "requests",
]
///
"""
Script to enrich MeSH identifiers with top-level type information.
Reads a TSV file with MeSH IDs and adds type identifier and label columns.
"""

import csv
import sys
import time
import requests
from typing import Dict, List, Tuple, Optional
from collections import defaultdict

# MeSH top-level category mappings
MESH_CATEGORIES = {
    'A': 'Anatomy',
    'B': 'Organisms',
    'C': 'Diseases',
    'D': 'Chemicals and Drugs',
    'E': 'Analytical, Diagnostic and Therapeutic Techniques, and Equipment',
    'F': 'Psychiatry and Psychology',
    'G': 'Phenomena and Processes',
    'H': 'Disciplines and Occupations',
    'I': 'Anthropology, Education, Sociology, and Social Phenomena',
    'J': 'Technology, Industry, and Agriculture',
    'K': 'Humanities',
    'L': 'Information Science',
    'M': 'Named Groups',
    'N': 'Health Care',
    'V': 'Publication Characteristics',
    'Z': 'Geographicals'
}

def get_mesh_info(mesh_id: str) -> Tuple[Optional[List[str]], Optional[str]]:
    """
    Query MeSH API for tree numbers and extract top-level categories.

    Args:
        mesh_id: MeSH identifier (e.g., 'D015059' or 'C471568')

    Returns:
        Tuple of (list of top-level category codes, error message)
    """
    # Remove MESH: prefix if present
    mesh_id = mesh_id.replace('MESH:', '').strip()

    # Build API URL
    url = f"https://id.nlm.nih.gov/mesh/{mesh_id}.json"

    try:
        response = requests.get(url, timeout=10)

        if response.status_code == 404:
            return None, f"MeSH ID not found: {mesh_id}"

        if response.status_code != 200:
            return None, f"API error (status {response.status_code}): {mesh_id}"

        data = response.json()

        # Extract tree numbers
        tree_numbers = []
        if 'treeNumbers' in data:
            tree_numbers = data['treeNumbers']

        if not tree_numbers:
            return None, f"No tree numbers found for: {mesh_id}"

        # Extract top-level categories (first letter of tree number)
        top_level_codes = set()
        for tree_num in tree_numbers:
            if tree_num and len(tree_num) > 0:
                top_level_codes.add(tree_num[0])

        if not top_level_codes:
            return None, f"Could not extract top-level categories for: {mesh_id}"

        return sorted(list(top_level_codes)), None

    except requests.exceptions.Timeout:
        return None, f"Timeout querying API for: {mesh_id}"
    except requests.exceptions.RequestException as e:
        return None, f"Network error for {mesh_id}: {str(e)}"
    except Exception as e:
        return None, f"Unexpected error for {mesh_id}: {str(e)}"


def main():
    input_file = './ctd-mesh-ids.tsv'
    output_file = './ctd-mesh-ids-enriched.tsv'

    # Track statistics
    total = 0
    success = 0
    errors = 0
    error_messages = defaultdict(int)

    try:
        with open(input_file, 'r', encoding='utf-8') as infile, \
             open(output_file, 'w', encoding='utf-8', newline='') as outfile:

            reader = csv.DictReader(infile, delimiter='\t')

            if not reader.fieldnames:
                print("ERROR: Could not read header from input file", file=sys.stderr)
                return 1

            # Add new columns for type information
            fieldnames = list(reader.fieldnames) + ['MESH_TOP_LEVEL_CODES', 'MESH_TOP_LEVEL_LABELS']
            writer = csv.DictWriter(outfile, fieldnames=fieldnames, delimiter='\t')
            writer.writeheader()

            for row in reader:
                total += 1
                mesh_id = row.get('CTD-ASSIGNED CONCEPT ID', '')

                if not mesh_id or not mesh_id.startswith('MESH:'):
                    warning = f"Invalid or missing MeSH ID in row {total}: {mesh_id}"
                    print(f"WARNING: {warning}", file=sys.stderr)
                    error_messages[warning] += 1
                    errors += 1
                    row['MESH_TOP_LEVEL_CODES'] = ''
                    row['MESH_TOP_LEVEL_LABELS'] = ''
                    writer.writerow(row)
                    continue

                # Query MeSH API
                top_level_codes, error = get_mesh_info(mesh_id)

                if error:
                    print(f"WARNING: {error}", file=sys.stderr)
                    error_messages[error[:50]] += 1  # Group similar errors
                    errors += 1
                    row['MESH_TOP_LEVEL_CODES'] = ''
                    row['MESH_TOP_LEVEL_LABELS'] = ''
                else:
                    # Map codes to labels
                    labels = [MESH_CATEGORIES.get(code, f'Unknown-{code}') for code in top_level_codes]

                    row['MESH_TOP_LEVEL_CODES'] = ';'.join(top_level_codes)
                    row['MESH_TOP_LEVEL_LABELS'] = ';'.join(labels)
                    success += 1

                writer.writerow(row)

                # Progress indicator
                if total % 100 == 0:
                    print(f"Processed {total} rows ({success} success, {errors} errors)...", file=sys.stderr)

                # Rate limiting: be nice to the API
                time.sleep(0.1)

        # Final summary
        print(f"\n{'='*60}", file=sys.stderr)
        print(f"Processing complete!", file=sys.stderr)
        print(f"Total rows: {total}", file=sys.stderr)
        print(f"Successful: {success}", file=sys.stderr)
        print(f"Errors: {errors}", file=sys.stderr)
        print(f"Output written to: {output_file}", file=sys.stderr)

        if error_messages:
            print(f"\nError summary:", file=sys.stderr)
            for msg, count in sorted(error_messages.items(), key=lambda x: -x[1])[:10]:
                print(f"  {count}x: {msg}", file=sys.stderr)

        return 0

    except FileNotFoundError:
        print(f"ERROR: Input file not found: {input_file}", file=sys.stderr)
        return 1
    except Exception as e:
        print(f"ERROR: Unexpected error: {str(e)}", file=sys.stderr)
        return 1


if __name__ == '__main__':
    sys.exit(main())

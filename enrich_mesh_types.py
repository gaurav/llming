#!/usr/bin/env python3
/// script
requires-python = ">=3.8"
dependencies = [
    "requests",
    "click",
]
///
"""
Script to enrich MeSH identifiers with top-level type information.
Reads a TSV file with MeSH IDs and adds type identifier and label columns.
"""

import csv
import sys
import time
import logging
import click
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


@click.command()
@click.argument('input_file', type=click.Path(exists=True), default='./ctd-mesh-ids.tsv')
@click.option('-o', '--output', 'output_file',
              type=click.Path(),
              default='./ctd-mesh-ids-enriched.tsv',
              help='Output file path (default: ./ctd-mesh-ids-enriched.tsv)')
@click.option('-d', '--delay',
              type=float,
              default=0.1,
              help='Delay between API requests in seconds (default: 0.1)')
@click.option('--log-level',
              type=click.Choice(['DEBUG', 'INFO', 'WARNING', 'ERROR'], case_sensitive=False),
              default='INFO',
              help='Set logging level (default: INFO)')
def main(input_file, output_file, delay, log_level):
    """
    Enrich MeSH identifiers with top-level type information.

    Reads INPUT_FILE (TSV with MeSH IDs) and adds type identifier and label columns.
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
    error_messages = defaultdict(int)

    try:
        with open(input_file, 'r', encoding='utf-8') as infile, \
             open(output_file, 'w', encoding='utf-8', newline='') as outfile:

            reader = csv.DictReader(infile, delimiter='\t')

            if not reader.fieldnames:
                logging.error("Could not read header from input file")
                sys.exit(1)

            # Add new columns for type information
            fieldnames = list(reader.fieldnames) + ['MESH_TOP_LEVEL_CODES', 'MESH_TOP_LEVEL_LABELS']
            writer = csv.DictWriter(outfile, fieldnames=fieldnames, delimiter='\t')
            writer.writeheader()

            for row in reader:
                total += 1
                mesh_id = row.get('CTD-ASSIGNED CONCEPT ID', '')

                if not mesh_id or not mesh_id.startswith('MESH:'):
                    warning = f"Invalid or missing MeSH ID in row {total}: {mesh_id}"
                    logging.warning(warning)
                    error_messages[warning] += 1
                    errors += 1
                    row['MESH_TOP_LEVEL_CODES'] = ''
                    row['MESH_TOP_LEVEL_LABELS'] = ''
                    writer.writerow(row)
                    continue

                # Query MeSH API
                top_level_codes, error = get_mesh_info(mesh_id)

                if error:
                    logging.warning(error)
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

                # Progress indicators
                if total % 100 == 0:
                    logging.debug(f"Processed {total} rows ({success} success, {errors} errors)")
                if total % 500 == 0:
                    logging.info(f"Processed {total} rows")

                # Rate limiting: be nice to the API
                time.sleep(delay)

        # Final summary
        logging.info("="*60)
        logging.info("Processing complete!")
        logging.info(f"Total rows: {total}")
        logging.info(f"Successful: {success}")
        logging.info(f"Errors: {errors}")
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

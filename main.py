import argparse
import os
import sys
from src.audit.audit_engine import audit_global_trials
from src.audit.svef_refinement import refine_svef_assets
from src.audit.smiles_recovery import recover_smiles

def main():
    parser = argparse.ArgumentParser(description="Global AACT Audit & Tiered SMILES Recovery Pipeline")
    parser.add_argument('--audit', action='store_true', help="Run Module 1: Global Denominator Analysis")
    parser.add_argument('--refine', action='store_true', help="Run Module 2: Targeted Asset Identification")
    parser.add_argument('--enrich', action='store_true', help="Run Module 3: Tiered Chemical Enrichment")
    parser.add_argument('--all', action='store_true', help="Run all modules in sequence")
    
    args = parser.parse_args()
    
    # Check for .svef virtual environment
    if not os.path.exists('.svef'):
        print("Error: .svef virtual environment not found. Please follow installation guide.")
        sys.exit(1)
        
    raw_dir = 'data/raw'
    processed_dir = 'data/processed'
    if not os.path.exists(processed_dir):
        os.makedirs(processed_dir)
        
    if args.all or args.audit:
        audit_global_trials(raw_dir, processed_dir)
        
    if args.all or args.refine:
        refine_svef_assets(processed_dir)
        
    if args.all or args.enrich:
        recover_smiles(processed_dir)
        
    if not any([args.audit, args.refine, args.enrich, args.all]):
        parser.print_help()

if __name__ == "__main__":
    main()

import pandas as pd
import sys

def audit_interventions():
    file_path = 'data/raw/interventions.txt'
    output_path = 'intervention_type_audit.csv'
    
    print(f"Loading {file_path} with memory-efficient usecols...")
    try:
        # Load only the intervention_type column
        # Using sep='|' as requested
        df = pd.read_csv(file_path, sep='|', usecols=['intervention_type'])
        
        # Count unique values
        counts = df['intervention_type'].value_counts().reset_index()
        counts.columns = ['intervention_type', 'count']
        
        # Sort by count descending
        counts = counts.sort_values(by='count', ascending=False)
        
        # Display the results
        print("\nIntervention Type Audit Results:")
        print(counts.to_string(index=False))
        
        # Save to CSV
        counts.to_csv(output_path, index=False)
        print(f"\nResults saved to {output_path}")
        
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    audit_interventions()

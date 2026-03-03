import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from matplotlib_venn import venn2
import os

def load_and_prepare_data(file_path):
    """
    Load the enriched dataset and create indicator variables.
    """
    print(f"Loading data from {file_path}...")
    df = pd.read_csv(file_path)
    
    # Create indicator variables
    df['has_pub'] = df['publication_count'].fillna(0) > 0
    df['has_smiles'] = df['is_dti_ready'].fillna(False)
    
    return df

def analyze_contingency(df):
    """
    Generate and print a 2x2 contingency table.
    """
    contingency = pd.crosstab(df['has_pub'], df['has_smiles'], 
                              rownames=['Has Publication'], 
                              colnames=['Has SMILES'])
    print("\n--- Contingency Table (Counts) ---")
    print(contingency)
    
    # Percentages
    print("\n--- Contingency Table (Percentages) ---")
    print((contingency / len(df)) * 100)
    
    return contingency

def identify_gold_standard(df, output_path):
    """
    Export candidates with both publications and SMILES data.
    """
    gold_standard = df[df['has_pub'] & df['has_smiles']]
    print(f"\nIdentified {len(gold_standard)} 'Gold Standard' candidates.")
    
    gold_standard.to_csv(output_path, index=False)
    print(f"Gold Standard subset saved to: {output_path}")
    
    return gold_standard

def plot_coverage(df, output_dir):
    """
    Create Venn diagram and Stacked Bar Chart.
    """
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
        
    # 1. Venn Diagram
    plt.figure(figsize=(8, 8))
    v = venn2(subsets=(
        len(df[df['has_pub'] & ~df['has_smiles']]), # Ab
        len(df[~df['has_pub'] & df['has_smiles']]), # aB
        len(df[df['has_pub'] & df['has_smiles']])   # AB
    ), set_labels=('Has Publication', 'Has SMILES'))
    plt.title("Overlap of Scholarly Evidence and Chemical SMILES Data")
    venn_path = os.path.join(output_dir, 'coverage_venn.png')
    plt.savefig(venn_path)
    print(f"Venn diagram saved to: {venn_path}")
    plt.close()

    # 2. Stacked Bar Chart
    plt.figure(figsize=(10, 6))
    summary = df.groupby(['has_smiles', 'has_pub']).size().unstack()
    summary.plot(kind='bar', stacked=True, color=['#ff9999','#66b3ff'])
    plt.title("Publication Status by SMILES Availability")
    plt.xlabel("Has SMILES Data")
    plt.ylabel("Number of Candidates")
    plt.xticks([0, 1], ['No SMILES', 'Has SMILES'], rotation=0)
    plt.legend(title="Has Publication")
    bar_path = os.path.join(output_dir, 'coverage_stacked_bar.png')
    plt.savefig(bar_path)
    print(f"Stacked bar chart saved to: {bar_path}")
    plt.close()

def main():
    input_file = os.path.join('data', 'processed', 'SVEF_Enriched_Final.csv')
    gold_output = os.path.join('data', 'processed', 'SVEF_Gold_Standard_Candidates.csv')
    figures_dir = os.path.join('reports', 'figures')
    
    df = load_and_prepare_data(input_file)
    
    # Analysis
    analyze_contingency(df)
    
    # Statistics
    avg_safety_gold = df[df['has_pub'] & df['has_smiles']]['Safety_Score'].mean()
    avg_safety_rest = df[~(df['has_pub'] & df['has_smiles'])]['Safety_Score'].mean()
    print(f"\nAverage Safety_Score (Gold Standard): {avg_safety_gold:.4f}")
    print(f"Average Safety_Score (Others): {avg_safety_rest:.4f}")
    
    # Identification
    identify_gold_standard(df, gold_output)
    
    # Visualization
    plot_coverage(df, figures_dir)
    
    print("\nAnalysis Complete.")

if __name__ == "__main__":
    main()

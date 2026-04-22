import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import os
import numpy as np
from matplotlib_venn import venn2

def load_and_prepare_data(file_path):
    """
    Load the enriched dataset and prepare indicator flags for coverage analysis.
    """
    if not os.path.exists(file_path):
        print(f"Error: File {file_path} not found.")
        return None
        
    df = pd.read_csv(file_path)
    
    # Coverage Flags
    df['has_smiles'] = df['smiles'].notnull()
    df['has_pub'] = df['publication_count'].fillna(0) > 0
    df['is_gold_standard'] = df['has_smiles'] & df['has_pub']
    
    return df

def plot_recovery_tiers(df, output_dir):
    """
    Visualizes the effectiveness of the Tiered Recovery system.
    """
    plt.figure(figsize=(10, 6))
    tier_counts = df['matched_by'].fillna('Failed').value_counts()
    sns.barplot(x=tier_counts.index, y=tier_counts.values, palette='magma', hue=tier_counts.index, legend=False)
    plt.title("Bioinformatics Recovery Success by Tier")
    plt.ylabel("Number of Assets")
    plt.savefig(os.path.join(output_dir, 'recovery_tiers.png'))
    plt.close()

def plot_lipinski_compliance(df, output_dir):
    """
    Visualizes Druggability (Lipinski Compliance).
    Handles missing SMILES as 'Undetermined'.
    """
    df_plot = df.copy()
    df_plot['Lipinski_Status'] = 'Undetermined (No SMILES)'
    df_plot.loc[df_plot['is_dti_ready'] & df_plot['is_lipinski_compliant'], 'Lipinski_Status'] = 'Compliant'
    df_plot.loc[df_plot['is_dti_ready'] & ~df_plot['is_lipinski_compliant'], 'Lipinski_Status'] = 'Non-Compliant'
    
    plt.figure(figsize=(10, 6))
    sns.countplot(data=df_plot, x='Lipinski_Status', palette='Set2', hue='Lipinski_Status', legend=False)
    plt.title("Lipinski Druggability Compliance (Rule of 5)")
    plt.ylabel("Asset Count")
    plt.savefig(os.path.join(output_dir, 'lipinski_compliance.png'))
    plt.close()

def plot_safety_distribution(df, output_dir):
    """
    Plots safety score distribution.
    Identifies 'Unknown Safety' count in the chart text.
    """
    missing_safety = df['Safety_Score'].isna().sum()
    valid_safety = df.dropna(subset=['Safety_Score'])
    
    plt.figure(figsize=(10, 6))
    sns.histplot(valid_safety['Safety_Score'], bins=30, kde=True, color='teal')
    plt.title("Safety Score Distribution (Human Exposure)")
    plt.xlabel("Safety Score (Normalized)")
    plt.text(0.95, 0.95, f"Missing Data: {missing_safety}", 
             transform=plt.gca().transAxes, ha='right', va='top', bbox=dict(facecolor='white', alpha=0.5))
    plt.savefig(os.path.join(output_dir, 'safety_distribution.png'))
    plt.close()

def plot_enrollment_comparison(df, output_dir):
    """
    Generates two charts: Raw Enrollment and Log-Normalized Enrollment.
    """
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 6))
    
    # 1. Raw Enrollment
    sns.histplot(df['enrollment'].dropna(), bins=50, ax=ax1, color='blue', log_scale=True)
    ax1.set_title("Trial Enrollment (Raw Counts - Log Scale X)")
    ax1.set_xlabel("Number of Participants")
    
    # 2. Log-Normalized Enrollment (The new feature)
    sns.histplot(df['log_enrollment'].dropna(), bins=30, ax=ax2, color='darkblue', kde=True)
    ax2.set_title("Log-Normalized Enrollment (Architect Metric)")
    ax2.set_xlabel("log1p(Enrollment)")
    
    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, 'enrollment_comparison.png'))
    plt.close()

def plot_coverage_venn(df, output_dir):
    """
    Venn Diagram of Chemical vs Evidence coverage.
    """
    plt.figure(figsize=(8, 8))
    smiles_set = set(df[df['has_smiles']]['nct_id'])
    pub_set = set(df[df['has_pub']]['nct_id'])
    
    venn2([smiles_set, pub_set], ('Has SMILES', 'Has Publications'))
    plt.title("Candidate Coverage: Chemical vs. Evidence")
    plt.savefig(os.path.join(output_dir, 'coverage_venn.png'))
    plt.close()

def main():
    input_file = os.path.join('data', 'processed', 'SVEF_Enriched_Final.csv')
    figures_dir = os.path.join('reports', 'figures')
    
    if not os.path.exists(figures_dir):
        os.makedirs(figures_dir)
        
    df = load_and_prepare_data(input_file)
    if df is None: return

    print("Generating upgraded Bioinformatics visualizations...")
    
    plot_recovery_tiers(df, figures_dir)
    plot_lipinski_compliance(df, figures_dir)
    plot_safety_distribution(df, figures_dir)
    plot_enrollment_comparison(df, figures_dir)
    plot_coverage_venn(df, figures_dir)
    
    # Export Gold Standard
    gold_std = df[df['is_gold_standard']].copy()
    gold_output = os.path.join('data', 'processed', 'SVEF_Gold_Standard_Candidates.csv')
    gold_std.to_csv(gold_output, index=False)
    
    print(f"\nAnalysis Complete. Gold Standard Count: {len(gold_std)}")
    print(f"Reports saved to {figures_dir}")

if __name__ == "__main__":
    main()

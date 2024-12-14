# /// script
# requires-python = ">=3.11"
# dependencies = [
#   "pandas",
#   "matplotlib",
#   "seaborn",
#   "httpx",
#   "chardet"
# ]
# ///

import os
import sys
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import httpx
import chardet
from pathlib import Path

import os

def get_ai_proxy_token():
    """
    Retrieve the AI Proxy token from an environment variable.
    """
    api_token = os.getenv("AIPROXY_TOKEN")
    if not api_token:
        raise ValueError("AIPROXY_TOKEN environment variable is not set.")
    return api_token


def generate_story_with_ai(summary_data=None, analysis=None, use_summary=True):
    """
    Generate a story or detailed analysis using GPT-4o-Mini via AI Proxy.

    Parameters:
        summary_data (str): Data insights to generate a story.
        analysis (str): Detailed analysis data.
        use_summary (bool): If True, uses summary_data for story; otherwise, uses analysis for detailed analysis.

    Returns:
        str: Generated story or analysis.
    """
    print("Generating story with AI...")
    token = get_ai_proxy_token()
    if not token:
        raise ValueError("AI Proxy token is required.")

    url = "https://aiproxy.sanand.workers.dev/openai/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }

    # Decide which prompt to use
    if use_summary:
        if not summary_data:
            raise ValueError("Summary data is required for story generation.")
        prompt = f"Generate a short story in 100 words based on the following data insight and then a adetailed analysis with a seperate heading: {summary_data}"
    else:
        if not analysis:
            raise ValueError("Analysis data is required for detailed analysis.")
        prompt = f"Provide a detailed analysis based on the following data summary: {analysis}"

    payload = {
        "model": "gpt-4o-mini",
        "messages": [
            {"role": "system", "content": "You are an AI assistant."},
            {"role": "user", "content": prompt}
        ],
        "max_tokens": 300,
    }

    try:
        response = httpx.post(url, json=payload, headers=headers, timeout=30.0)
        print(f"Response Status Code: {response.status_code}")
        if response.status_code == 200:
            return response.json().get("choices", [{}])[0].get("message", {}).get("content", "No response text found.")
        else:
            print(f"Error: {response.status_code}, {response.text}")
            return "Error generating story or analysis."
    except Exception as e:
        print(f"Error communicating with AI Proxy: {e}")
        return "Error generating story or analysis."


def load_data(file_path):
    """
    Load CSV data with encoding detection.
    """
    try:
        with open(file_path, 'rb') as f:
            result = chardet.detect(f.read())
        encoding = result['encoding']
        return pd.read_csv(file_path, encoding=encoding)
    except Exception as e:
        print(f"Error loading the CSV file: {e}")
        sys.exit(1)

def analyze_csv(file_path):
    """
    Analyze the given CSV file, generate charts, and write a story to README.md.
    """
    print(f"Analyzing file: {file_path}")

    # Verify if the file exists
    if not Path(file_path).is_file():
        print(f"Error: File '{file_path}' does not exist.")
        return

    print("File exists. Reading the CSV file...")
    try:
        data = load_data(file_path)
        print("CSV file loaded successfully.")
    except Exception as e:
        print(f"Error reading the CSV file: {e}")
        return

    # Extract the base name for the folder
    base_name = Path(file_path).stem
    output_dir = Path(base_name)
    output_dir.mkdir(exist_ok=True)
    print(f"Output directory created: {output_dir}")

    # Generate descriptive statistics
    print("Generating descriptive statistics...")
    desc_stats = data.describe(include='all')
    desc_stats.to_csv(output_dir / "analysis.csv")

    # Count missing values
    print("Counting missing values...")
    missing_values = data.isnull().sum()
    missing_values.to_csv(output_dir / "missing_values.csv")

    # Generate correlation matrix if numerical data exists
    num_cols = data.select_dtypes(include=['float64', 'int64']).columns
    if len(num_cols) > 1:
        print("Generating correlation matrix...")
        correlation_matrix = data[num_cols].corr()
        sns.heatmap(correlation_matrix, annot=True, cmap="coolwarm")
        plt.title("Correlation Matrix")
        plt.savefig(output_dir / "correlation_matrix.png")
        plt.close()

    # Generate histograms for numerical columns
    print("Generating histograms...")
    for col in num_cols:
        plt.figure(figsize=(8, 6))
        sns.histplot(data[col], kde=True)
        plt.title(f"Distribution of {col}")
        plt.savefig(output_dir / f"{col}_histogram.png")
        plt.close()

    # Pair plot for numerical data
    if len(num_cols) > 1:
        print("Generating pair plot...")
        sns.pairplot(data[num_cols])
        plt.savefig(output_dir / "pairplot.png")
        plt.close()

    # Example values for categorical columns
    print("Extracting example values for categorical columns...")
    cat_cols = data.select_dtypes(include=['object']).columns
    example_values = {col: data[col].value_counts().head(5).to_dict() for col in cat_cols}

    # Summary data for AI
    print("Compiling summary data for AI...")
    summary_data = {
        "rows": data.shape[0],
        "columns": data.shape[1],
        "numerical_columns": list(num_cols),
        "categorical_columns": list(cat_cols),
        "missing_values": missing_values.to_dict(),
        "example_values": example_values,
        "top_statistics": desc_stats.to_dict()
    }

    # Generate story using AI
    print("Generating story using AI...")
    story = generate_story_with_ai(summary_data)

    # Write story to README.md
    print("Writing results to README.md...")
    readme_content = f"# Analysis Report for {base_name}\n\n"
    readme_content += f"## Descriptive Statistics\n"
    readme_content += f"The descriptive statistics for the dataset have been saved in `analysis.csv`.\n\n"
    readme_content += f"## Missing Values\n"
    readme_content += f"The count of missing values for each column has been saved in `missing_values.csv`.\n\n"
    readme_content += f"## Charts\n"
    readme_content += f"- Histograms for numerical columns have been saved as separate files.\n"
    if len(num_cols) > 1:
        readme_content += f"- A pair plot of numerical columns has been saved as `pairplot.png`.\n"
        readme_content += f"- A correlation matrix heatmap has been saved as `correlation_matrix.png`.\n\n"
    readme_content += f"## Example Values for Categorical Columns\n"
    for col, examples in example_values.items():
        readme_content += f"### {col}:\n"
        for value, count in examples.items():
            readme_content += f"- {value}: {count} occurrences\n"
    readme_content += f"\n## AI-Generated Insights\n"
    readme_content += f"{story}\n"

    with open(output_dir / "README.md", "w") as readme_file:
        readme_file.write(readme_content)

    print(f"Analysis for {base_name} completed. Results saved in the '{output_dir}' folder.")

# If running as a standalone script, accept the CSV file path as input
if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: uv run autolysis.py <csv_file_path>")
    else:
        analyze_csv(sys.argv[1])


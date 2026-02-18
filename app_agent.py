"""Simple agent integration script for local testing (non-UI)

Creates a Vishleshak agent from CSV `sample_data.csv` and runs a sample query.
"""
import pandas as pd
from agentic_core import create_vishleshak_agent
from tools.specialized import (
    StatisticalAnalyzerTool,
    CorrelationFinderTool,
    AnomalyDetectorTool,
    ChartGeneratorTool,
    TrendAnalyzerTool,
    ForecasterTool,
    PythonSandboxTool,
    ReportGeneratorTool,
)


def main():
    df = pd.read_csv("sample_data.csv")
    tools = [
        StatisticalAnalyzerTool(df),
        CorrelationFinderTool(df),
        AnomalyDetectorTool(df),
        ChartGeneratorTool(df),
        TrendAnalyzerTool(df),
        ForecasterTool(df),
        PythonSandboxTool(),
        ReportGeneratorTool(df),
    ]

    agent = create_vishleshak_agent(tools=tools, data_context=f"Dataset: {len(df)} rows × {len(df.columns)} columns")
    q = "What are the key correlations and any anomalies in this data?"
    res = agent.run(q)
    print("Answer:\n", res.get('answer'))
    print("Confidence:", res.get('confidence'))
    print("Tools used:", res.get('tools_used'))


if __name__ == '__main__':
    main()

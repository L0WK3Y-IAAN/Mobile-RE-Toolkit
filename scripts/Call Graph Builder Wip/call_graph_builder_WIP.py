#!/usr/bin/env python3
import networkx as nx
from androguard.misc import AnalyzeAPK
from androguard.core.analysis.analysis import MethodClassAnalysis

def build_callgraph(apk_path, output_gexf):
    # Analyze the APK with Androguard
    a, d, dx = AnalyzeAPK(apk_path)

    # Create a directed graph in NetworkX
    G = nx.DiGraph()

    # Iterate over all methods known to the analysis
    for method_analysis in dx.get_methods():
        # 'method_analysis.method' is a DalvikMethod object
        caller_name = str(method_analysis.method)

        # Add the caller as a node (in case it has no outgoing edges)
        G.add_node(caller_name)

        # For each cross-reference to other methods
        for _, callee_method, _ in method_analysis.get_xref_to():
            callee_name = str(callee_method)
            G.add_node(callee_name)
            G.add_edge(caller_name, callee_name)

    # Write out the graph in GEXF format
    nx.write_gexf(G, output_gexf)
    print(f"[+] Call graph saved as {output_gexf}")

if __name__ == "__main__":
    apk_path = "my_app.apk"      # Replace with your APK path
    output_gexf = "callgraph.gexf"
    build_callgraph(apk_path, output_gexf)

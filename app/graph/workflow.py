"""
Builds and compiles the LangGraph state graph: wires the 8 nodes
together in order (classify -> context -> retrieve -> business_data
-> route -> generate -> verify -> decide) and exposes run_graph().
"""

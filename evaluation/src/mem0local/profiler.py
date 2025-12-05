import time

class KuzuQueryProfiler:
    def __init__(self, graph):
        self.graph = graph
    
    def timed_query(self, query, params=None):
        start = time.perf_counter()
        results = self.graph.kuzu_execute(query, params)
        elapsed = time.perf_counter() - start
        return results, elapsed

    def profile_query(self, query, params=None):
        start = time.perf_counter()
        results = self.graph.kuzu_execute(f"PROFILE {query}", params)
        elapsed = time.perf_counter() - start
        return results, elapsed

    def table_query(self):
        results = self.graph.kuzu_execute("""
            MATCH (n:Entity)
            RETURN n.user_id, COUNT(n) as count
            ORDER BY count DESC
        """)
        return results

    def get_stats(self):
        nodes, t1 = self.timed_query("MATCH (n) RETURN COUNT(n) as count")
        edges, t2 = self.timed_query("MATCH ()-[e]->() RETURN COUNT(e) as count")
        print("Kuzu Tables:", self.table_query())
        return {
            "node_count": nodes[0]['count'],
            "edge_count": edges[0]['count'],
            "node_query_time": t1,
            "edge_query_time": t2,
        }
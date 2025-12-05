import os
import time
from mem0 import Memory
import logging
import httpx
from qdrant_client import QdrantClient
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

os.environ["OPENROUTER_API_KEY"] = "sk-or-v1-xxxxxxxxxxxxxxxxxxxxxxxxxxxx"
os.environ["OPENAI_API_KEY"] = os.environ["OPENROUTER_API_KEY"]
os.environ["OPENAI_API_BASE"] = "https://openrouter.ai/api/v1"

config = {
    "vector_store": {
        "provider": "qdrant",
        "config": {
            "host": "localhost",
            "port": 6333,
        },
    },
    "graph_store": {
        "provider": "kuzu",
        "config": {
            "db": "./mem0-example.kuzu",
        },
    },
    "llm": {
        "provider": "openai",
        "config": {
            "model": "x-ai/grok-4.1-fast:free",
            "temperature": 0.2,
        },
    },
    "embedder": {
        "provider": "openai",
        "config": {
            "model": "qwen/qwen3-embedding-8b",
        },
    },
}

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

if __name__ == "__main__":
    m = Memory.from_config(config)
    # logger.info("Memory instance created from config file.")
    # messages = [
    #     {"role": "user", "content": "Hi, I'm Alex. I love basketball and gaming."},
    #     {"role": "assistant", "content": "Hey Alex! I'll remember your interests."}
    # ]
    # m.add(messages, user_id="alex")



    # qdrant_ = QdrantClient("localhost", port=6333)
    # telemetry_data = httpx.get("http://localhost:6333/telemetry?anonymize=false&details_level=6").json()
    # print(telemetry_data)

    # metrics = qdrant_.http.service_api.metrics()
    metrics_text = httpx.get("http://localhost:6333/metrics").text
    
    target_metrics = [
        "memory_active_bytes",
        "collections_vector_total",
        "collections_total",
        "collection_points",
        "collection_vectors",
        "collections_vector_total",
        "rest_responses_total",
        "rest_responses_avg_duration_seconds",
        "grpc_responses_total"
        "collection_hardware_metric_cpu",
        "collection_hardware_metric_payload_io_read",
        "collection_hardware_metric_payload_io_write",
        "collection_hardware_metric_payload_index_io_read",
        "collection_hardware_metric_payload_index_io_write",
        "collection_hardware_metric_vector_io_read",
        "collection_hardware_metric_vector_io_write",
    ]
    
    print("--- Extracted Metrics ---")
    for line in metrics_text.splitlines():
        if line.startswith("#"):
            continue
        for target in target_metrics:
            if line.startswith(target):
                print(line)

    profiler = KuzuQueryProfiler(m.graph)
    stats = profiler.get_stats()
    print(stats)
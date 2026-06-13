from typing import Literal

GRAPH_VERSION = "pathai.graph.v1"
DEFAULT_MAX_REVISIONS = 3
MAX_GRAPH_STEPS = 32

NodeName = Literal[
    "start_node",
    "assessor_node",
    "curriculum_node",
    "resource_node",
    "critic_node",
    "persist_node",
    "notify_node",
    "failure_node",
]

StageName = Literal[
    "created",
    "started",
    "assessing",
    "generating_curriculum",
    "attaching_resources",
    "reviewing",
    "persisting",
    "notifying",
    "completed",
    "failed",
]

JobStatus = Literal["queued", "running", "completed", "failed", "failed_persist"]
TraceStatus = Literal["started", "completed", "failed"]
CriticDecision = Literal["approved", "revise", "auto_approved"]
ResourceRefreshScope = Literal["all", "affected_only"]

START_NODE: NodeName = "start_node"
ASSESSOR_NODE: NodeName = "assessor_node"
CURRICULUM_NODE: NodeName = "curriculum_node"
RESOURCE_NODE: NodeName = "resource_node"
CRITIC_NODE: NodeName = "critic_node"
PERSIST_NODE: NodeName = "persist_node"
NOTIFY_NODE: NodeName = "notify_node"
FAILURE_NODE: NodeName = "failure_node"
END_NODE = "END"

GRAPH_NODES: list[NodeName] = [
    START_NODE,
    ASSESSOR_NODE,
    CURRICULUM_NODE,
    RESOURCE_NODE,
    CRITIC_NODE,
    PERSIST_NODE,
    NOTIFY_NODE,
    FAILURE_NODE,
]

GRAPH_EDGES: list[dict[str, str]] = [
    {"from": "START", "to": START_NODE, "condition": "every run"},
    {"from": START_NODE, "to": ASSESSOR_NODE, "condition": "no error"},
    {"from": ASSESSOR_NODE, "to": CURRICULUM_NODE, "condition": "knowledge map created"},
    {"from": CURRICULUM_NODE, "to": RESOURCE_NODE, "condition": "curriculum draft exists"},
    {"from": RESOURCE_NODE, "to": CRITIC_NODE, "condition": "resources attached"},
    {"from": CRITIC_NODE, "to": CURRICULUM_NODE, "condition": "revise and below max revisions"},
    {"from": CRITIC_NODE, "to": PERSIST_NODE, "condition": "approved or max revisions reached"},
    {"from": PERSIST_NODE, "to": NOTIFY_NODE, "condition": "persist placeholder completed"},
    {"from": NOTIFY_NODE, "to": END_NODE, "condition": "notification placeholder completed"},
    {"from": "any node", "to": FAILURE_NODE, "condition": "state contains an error"},
    {"from": FAILURE_NODE, "to": END_NODE, "condition": "failure converted to user-safe state"},
]

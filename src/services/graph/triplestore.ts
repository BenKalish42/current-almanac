/**
 * Master Knowledge Graph — local triplestore.
 *
 * Backend abstraction: in v1 RC1 the storage is in-memory + localStorage;
 * Dexie / Capacitor SQLite slot in by replacing the `Storage` interface
 * (see `src/services/db/index.ts` once Stream 5 storage layer lands).
 *
 * NEVER call the network from this module. Sovereignty rule.
 */

import type {
  EdgeProperties,
  EdgeType,
  GraphEdge,
  GraphNode,
  NodeLabel,
  NodeProperties,
} from "./types";

// -----------------------------------------------------------------------------
// Storage interface — swap-in slot for Dexie / SQLite later
// -----------------------------------------------------------------------------

export interface TriplestoreStorage {
  load(): { nodes: GraphNode[]; edges: GraphEdge[] };
  save(nodes: GraphNode[], edges: GraphEdge[]): void;
  clear(): void;
}

const LS_NODES = "current.graph.nodes.v1";
const LS_EDGES = "current.graph.edges.v1";

class LocalStorageBackend implements TriplestoreStorage {
  load(): { nodes: GraphNode[]; edges: GraphEdge[] } {
    if (typeof localStorage === "undefined") return { nodes: [], edges: [] };
    try {
      const n = JSON.parse(localStorage.getItem(LS_NODES) || "[]") as GraphNode[];
      const e = JSON.parse(localStorage.getItem(LS_EDGES) || "[]") as GraphEdge[];
      return { nodes: Array.isArray(n) ? n : [], edges: Array.isArray(e) ? e : [] };
    } catch {
      return { nodes: [], edges: [] };
    }
  }
  save(nodes: GraphNode[], edges: GraphEdge[]): void {
    if (typeof localStorage === "undefined") return;
    try {
      localStorage.setItem(LS_NODES, JSON.stringify(nodes));
      localStorage.setItem(LS_EDGES, JSON.stringify(edges));
    } catch {
      // ignore quota / private browsing
    }
  }
  clear(): void {
    if (typeof localStorage === "undefined") return;
    try {
      localStorage.removeItem(LS_NODES);
      localStorage.removeItem(LS_EDGES);
    } catch {
      // ignore
    }
  }
}

class MemoryBackend implements TriplestoreStorage {
  private n: GraphNode[] = [];
  private e: GraphEdge[] = [];
  load() { return { nodes: [...this.n], edges: [...this.e] }; }
  save(nodes: GraphNode[], edges: GraphEdge[]): void {
    this.n = [...nodes];
    this.e = [...edges];
  }
  clear(): void {
    this.n = [];
    this.e = [];
  }
}

// -----------------------------------------------------------------------------
// Triplestore
// -----------------------------------------------------------------------------

function uid() {
  return `${Date.now().toString(36)}-${Math.random().toString(36).slice(2, 10)}`;
}

export class Triplestore {
  private nodes: Map<string, GraphNode> = new Map();
  private edges: Map<string, GraphEdge> = new Map();
  // Indexes
  private nodesByLabel: Map<NodeLabel, Set<string>> = new Map();
  private edgesByType: Map<EdgeType, Set<string>> = new Map();
  private outEdges: Map<string, Set<string>> = new Map();
  private inEdges: Map<string, Set<string>> = new Map();

  private storage: TriplestoreStorage;

  constructor(storage: TriplestoreStorage = new LocalStorageBackend()) {
    this.storage = storage;
    this.hydrate();
  }

  private hydrate() {
    const { nodes, edges } = this.storage.load();
    for (const n of nodes) this.indexNode(n);
    for (const e of edges) this.indexEdge(e);
  }

  private persist() {
    this.storage.save([...this.nodes.values()], [...this.edges.values()]);
  }

  private indexNode(n: GraphNode) {
    this.nodes.set(n.id, n);
    if (!this.nodesByLabel.has(n.label)) this.nodesByLabel.set(n.label, new Set());
    this.nodesByLabel.get(n.label)!.add(n.id);
  }

  private indexEdge(e: GraphEdge) {
    this.edges.set(e.id, e);
    if (!this.edgesByType.has(e.type)) this.edgesByType.set(e.type, new Set());
    this.edgesByType.get(e.type)!.add(e.id);
    if (!this.outEdges.has(e.sourceId)) this.outEdges.set(e.sourceId, new Set());
    this.outEdges.get(e.sourceId)!.add(e.id);
    if (!this.inEdges.has(e.targetId)) this.inEdges.set(e.targetId, new Set());
    this.inEdges.get(e.targetId)!.add(e.id);
  }

  // ---- CRUD ----

  upsertNode(label: NodeLabel, properties: NodeProperties, id?: string): GraphNode {
    const node: GraphNode = { id: id ?? uid(), label, properties };
    this.indexNode(node);
    this.persist();
    return node;
  }

  upsertEdge(
    type: EdgeType,
    sourceId: string,
    targetId: string,
    properties: EdgeProperties = {},
    id?: string
  ): GraphEdge {
    if (!this.nodes.has(sourceId)) {
      throw new Error(`Triplestore: source node not found: ${sourceId}`);
    }
    if (!this.nodes.has(targetId)) {
      throw new Error(`Triplestore: target node not found: ${targetId}`);
    }
    const edge: GraphEdge = { id: id ?? uid(), type, sourceId, targetId, properties };
    this.indexEdge(edge);
    this.persist();
    return edge;
  }

  // ---- Query ----

  getNode(id: string): GraphNode | undefined {
    return this.nodes.get(id);
  }

  nodesWithLabel(label: NodeLabel): GraphNode[] {
    const ids = this.nodesByLabel.get(label) ?? new Set();
    return [...ids].map((id) => this.nodes.get(id)!).filter(Boolean);
  }

  edgesOfType(type: EdgeType): GraphEdge[] {
    const ids = this.edgesByType.get(type) ?? new Set();
    return [...ids].map((id) => this.edges.get(id)!).filter(Boolean);
  }

  outgoing(nodeId: string, type?: EdgeType): GraphEdge[] {
    const ids = this.outEdges.get(nodeId) ?? new Set();
    const out = [...ids].map((id) => this.edges.get(id)!).filter(Boolean);
    return type ? out.filter((e) => e.type === type) : out;
  }

  incoming(nodeId: string, type?: EdgeType): GraphEdge[] {
    const ids = this.inEdges.get(nodeId) ?? new Set();
    const out = [...ids].map((id) => this.edges.get(id)!).filter(Boolean);
    return type ? out.filter((e) => e.type === type) : out;
  }

  /** Followers of `nodeId` along `type` — returns target nodes. */
  follow(nodeId: string, type: EdgeType): GraphNode[] {
    return this.outgoing(nodeId, type)
      .map((e) => this.nodes.get(e.targetId))
      .filter((n): n is GraphNode => Boolean(n));
  }

  /** Reverse: nodes pointing AT `nodeId` via `type`. */
  inverseFollow(nodeId: string, type: EdgeType): GraphNode[] {
    return this.incoming(nodeId, type)
      .map((e) => this.nodes.get(e.sourceId))
      .filter((n): n is GraphNode => Boolean(n));
  }

  // ---- Bulk / utility ----

  size(): { nodes: number; edges: number } {
    return { nodes: this.nodes.size, edges: this.edges.size };
  }

  clear(): void {
    this.nodes.clear();
    this.edges.clear();
    this.nodesByLabel.clear();
    this.edgesByType.clear();
    this.outEdges.clear();
    this.inEdges.clear();
    this.storage.clear();
  }

  /** For tests + RAG serialization — never used to round-trip the live store. */
  snapshot(): { nodes: GraphNode[]; edges: GraphEdge[] } {
    return {
      nodes: [...this.nodes.values()],
      edges: [...this.edges.values()],
    };
  }
}

// -----------------------------------------------------------------------------
// Default / test factories
// -----------------------------------------------------------------------------

let _default: Triplestore | null = null;

export function getTriplestore(): Triplestore {
  if (!_default) _default = new Triplestore();
  return _default;
}

export function createInMemoryTriplestore(): Triplestore {
  return new Triplestore(new MemoryBackend());
}

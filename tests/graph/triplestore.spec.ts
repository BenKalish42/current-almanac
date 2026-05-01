import { describe, it, expect, beforeEach } from "vitest";
import { createInMemoryTriplestore, Triplestore } from "@/services/graph/triplestore";

describe("Triplestore — CRUD + indexing", () => {
  let store: Triplestore;
  beforeEach(() => {
    store = createInMemoryTriplestore();
  });

  it("upserts nodes and retrieves by label", () => {
    const a = store.upsertNode("Botanical", { tcm_name: "Ren Shen" });
    const b = store.upsertNode("Botanical", { tcm_name: "Gan Cao" });
    const f = store.upsertNode("Formula", { name: "Si Jun Zi Tang" });

    const botanicals = store.nodesWithLabel("Botanical");
    expect(botanicals).toHaveLength(2);
    expect(store.nodesWithLabel("Formula")).toHaveLength(1);
    expect(store.getNode(a.id)?.properties.tcm_name).toBe("Ren Shen");
    expect(store.getNode(b.id)?.properties.tcm_name).toBe("Gan Cao");
    expect(store.getNode(f.id)?.label).toBe("Formula");
  });

  it("upserts edges, indexes outgoing/incoming, and follows", () => {
    const formula = store.upsertNode("Formula", { name: "Si Jun Zi Tang" });
    const ren = store.upsertNode("Botanical", { tcm_name: "Ren Shen" });
    const gan = store.upsertNode("Botanical", { tcm_name: "Gan Cao" });

    store.upsertEdge("CONTAINS_HERB", formula.id, ren.id, { role: "King" });
    store.upsertEdge("CONTAINS_HERB", formula.id, gan.id, { role: "Courier" });

    const herbs = store.follow(formula.id, "CONTAINS_HERB");
    expect(herbs.map((h) => h.properties.tcm_name).sort()).toEqual(["Gan Cao", "Ren Shen"]);

    const formulas = store.inverseFollow(ren.id, "CONTAINS_HERB");
    expect(formulas.map((f) => f.properties.name)).toEqual(["Si Jun Zi Tang"]);
  });

  it("rejects edges to missing nodes", () => {
    const a = store.upsertNode("Pathology", { nature: "Heat" });
    expect(() => store.upsertEdge("AFFECTS", a.id, "no-such-id")).toThrow(
      /target node not found/
    );
    expect(() => store.upsertEdge("AFFECTS", "ghost", a.id)).toThrow(
      /source node not found/
    );
  });

  it("size() reflects current cardinalities", () => {
    expect(store.size()).toEqual({ nodes: 0, edges: 0 });
    const a = store.upsertNode("Pathology", { nature: "Damp" });
    const b = store.upsertNode("Botanical", { tcm_name: "Cang Zhu" });
    store.upsertEdge("TREATS", b.id, a.id);
    expect(store.size()).toEqual({ nodes: 2, edges: 1 });
  });

  it("clear() empties the store", () => {
    const n = store.upsertNode("Pathology", { nature: "Wind" });
    store.upsertEdge("AFFECTS", n.id, n.id);
    store.clear();
    expect(store.size()).toEqual({ nodes: 0, edges: 0 });
  });
});

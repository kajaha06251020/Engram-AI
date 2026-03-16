"use client";

import dynamic from "next/dynamic";
import { useApi } from "@/hooks/useApi";
import { GraphData } from "@/lib/types";
import { useCallback, useRef, useState } from "react";

const ForceGraph2D = dynamic(() => import("react-force-graph-2d"), {
  ssr: false,
});

function drawHexagon(ctx: CanvasRenderingContext2D, x: number, y: number, r: number) {
  ctx.beginPath();
  for (let i = 0; i < 6; i++) {
    const angle = (Math.PI / 3) * i - Math.PI / 6;
    const px = x + r * Math.cos(angle);
    const py = y + r * Math.sin(angle);
    if (i === 0) ctx.moveTo(px, py);
    else ctx.lineTo(px, py);
  }
  ctx.closePath();
}

export default function GraphPage() {
  const { data: graph, loading } = useApi<GraphData>("/api/graph");
  const fgRef = useRef<any>(null);
  const [highlightNodes, setHighlightNodes] = useState<Set<string>>(new Set());

  const graphData =
    graph && graph.nodes.length > 0
      ? {
          nodes: graph.nodes.map((n) => ({ ...n })),
          links: graph.edges.map((e) => ({
            source: e.source,
            target: e.target,
            type: e.type,
            weight: e.weight,
          })),
        }
      : { nodes: [], links: [] };

  const nodeLabel = useCallback((node: any) => {
    if (node.type === "skill")
      return `Skill: ${node.label}\nConfidence: ${((node.confidence ?? 0) * 100).toFixed(0)}%`;
    return `${node.label}\nValence: ${(node.valence ?? 0).toFixed(2)}`;
  }, []);

  const linkColor = useCallback(
    (link: any) => {
      const srcId = typeof link.source === "object" ? link.source.id : link.source;
      const tgtId = typeof link.target === "object" ? link.target.id : link.target;
      if (highlightNodes.size > 0 && (highlightNodes.has(srcId) || highlightNodes.has(tgtId))) {
        return link.type === "source" ? "rgba(129,140,248,0.7)" : "rgba(148,163,184,0.5)";
      }
      return link.type === "source"
        ? "rgba(129,140,248,0.3)"
        : "rgba(148,163,184,0.15)";
    },
    [highlightNodes]
  );

  const handleNodeClick = useCallback(
    (node: any) => {
      const connectedIds = new Set<string>();
      connectedIds.add(node.id);
      graphData.links.forEach((link: any) => {
        const srcId = typeof link.source === "object" ? link.source.id : link.source;
        const tgtId = typeof link.target === "object" ? link.target.id : link.target;
        if (srcId === node.id) connectedIds.add(tgtId);
        if (tgtId === node.id) connectedIds.add(srcId);
      });
      setHighlightNodes((prev) =>
        prev.has(node.id) ? new Set() : connectedIds
      );
    },
    [graphData.links]
  );

  if (loading) {
    return (
      <div className="flex items-center justify-center h-[calc(100vh-120px)] text-gray-500">
        Loading graph...
      </div>
    );
  }

  if (!graph || graph.nodes.length === 0) {
    return (
      <div className="flex items-center justify-center h-[calc(100vh-120px)] text-gray-500">
        No data to visualize.
      </div>
    );
  }

  return (
    <div
      className="rounded-xl bg-engram-card border border-engram-border overflow-hidden"
      style={{ height: "calc(100vh - 120px)" }}
    >
      <ForceGraph2D
        ref={fgRef}
        graphData={graphData}
        nodeLabel={nodeLabel}
        linkColor={linkColor}
        linkWidth={(link: any) => (link.type === "source" ? 1.5 : 0.5)}
        backgroundColor="#0f0f23"
        onNodeClick={handleNodeClick}
        onBackgroundClick={() => setHighlightNodes(new Set())}
        nodeCanvasObject={(node: any, ctx: CanvasRenderingContext2D, globalScale: number) => {
          const isHighlighted = highlightNodes.size === 0 || highlightNodes.has(node.id);
          const alpha = isHighlighted ? 0.9 : 0.2;

          if (node.type === "skill") {
            const r = 4 + (node.confidence ?? 0.5) * 4;
            drawHexagon(ctx, node.x!, node.y!, r);
            ctx.fillStyle = `rgba(251,191,36,${alpha})`;
            ctx.fill();
            ctx.strokeStyle = `rgba(251,191,36,${Math.min(alpha + 0.2, 1)})`;
            ctx.lineWidth = 0.5;
            ctx.stroke();
          } else {
            const r = 2 + Math.abs(node.valence ?? 0) * 4;
            ctx.beginPath();
            ctx.arc(node.x!, node.y!, r, 0, 2 * Math.PI);
            const color = (node.valence ?? 0) >= 0 ? "52,211,153" : "248,113,113";
            ctx.fillStyle = `rgba(${color},${alpha})`;
            ctx.fill();
          }
        }}
        nodePointerAreaPaint={(node: any, color: string, ctx: CanvasRenderingContext2D) => {
          const r = node.type === "skill" ? 8 : 6;
          ctx.beginPath();
          ctx.arc(node.x!, node.y!, r, 0, 2 * Math.PI);
          ctx.fillStyle = color;
          ctx.fill();
        }}
        warmupTicks={50}
        cooldownTicks={100}
      />
    </div>
  );
}

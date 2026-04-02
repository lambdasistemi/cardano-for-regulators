import mermaid from "https://unpkg.com/mermaid@10.4.0/dist/mermaid.esm.min.mjs";

mermaid.initialize({
  startOnLoad: false,
  securityLevel: "loose",
  theme: "dark",
});

await mermaid.run({ querySelector: ".mermaid" });

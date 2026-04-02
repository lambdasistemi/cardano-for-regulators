import mermaid from "https://cdn.jsdelivr.net/npm/mermaid@11/dist/mermaid.esm.min.mjs";

document$.subscribe(async () => {
  mermaid.initialize({
    startOnLoad: false,
    securityLevel: "loose",
  });
  await mermaid.run({ querySelector: ".mermaid" });
});

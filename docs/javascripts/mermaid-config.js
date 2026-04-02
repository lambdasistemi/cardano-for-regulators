// Patch mermaid config after mermaid2 plugin sets it
// mermaid2 overwrites window.mermaidConfig, so we intercept via defineProperty
Object.defineProperty(window, "mermaidConfig", {
  set(val) {
    if (val && val.default) {
      val.default.securityLevel = "loose";
    }
    this._mermaidConfig = val;
  },
  get() {
    return this._mermaidConfig;
  },
  configurable: true
});

/**
 * Client-Side Game Mode & Renderer Registry.
 * Allows game modes to be registered dynamically as independent plugins.
 */
window.GameRegistry = (() => {
  const modes = new Map();

  const registry = {
    register(id, definition) {
      modes.set(id, definition);
    },
    get(id) {
      return modes.get(id);
    },
    has(id) {
      return modes.has(id);
    },
    list() {
      return Array.from(modes.keys());
    },
    render(id, data, context) {
      const mode = modes.get(id);
      if (mode && typeof mode.render === 'function') {
        mode.render(data, context);
        return true;
      }
      return false;
    }
  };

  window.GameRendererRegistry = registry;
  return registry;
})();

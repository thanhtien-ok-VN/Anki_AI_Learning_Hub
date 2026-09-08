/**
 * Core Application State for Anki AI Learning Hub.
 */
window.HubState = (() => {
  const state = {
    route: 'home',
    decks: [],
    pairs: [],
    seen: new Set(),
    exercise: null,
    index: 0,
    answers: {},
    busy: false,
    history: {},
    userPrefs: {},
    matchingStats: null,
    supportedLanguages: [],
    uiLanguages: ['en', 'vi'],
    isGraded: false,
    deckConfig: {
      deckId: null,
      modelId: null,
      termField: null,
      definitionField: null,
      sampleLimit: 20
    }
  };

  return state;
})();

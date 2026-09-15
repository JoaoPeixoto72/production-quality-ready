# Search

Search is often the fastest path to content. A poor search experience is one of the most common reasons users churn from content-heavy apps.

## Checklist

| Item | Guidance |
|---|---|
| Discoverability | Search bar on the home screen or one tap away. Never buried in a menu. |
| Recent searches | Last 5–10 saved. Individually deletable. |
| Suggestions | Autocomplete after 1–2 keystrokes. Debounced ~300ms. |
| Filter and sort | Filter chips above results. Active filter count in a badge. All filters clearable in one tap. |
| Search scope indicator | UI shows what is being searched (e.g. "Searching in Orders"). |
| Empty-results state | "No results for X" with spelling suggestion and related categories. Empty-state anatomy in `./error-handling.md`. |
| Voice search | Microphone icon in the bar (see `./multimodal-input.md`). |
| Typo tolerance | Fuzzy matching handles common misspellings. |
| Blank-state suggestions | With empty bar, show trending or personalized suggestions. |

## Patterns

- **Progressive disclosure.** Show top 3 inline with "See all" instead of full-page results for every query.
- **Federated search.** Group by content type (People / Products / Documents) with clear section headers.
- **Zero-result analytics.** Every zero-result query is a content-gap or labeling signal — track them.

## Anti-patterns

- A search box behind a hamburger menu on a content-heavy app.
- No spelling suggestion in the empty-results state.
- Filter chips with no visible active-count indicator.
- Search returning "No results" in a filtered context without telling the user which filter is active.

## Related

- `./information-architecture.md` — labels and categorization that make search findable.
- `./error-handling.md` — empty-state standards.
- `./ai-automation.md` — semantic search and natural-language queries.
- `./multimodal-input.md` — voice and image search input.

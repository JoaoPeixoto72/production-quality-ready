# Network and Connectivity

Network conditions are unpredictable. An app that only works on fast Wi-Fi is not a reliable product. Design for the worst connection and fast connections take care of themselves.

## Checklist

| Item | Guidance |
|---|---|
| Slow-connection resilience | Critical content loads first. Images lazy-load. Payloads compressed. |
| No-internet state | Inline message + Retry. Never an empty screen with no explanation. |
| Network switch resilience | Wi-Fi ↔ mobile switch doesn't crash or disconnect. |
| Offline mode | Cached content displayed. Writes queued and flushed when connection returns. |
| Background sync | Syncs on Wi-Fi by default. User can enable on mobile data. |
| Optimistic UI | Update the UI immediately, sync in background, show undo on failure. |
| Skeleton screens over spinners | For content-heavy loads beyond 400ms. |

## Cache strategies

| Strategy | Best for |
|---|---|
| Stale-while-revalidate | Feeds, dashboards — show cached, refresh in background |
| Cache-first | Read-heavy content the user manually pulls to refresh |
| Network-first | Freshness-sensitive content with cache as fallback on error |

## Error patterns

| Scenario | UI |
|---|---|
| No internet at launch | Full-screen message + Retry |
| Lost internet mid-use | Top banner: "No connection — working offline" |
| Slow connection | Skeleton screens, not spinners |
| Server 5xx | Human message + Retry |
| Request timeout | "Taking longer than usual" + Keep waiting / Cancel |
| Partial failure | Load what worked, inline error for what didn't |

## Performance targets

**Web — Core Web Vitals**

| Metric | Target |
|---|---|
| LCP (Largest Contentful Paint) | < 2.5s |
| INP (Interaction to Next Paint) | < 200ms |
| CLS (Cumulative Layout Shift) | < 0.1 |

**Mobile app**

| Metric | Target |
|---|---|
| Cold start to interactive | < 2s |
| API response (P95) | < 500ms |
| Offline cache hit | < 100ms |
| Scrolling | No dropped frames at display refresh rate |

## Anti-patterns

- Spinners for anything over ~1s of content load.
- Silent write failures.
- "Retry" that isn't idempotent — creates duplicates on flaky networks.
- Layout shift as the network arrives (fails CLS and feels broken).

## Related

- `./error-handling.md` — error message writing and retry patterns.
- `./help-onboarding.md` — loading indicators and skeleton screens.
- `./ai-agent.md` — long-running tasks that survive a page reload.
- `../agent/tool-strategy.md` — running the accessibility / performance tool to verify a network claim.

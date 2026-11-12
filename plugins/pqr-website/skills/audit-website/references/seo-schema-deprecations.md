# Schema.org — Deprecations relevant for SERP

- **HowTo** — Google removed the rich result in September 2023. Do not recommend adding new `HowTo` for SERP benefit. Do not auto-strip existing usage.
- **FAQPage** — Google retired FAQ rich results for all sites on 7 May 2026. Do not recommend adding new `FAQPage` for SERP benefit. Do not recommend removing existing usage — the markup remains valid Schema.org, and some AI surfaces may still consume it (unverified).

## Types the skill checks by default
- `Organization`
- `WebSite` and `SearchAction`
- `BreadcrumbList`
- `Article` / `NewsArticle` / `BlogPosting`
- `Product` (with `Offer` / `AggregateRating` / `Review`)
- `LocalBusiness` (and subtypes)
- `Event`
- `Recipe`
- `VideoObject`

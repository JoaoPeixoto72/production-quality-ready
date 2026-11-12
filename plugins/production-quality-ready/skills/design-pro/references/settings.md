# Settings

Settings is where users go when the defaults do not fit their life. A well-designed settings screen increases retention. An overwhelming one drives frustration.

## Checklist

| Item | Guidance |
|---|---|
| Grouped by theme | Account / Notifications / Appearance / Privacy / Storage / About / Danger zone. |
| Theme switching | System (auto) / Light / Dark, three-way segmented control. |
| Font size | Respects OS setting by default. Offers in-app override for a11y. |
| In-app language | Change language from within Settings, independent of OS language. |
| Per-type notification toggles | Not a single on/off. See `./notifications.md`. |
| Data-usage controls | Auto-download on Wi-Fi only by default. Media quality selectable. |
| Clear cache | Cache clearable in-app with storage usage visible. |
| No nav duplication | Settings is not a mirror of main nav. |
| Search in settings | Search bar in Settings with 20+ items. |
| Destructive actions at the bottom | Delete account / Sign out at the end of the list. |
| Immediate save | Settings apply instantly unless the change requires a form (e.g. change email). |
| Live preview for visual settings | Theme / font size preview without leaving Settings. |

## Standard settings tree

```
Settings
├── Account / Profile
│   ├── Edit profile
│   ├── Change email or phone
│   └── Password and security
├── Notifications
│   ├── [Type 1] on/off
│   ├── [Type 2] on/off
│   └── Notification schedule
├── Appearance
│   ├── Theme (System / Light / Dark)
│   ├── Font size
│   └── Language
├── Privacy
│   ├── Data and permissions
│   ├── Download my data
│   └── Connected apps
├── Storage
│   ├── Storage usage
│   └── Clear cache
├── About
│   ├── Version number
│   ├── Privacy policy
│   ├── Terms of service
│   └── Open-source licenses
└── Danger zone
    ├── Sign out
    └── Delete account
```

## Platform conventions

- **iOS.** Navigation list with `.insetGrouped`, disclosure chevrons.
- **Android.** `PreferenceFragmentCompat` with Material You styling.
- **Web.** Left sidebar for complex settings, tabs for simpler ones.

## Anti-patterns

- Save button on every toggle (immediate save is the norm).
- Destructive actions at the top of the list.
- Settings that mirror the main nav rather than complement it.
- Language toggle absent — many users have OS in one language and prefer the app in another.

## Related

- `./notifications.md` — per-type controls in depth.
- `./user-account.md` — account section content and deletion.
- `./general.md` — version number, dark-mode sync, OS-language sync.

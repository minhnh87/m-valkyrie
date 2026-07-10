# Omniheroes site · workflow

Một site duy nhất với tab navigation. Mỗi tab tương ứng với một tab trong Google
Sheets. Tất cả data + CSS + JS đều inline trong một file — chạy offline qua
`file://`, share bằng cách gửi file.

> **Single-file `index.html` từ 2026-06-24**: site là MỘT file duy nhất
> `index.html`, build từ `templates-mobile/` qua `scripts/build_mobile.py`
> (mobile-first). `mobile.html` đã bị bỏ hẳn. Legacy desktop `build_html.py` +
> `templates/` đã nghỉ hưu (vẫn nằm trên disk để tham khảo, không còn chạy). Khi
> thêm tab mới chỉ cần fragment trong `templates-mobile/` (xem `relics-priority`
> làm mẫu cho một page không-phải-hero: không avatar, không merge vào
> characters.json).

## Source

- Spreadsheet ID + tab list: [`data/sheets.json`](data/sheets.json)
- Page registry (tabs hiển thị + order): [`data/pages.json`](data/pages.json)
- Source URL: <https://docs.google.com/spreadsheets/d/1S6HcGV7DM9DDR7932bEF1yOCEA8yeMhBn7bnokxG6cU/>
- Hero images: scraped từ <https://omniheroesgame.fandom.com> (MediaWiki API, không cần token)
- Hero skills: scraped từ section "Hero Skills" của cùng Fandom wiki (rate-limit/403 nên scraper backoff + resume)

## Pipeline

```
Google Sheets ── fetch_sheet.sh ──► data/raw/<slug>.csv
                                       │
            ┌──────────────────────────┘
            ▼
fetch_images.py ──► data/images.json   (cache hero name → CDN URL, shared across pages)
            │
            ▼
build_<page>.py ──► data/<page>.json   (clean shape mỗi tab cần)
            │
data/character_skills.json             (bilingual EN/VI skill profiles — nguồn skill DUY NHẤT, hand/skill-curated)
            │
            ▼
build_characters.py ──► data/characters.json   (merge 5 sheets + images + skill profiles, 1 entry/hero)
            │
            ▼
build_mobile.py ─► index.html          (shell + page fragments + per-page JSON + characters JSON; from templates-mobile/)
```

`characters.json` là aggregate per-hero (avatar, tier ranks, rune note, rune
priority, skills) được nhúng global vào shell qua placeholder `__CHARACTERS_DATA__`.
Click hero ở **bất kỳ tab nào** đều mở chung một profile modal qua `Omni.openProfile(name)`.

## Update nhanh nhất

```sh
./scripts/update.sh                 # tất cả page + characters + assemble index.html
./scripts/update.sh tier-list       # chỉ rebuild data tier-list, vẫn merge + assemble lại index
./scripts/update.sh --no-images     # bỏ qua bước query Fandom cho ảnh (đỡ tốn API)
```

Sau khi chạy, mở `index.html` bằng browser (file:// cũng được — data nằm trong cùng file).

> **Skills = 1 nguồn duy nhất**: skill của hero nằm trong `data/character_skills.json`
> (song ngữ EN/VI, curate tay/từ screenshot). Không còn scrape Fandom. `build_characters.py`
> merge file này thành `skill_profile` mỗi hero (hero chưa có → section "Skills" rỗng).
> Thêm skill cho hero mới: dùng skill `hero-skill-extract`.

## Architecture

### Shell (`templates/index.template.html`)

- Tab bar sticky ở top, nav giữa các page
- Sections chứa từng page fragment (chỉ active section là visible, rest có `hidden`)
- Shared CSS: theme vars, page-header, controls bar, search box, segmented control,
  modal — đừng redefine trong fragment
- Tab router:
  - URL hash format: `#page=<slug>&<page-specific params>`
  - Click tab → clears non-page params, dispatch `omni:tab-active` event
  - Deep-link `#page=<slug>&...` → giữ nguyên params, dispatch tab-active
  - Back/forward (hashchange) → activate đúng tab + giữ params
- Window API `Omni`: pages dùng để integrate với shell
  - `Omni.getActivePage()`, `Omni.readPageHash()`, `Omni.writePageHash(slug, params)`
  - `Omni.openModal(html)`, `Omni.closeModal()`
  - `Omni.openProfile(name)` — mở shared character profile (resolve theo name/alias);
    page chỉ cần giữ `state.hero` + `syncHash` để reopen khi quay lại tab
  - `Omni.onTab(slug, handler)` — listen tab activation
  - `Omni.onModalClosed(handler)` — listen modal close

### Page fragments (`templates/_page_<slug>.html`)

Mỗi fragment gồm 2 phần được tách bằng `<!-- ::: PAGE SCRIPT ::: -->`:

1. **Markup half** (đi vào `__PAGE_FRAGMENTS__` trong `<main>`):
   - `<style>` với selectors prefix `.page-<slug>` (tránh collision)
   - `<section class="page page-<slug>" data-tab="<slug>" hidden>` chứa markup
   - `<script type="application/json" id="data-<slug>">__<PAGE>_DATA__</script>`
2. **Script half** (đi vào `__PAGE_SCRIPTS__` sau shell IIFE):
   - IIFE bắt đầu bằng `const SLUG`, `const ROOT`, `const DATA`
   - `Omni.onTab(SLUG, () => { init(); render(); ... })` để init lazy
   - IDs trong markup nên prefix (vd. `tl-q`, `bp-q`) để tránh collision khi
     gặp tabs khác cũng có search box

Convention:
- **Single-file**: data nhúng vào `<script type="application/json">`, runs offline + share via file://
- **Dark theme**: dùng nguyên CSS variables `--bg-0..3`, `--text*`, palette tier
  `--t-ss`, `--t-sp`, …, `--t-d`. Đừng định nghĩa màu mới ad-hoc.
- **CSS scoping**: in-page → `.page-<slug> ...`; nội dung trong shared modal →
  `.omni-modal-from-<slug> ...` (page IIFE add class này khi mở modal)
- **State qua URL hash**: `page=<slug>` là global, các params còn lại thuộc về page active
- **Image fallback**: dùng SVG/CSS initials với màu của tier hiện tại

## Khi nào phải làm gì

### Sheet update content (giá trị thay đổi, đổi note, thêm hero)

```sh
./scripts/update.sh <slug> --no-images
```

Pipeline tự đọc lại CSV + dùng cache ảnh cũ + assemble lại `index.html`.

### Thêm hero mới chưa có trong sheet trước đây

```sh
./scripts/update.sh <slug>       # bỏ --no-images để query wiki cho ảnh mới
```

Nếu hero chưa có ảnh trên wiki, hero hiển thị fallback initials. Chạy lại sau khi
wiki được cập nhật.

### Tên hero trong sheet ≠ tên trên wiki

Mở `scripts/fetch_images.py`, thêm vào dict `ALIASES`:
```python
ALIASES = {
    "King Arthur": "Arthur",
    "Tsukuyomi ": "Tsukuyomi",
    ...
}
```
Rồi chạy `python3 scripts/fetch_images.py --refresh`.

### Tên hero trong sheet `<X>` ≠ tên trong cache images cũ

Mở builder của page (`scripts/build_<slug>.py`), thêm vào dict `NAME_TO_IMAGE`:
```python
NAME_TO_IMAGE = {
    "Tsuki": "Tsukuyomi",
    "Jorm": "Jormungand",
    ...
}
```

### `build_characters.py` báo "unmatched source name" (build fail)

`build_characters.py` merge theo tên canonical của **Tier List** và **fail loud**:
nếu một sheet dùng tên viết tắt/typo không khớp hero canonical nào, build in ra
`unmatched_names` rồi exit non-zero (không âm thầm bỏ hero). Khi thêm hero mới có
shorthand mới, mở `scripts/build_characters.py` và thêm vào dict `ALIASES`
(source name → canonical Tier-List name):
```python
ALIASES = {
    "A. Bastet": "Ascended Bastett",   # "A." là Ascended hay Arcane tùy hero
    "A. Dorabella": "Arcane Dorabella",
    "Jorm": "Jormungand",
    ...
}
```
Rồi chạy lại `python3 scripts/build_characters.py`. Variant (Arcane/Ascended/
Primordial/Sovereign) là **character riêng** — không merge vào hero gốc.

### Thêm cột mới trong tier list (vd. có thêm boss / mode)

1. Mở `scripts/build_tier_list.py`, thêm entry vào `COLUMNS`:
   ```python
   {"key": "new_mode", "label": "New Mode", "group": "...", "subgroup": ""},
   ```
   thứ tự `COLUMNS` phải đúng thứ tự cột trong sheet.
2. Chạy lại pipeline.
3. Mode picker + table tự render thêm cột — không cần đụng HTML.

### Thêm một tab mới (vd. làm tab Rune Tier List)

1. Đảm bảo tab có mặt trong `data/sheets.json` với `slug` mới.
2. Tạo `scripts/build_<slug>.py` — copy `build_beginners_priority.py` (đơn giản hơn)
   hoặc `build_tier_list.py` rồi đổi:
   - đường dẫn `RAW_CSV`, `OUT`
   - parse logic phù hợp với layout sheet
   - convention: output JSON ở `data/<slug>.json`
3. Tạo `templates/_page_<slug>.html` — copy 1 fragment có sẵn rồi:
   - Đổi `.page-<slug>` trong toàn bộ CSS
   - Đổi `data-tab="<slug>"`, IDs prefix (vd. `rn-` cho rune)
   - Đổi placeholder `__<PAGE>_DATA__` (và script `data-<slug>`)
   - Đổi `SLUG`, `ROOT` selector trong IIFE
4. Đăng ký page trong `data/pages.json`:
   ```json
   {
     "slug": "rune-tier-list",
     "title": "Rune Tier List",
     "subtitle": "...",
     "fragment": "_page_rune-tier-list.html",
     "data": "rune-tier-list.json",
     "placeholder": "__RUNE_TIER_LIST_DATA__"
   }
   ```
5. Thêm case vào `scripts/update.sh`:
   ```bash
   ALL_PAGES=(tier-list beginners-priority rune-tier-list)
   ...
   build_rune_tier_list() {
     echo "▶ rune-tier-list: pulling CSV"
     ./scripts/fetch_sheet.sh rune-tier-list
     maybe_refresh_images
     echo "▶ rune-tier-list: building data JSON"
     python3 scripts/build_rune_tier_list.py
   }
   ...
   case "$t" in
     ...
     rune-tier-list) build_rune_tier_list ;;
   esac
   ```
6. `./scripts/update.sh rune-tier-list` — tab tự xuất hiện trong index.html.

## File map

```
m-valkyrie/
├── data/
│   ├── sheets.json          # spreadsheet ID + all 27 tab gids (master list)
│   ├── pages.json           # registered page tabs (drives index.html)
│   ├── raw/                 # CSV download (1 file / tab)
│   ├── images.json          # cache name → CDN URL + danh sách missing
│   ├── character_skills.json # bilingual EN/VI skill profiles (SOLE skill source)
│   ├── characters.json      # per-hero aggregate (drives the shared profile modal)
│   ├── tier-list.json       # clean data → consumed by _page_tier-list.html
│   └── beginners-priority.json
├── assets/
│   ├── heroes/              # mirrored hero avatars
│   ├── runes/               # inline rune images (fallback avatars)
│   └── skills/              # mirrored skill icons
├── scripts/
│   ├── fetch_sheet.sh       # CSV export ↳ data/raw/<slug>.csv
│   ├── fetch_images.py      # Fandom Heroes page → images.json
│   ├── build_tier_list.py
│   ├── build_beginners_priority.py
│   ├── build_characters.py  # merge all sheets + images + skill profiles → characters.json
│   ├── build_mobile.py      # assembles index.html from templates-mobile/ (the active build)
│   ├── build_html.py        # legacy desktop assembler (retired; not run)
│   └── update.sh            # one-shot orchestrator
├── templates/
│   ├── index.template.html  # shell: tab bar, shared CSS, tab router, modal, openProfile
│   ├── _page_tier-list.html
│   └── _page_beginners-priority.html
├── index.html               # built artifact (the only user-facing HTML)
└── WORKFLOW.md
```

## Troubleshooting

- **Hero ko hiện ảnh dù wiki đã có**: `python3 scripts/fetch_images.py --refresh`
- **Mọi avatar đều miss**: Fandom có thay đổi cấu trúc Heroes page —
  chỉnh regex trong `fetch_heroes_page_map()`.
- **Sheet bị set private**: `fetch_sheet.sh` sẽ trả HTTP 4xx. Cần "Anyone with the link"
  hoặc Drive API token.
- **Tier rating mới (vd. "SSS")**: thêm vào `TIER_ORDER` ở `build_tier_list.py`
  + thêm CSS variable `--t-xxx` trong `index.template.html` + map trong `TIER_BANDS` JS
  của `_page_tier-list.html`.
- **Một tab bị blank khi mở**: check console — thường do ID collision (2 fragment
  dùng cùng ID không prefix) hoặc CSS scope sai (`.page-<slug>` thiếu trước
  selector → conflict cross-tab).
- **Tab tự switch về tab đầu khi reload**: hash format wrong. Format đúng là
  `#page=<slug>&...`. Nếu hash có ký tự lạ, shell fallback về tab đầu.
- **`build_characters.py` exit non-zero**: có `unmatched_names` — thêm alias vào
  `ALIASES` trong `build_characters.py` (xem section bên trên) rồi chạy lại.
- **Hero mở profile nhưng section "Skills" rỗng**: hero đó chưa có entry trong
  `data/character_skills.json` → nằm trong `missing_skills`. Thêm skill bằng skill
  `hero-skill-extract` (từ screenshot in-game, song ngữ EN/VI) rồi rebuild.

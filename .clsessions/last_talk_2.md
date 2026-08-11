# Last Talk - m-valkyrie
Updated: 20260811_155935
Mode: bypassPermissions

---

## User

ĐỒng bộ lại content tab Relic (tab Priority) từ đây https://docs.google.com/spreadsheets/d/1S6HcGV7DM9DDR7932bEF1yOCEA8yeMhBn7bnokxG6cU/edit?gid=987620772#gid=987620772

---

## Claude

Đồng bộ xong. Đã chạy pipeline sẵn có: `./scripts/update.sh relics-priority` (pull CSV backup → tải lại `omni.xlsx` → extract icon relic → build `relics-priority.json` + `relics-tier.json` → merge characters → build `index.html`).

**Thay đổi nội dung từ sheet (gid 987620772 — khớp với `sheets.json`):**

| Relic | Thay đổi |
|---|---|
| **Crimson Chalice** | Trước là placeholder rỗng → nay có đủ: "Strong and cheap, gets better as you upgrade it.", nguồn Relic Rebate, mốc `2, 4, 6, 8` (đỏ: 8), focus `PvP > PvE` |
| **Divine Scepter** | Note đảo ngược hẳn: từ "một trong những relic tệ nhất" → "counters Lucifer, lấy 2★ hoặc 9★ để insta cast"; được đẩy từ mục *Extras/Rebates - PvP Road* lên *Rebates & Extra Sources* |
| **Lance** | Thêm nguồn "End of Season Shop" + ghi chú "Don't get it from here" cho Relic Rebate; nhảy lên đầu mục Rebates |
| **Crown of Purity** | Tụt xuống giữa mục *Extras/Rebates - PvP Road* |

Tổng vẫn 43 relic / 4 section, không có relic thêm hay bị xoá — chỉ đổi thứ tự và nội dung. Icon relic cũng được extract lại (55 icon).

**Một điểm cần bạn xác nhận:** `Crimson Chalice` vẫn không có icon (fallback chữ cái đầu) vì tab Relics Tier List không có tên này — gần nhất là **Crimson Crown** (`assets/relics/2f8c23659f81.png`). Note hai bên không giống nhau ("strong and cheap" vs "requires too much investment"), nên mình không tự map. Nếu đúng là một relic, mình thêm `ALIASES = {"Crimson Chalice": "Crimson Crown"}` trong `scripts/build_relics_priority.py:54` rồi build lại là có icon.

Lưu ý: diff `index.html` còn kèm phần sửa layout tab Tier List đang dở trong `templates-mobile/_page_tier-list.html` (đã có sẵn trước khi sync, build lại giữ nguyên).

Mở app:
```
open /Users/minh/www/git/personal/tools/m-valkyrie/index.html
```

---


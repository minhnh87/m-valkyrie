# Last Talk - m-valkyrie
Updated: 20260811_162730
Mode: bypassPermissions

---

## User

à khoan, đấy là 2 cái khác nhau đấy. Roll lại đoạn set alias đi. Còn icon của các relics hình như cũng là cut ra từ excel mà, làm tương tự với Crimson Chalice được không?

---

## Claude

Xong. Đã revert alias và lấy icon đúng cách.

**Việc đã làm:**
1. `git checkout` 2 builder → xoá sạch phần alias/rename (Crimson Crown giữ nguyên tên, 2 relic tách biệt như cũ).
2. Kiểm tra drawing anchors trong `omni.xlsx`: tab **Priority sau khi rebuild có 43 icon inline ở cột B** (Crimson Chalice ở row 20) — docstring cũ của `extract_relic_images.py` viết từ trước lúc rebuild nên nói tab này "không có icon per-relic", đã sai.
3. Sửa `scripts/extract_relic_images.py`: harvest từ cả 2 tab, Tier List trước rồi Priority điền chỗ thiếu; tên nào đã có thì bỏ qua **trước khi** ghi file nên không sinh PNG trùng.

**Kết quả:** `56 named relics, 56 unique icons — 55 from Relics Tier List, 1 from Relics Priority List`. Diff `relic_images.json` chỉ có đúng 1 dòng thêm (`Crimson Chalice`), 0 thay đổi, 0 xoá. Hai icon nhìn khác hẳn nhau (Chalice = chiếc bình đỏ, Crown = vương miện) → xác nhận thêm là 2 relic khác nhau.

Đã verify trên browser ở viewport 414×896: card **Crimson Chalice** hiện icon thật (86×86, load OK), mốc `2, 4, 6, ` với **8** đỏ, badge `PVP > PVE`, nguồn Relic Rebate. Không còn relic nào fallback chữ cái đầu.

**File đổi:** `scripts/extract_relic_images.py` (logic), `scripts/build_relics_priority.py` (chỉ comment — ghi rõ Chalice/Crown là 2 relic để lần sau không alias nhầm), `data/relic_images.json`, `data/relics-priority.json`, `data/relics-tier.json`, `index.html`, + `assets/relics/d9f7db7448a7.png` (mới).

**Edge case đáng lưu ý cho lần sync sau:**
- Relic có mặt ở cả 2 tab nhưng ảnh crop khác nhau → Tier List luôn thắng, không sinh file rác. ✅ đã test (54/55 tên bị skip ở tab Priority).
- Relic chỉ có ở tab Priority → nay lấy được icon. ✅
- Nếu tab Priority đổi cột tên khỏi C, hoặc mất drawing → script `raise SystemExit` rõ ràng chứ không âm thầm bỏ icon.
- Tên gần giống nhau (Crown of Purity / Crown of Schemes / Crimson Crown / Crimson Chalice): dòng in `without icon` giờ là tín hiệu đi tìm sheet, **không** phải tín hiệu để alias.

Mở app:
```
open /Users/minh/www/git/personal/tools/m-valkyrie/index.html
```

---


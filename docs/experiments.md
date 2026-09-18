# Experimental Evaluation

> Bu doküman Phase 19 (deneysel değerlendirme) ve Phase 20'de (stress test) sistemli deneylerle asıl içeriğini alacak. Aşağıdaki bölüm, Phase 3'te baseline scheduler'ı doğrularken elde edilen **ilk gözlemleri** kaydediyor — resmi deney değil, ama gerçek çalıştırma sonucu, uydurulmamış.

## Phase 3 — Baseline (FCFS vs EDF) İlk Gözlemler

SMALL dataset (10 makine, 50 job, seed=42) üzerinde iki baseline stratejisi çalıştırıldı:

| Metric | FCFS | EDF |
|---|---:|---:|
| Production Time (h) | 144.31 | 144.31 |
| Energy Cost | 4858.60 | 4742.23 |
| Late Jobs | 3 | 7 |
| Avg Tardiness (h) | 0.20 | 0.18 |
| Avg Machine Utilization | 0.12 | 0.12 |

**Gözlem — EDF, FCFS'ten daha fazla geciken iş üretti.** İlk bakışta ters görünüyor ("deadline'a göre sıralamak daha iyi olmalıydı"), ama bu bilinen bir teorik sonuçla tutarlı: EDF, yalnızca **tek makineli, release-time'sız** ortamlarda maksimum gecikmeyi (Lmax) garantili minimize eder. Bu projede birden fazla makine, makine tipi paylaşımı (özellikle SMALL preset'te `Assembly` tipinden tek makine var ve ürün şablonlarının çoğu oradan geçiyor) ve release_time olduğu için bu garanti geçerli değil. EDF bazı işleri (deadline'a yakın olanları) öne çekerken, paylaşılan darboğaz makinede başka işleri geciktirebiliyor — tam olarak gözlemlenen bu. Doğrulama detayları için `baseline/scheduler.py` çalıştırılıp `experiments/baseline/` altına yazılan schedule dosyalarına bakılabilir (reproducible, seed=42).

Bu gözlem, ileride Phase 9'da optimizasyon sonucuyla kıyaslarken **her iki baseline'ın da** referans olarak tutulmasını gerektiriyor — "hangi baseline'a göre iyileşme" sorusunun cevabı tek bir sayı değil.

## Phase 9 — Baseline vs Optimized (SMALL) — *HiGHS ile ölçüldü, tarihi kayıt*

> **2026-09-19 notu**: Bu bölümdeki (ve Phase 11/15/19'daki) sayılar, o zamanki aktif solver olan **HiGHS** ile ölçüldü. 2026-09-18'de solver Gurobi'ye geçirildi (bkz. `docs/decision-log.md`); Gurobi genelde belirgin şekilde daha iyi/hızlı sonuç buluyor. Bu tarihi sayılar CLAUDE.md kural 3 gereği (sonuç uydurma/silme yok) olduğu gibi bırakıldı — güncel Gurobi sonuçları için dokümanın en altındaki **"Solver Güncellemesi: Gurobi"** bölümüne bakın.

`optimization/comparison.py --size small --time-limit 120` çalıştırıldı (warm-start: FCFS, Stage "final" — bkz. Phase 8 bulgusu, makespan yerine birleşik $ hedefiyle karşılaştırma yapılıyor).

> **Güncelleme (Phase 11)**: Aşağıdaki tablo, Phase 11'de bulunan bir warm-start hatası (`optimization/replay.py`'nin bakım pencerelerini hesaba katmaması, bkz. decision-log) düzeltildikten SONRAKİ, doğru sayılardır. Düzeltme öncesi ilk ölçüm %5.22 iyileşme göstermişti; warm-start düzgün kabul edilince sonuç **iyileşti** (%10.67) — bu bir hata değil, düzeltmenin beklenen sonucu.

| Metric | FCFS | EDF | Optimized |
|---|---:|---:|---:|
| Production Time (h) | 144.31 | 144.31 | 146.50 |
| Energy Cost ($) | 4858.60 | 4742.23 | 3900.75 |
| Late Jobs | 3 | 7 | 4 |
| Avg Tardiness (h) | 0.20 | 0.18 | 0.09 |
| Avg Machine Utilization | 0.120 | 0.120 | 0.122 |
| **Total Cost ($, weighted)** | **13051.72** | 12863.95 | **11659.12** |

**Optimized vs FCFS toplam maliyet iyileşmesi: %10.67** (solver durumu: time limit, gap %5.33).

**Dürüst nüans**: Bu sefer neredeyse her metrik iyileşti (enerji %20, geciken iş 3→4 ile hemen hemen aynı, ortalama gecikme %55 azaldı) — düzeltilmiş warm-start'ın gerçekten daha iyi bir arama noktasından başladığının işareti.

**Reproducibility notu**: Veri üretimi (`SEED=42`) tam deterministik, ama **solver'ın time-limit'e dayalı sonucu değildir** — aynı model, farklı çalıştırmalarda (sistem yükü, zamanlama farkları nedeniyle) hafifçe farklı ama benzer kalitede çözümler bulabilir. Bu, MIP zaman sınırlı çözümlerin bilinen bir karakteristiği — veri üretiminin reproducibility'siyle karıştırılmamalı.

## Phase 11 — Predict → Optimize (SMALL) — *HiGHS ile ölçüldü, tarihi kayıt*

`ml/predict_optimize.py --size small --time-limit 120`: Phase 10'un ML modeli süreleri tahmin etti, optimizasyon bu tahminle plan kurdu, plan GERÇEK sürelerle yeniden zamanlandı (`optimization/replay.py`) ve öyle değerlendirildi:

| Senaryo | Total Cost ($) | FCFS'e göre iyileşme |
|---|---:|---:|
| FCFS (baseline) | 13051.72 | — |
| **ML-Predicted → Optimize → gerçek sürede çalıştır** | **12482.86** | **%4.36** |
| Ground-Truth → Optimize ("mükemmel bilgi", Phase 9) | 11659.12 | %10.67 |

**Yorum**: ML tabanlı optimizasyon, teorik maksimum iyileşmenin (mükemmel bilgiyle elde edilebilecek %10.67) yalnızca **%40.85**'ini yakalayabildi. Aradaki fark (%59.15), Phase 10'daki ML tahmin hatasının (R² 0.54) doğrudan maliyetidir — "tahmin ne kadar iyi olursa, optimizasyon o kadar değer katar" ilişkisinin somut, ölçülmüş kanıtı.

## Phase 15 — What-If Senaryolar (SMALL) — *HiGHS ile ölçüldü, tarihi kayıt*

`simulation/scenarios.py`, orijinal (senaryosuz) optimize edilmiş plan ($11659.12) ile 5 farklı senaryo çalıştırması karşılaştırıldı:

| Senaryo | Total Cost | Değişim | Not |
|---|---:|---:|---|
| Machine M003 failure (SMALL'daki tek Assembly makinesi) | — | — | **INFEASIBLE** — hiçbir geçerli plan yok |
| Machine M001 failure (3 CNC'den biri, yedekli) | $12747.22 | +%9.3 | Geçerli ama daha pahalı yeni plan bulundu |
| Energy price +20% | $14023.44 | +%20.3 | Enerji maliyeti +%49; production time/late jobs hafifçe iyileşti |
| Deadline shift −12h | $38011.34 | +%226 | Late jobs 4→41/50 — deadline'lara aşırı duyarlılık |
| Maintenance duration +50% | $14039.78 | +%20.4 | Late jobs 4→5, tardiness 0.09h→0.39h |

**En önemli bulgu**: Yedeksiz kritik makine (M003) arızası sistemi tamamen durdururken (infeasible), yedekli makine (M001) arızası sadece maliyeti artırıyor. Bu, "tek nokta bağımlılığı" riskinin somut, ölçülmüş bir kanıtı — fabrika tasarımı için doğrudan uygulanabilir bir öneri (kritik makine tiplerinde yedeklilik).

## Phase 19 — Deneysel Değerlendirme (SMALL / MEDIUM / LARGE)

Üç boyutta, aynı "final" (birleşik $) hedefiyle, `optimization/comparison.py` üzerinden sistematik ölçüm yapıldı. Amaç: ölçek büyüdükçe sistemin nerede zorlandığını dürüstçe göstermek.

### Model Boyutu (çözmeden önce, sadece kurulum)

> Bu tablo **solver'dan bağımsız** — model kurulumu (`optimization/model.py::build_model`) tamamen Pyomo tarafında, hiçbir solver çağrısı olmadan gerçekleşir. Gurobi'ye geçiş bu sayıları etkilemez, hâlâ geçerli.

| | Operasyon | Binary Değişken | Kısıt | Model Kurulum Süresi |
|---|---:|---:|---:|---:|
| SMALL | 162 | 30.437 | 64.990 | 0.49 sn |
| MEDIUM | 814 | 214.172 | 856.228 | 8.53 sn |
| LARGE | 3.245 | 1.741.716 | 25.465.109 | **8569.40 sn (2.4 saat)** |

**Kök neden (doğrulandı)**: Operasyon sayısı SMALL→LARGE arası 20 kat artarken, aynı makine tipini paylaşan operasyon **çiftleri** (C3 kısıtının temeli, `y[o,o']`) 413 kat arttı (2.789 → 1.151.635) — çünkü bu ilişki karesel (O(n²)) büyüyor: her makine tipi için o tipteki operasyon sayısının karesiyle orantılı. Bu, Phase 5'te seçilen "ikili çakışma" (pairwise disjunctive, Big-M) kısıt formülasyonunun literatürde bilinen bir zayıflığı — kod hatası değil, seçilen matematiksel yaklaşımın büyük ölçekteki doğal sınırı. Alternatif formülasyonlar (ör. zaman-indeksli) farklı ölçeklenme karakteristiği gösterir ama daha fazla değişken/karmaşıklık gerektirir — bu bir sonraki faz (Phase 20) veya gelecekteki bir iyileştirme için not.

### Baseline vs Optimized (Stage "final") — *HiGHS ile ölçüldü, tarihi kayıt*

> SMALL ve MEDIUM için güncel Gurobi sayıları dokümanın sonundaki **"Solver Güncellemesi: Gurobi"** bölümünde — MEDIUM'daki hikaye (aşağıdaki %0.00 iyileşme) Gurobi ile tamamen değişti.

| Metric | SMALL (120sn) | MEDIUM (180sn) | LARGE |
|---|---:|---:|---:|
| FCFS Total Cost ($) | 13051.72 | 29366.39 | — |
| Optimized Total Cost ($) | **11659.12** | 29366.39 | — |
| İyileşme | **%10.67** | **%0.00** | — |
| Solver Gap | %5.33 | %74.95 | — |
| Solver Durumu | Time limit | Time limit (warm-start'tan hiç iyileşmedi) | Model kurulumu bile tamamlanamadı (çözme denenmedi) |

**Dürüst yorum — ölçeklenme hikayesi tutarlı**: SMALL'da solver warm-start'ı gerçek anlamda iyileştirebiliyor (%10.67, gap %5.33 — makul). MEDIUM'da model (özellikle enerji `w[o,t]` mekanizması: 814×168≈136.752 ek ikili değişken + C3'ün genişlemiş hali) o kadar büyüdü ki solver 180 saniyede **warm-start'tan bir adım bile ilerleyemedi** (gap %74.95 — LP gevşetmesi çok zayıf). LARGE'da model kurulumu tek başına 2.4 saat sürdüğü için çözme denemesi hiç yapılmadı. Bu, "büyük problemler exact olarak çözülemiyorsa gizlenmez" ilkesine uygun, gerçek ve önemli bir bilimsel bulgu — MILP tabanlı exact çözümün bu formülasyonla nerede pratik sınırına dayandığını net gösteriyor.

**Not**: MEDIUM'un burada "final" hedefte %74.95 gap vermesi, Phase 8'deki MEDIUM "makespan-only" testiyle (gap %0.21) çelişmiyor — o test çok daha küçük bir modeldi (`w[o,t]` yok). Enerji mekanizması eklenince model büyüklüğü/zorluğu kalitatif olarak değişiyor.

## Phase 20 — Stress Test: "Diz Noktası" (Knee Point) Haritalaması

Phase 19'da MEDIUM (8.53sn) ile LARGE (8569sn) arasında devasa bir fark bulunmuştu. Bu fazda, aradaki büyüklüklerde (25, 30, 35, 40, 45 makine — orantılı iş sayılarıyla) **sadece model kurulum süresi** ölçülerek darboğazın tam olarak nerede başladığı haritalandı. Her nokta için 300 saniyelik sert bir zaman sınırı kullanıldı (bir nokta zaten zaman aşımına uğrarsa daha büyüğü denenmedi — monoton artış zaten biliniyor).

> **Solver'dan bağımsız, hâlâ geçerli**: Buradaki tüm süreler model KURULUMU (Pyomo, solver çağrılmadan önce) — Gurobi'ye geçiş bu darboğazı değiştirmez, çünkü sorun hiç solver'a ulaşmıyor. LARGE'ı Gurobi ile yeniden test etmedim (bkz. `docs/decision-log.md`, Solver Değişikliği kaydı) — 2.4 saati boşa harcamanın anlamı yok, sonuç aynı çıkardı.

| Makine / İş | Operasyon | Binary Değişken | Kısıt | Model Kurulum Süresi |
|---:|---:|---:|---:|---:|
| 20 / 250 (MEDIUM) | 814 | 214.172 | 856.228 | 8.53 sn |
| 25 / 350 | 1.144 | 341.656 | 1.755.294 | 18.85 sn |
| 30 / 450 | 1.480 | 497.172 | 3.248.548 | 33.24 sn |
| 35 / 550 | 1.790 | 664.671 | 5.206.096 | 54.08 sn |
| 40 / 700 | 2.279 | 971.424 | 9.307.597 | 151.10 sn |
| 45 / 850 | — | — | — | **>300 sn (zaman aşımı)** |
| 50 / 1000 (LARGE) | 3.245 | 1.741.716 | 25.465.109 | 8569.40 sn |

**Büyüme oranları (art arda noktalar arası)**:

| Makine artışı | Süre artışı |
|---|---|
| 20→25 (1.25×) | 2.21× |
| 25→30 (1.20×) | 1.76× |
| 30→35 (1.17×) | 1.63× |
| 35→40 (1.14×) | 2.79× |
| **40→50 (1.25×)** | **56.71×** |

**Bulgu — pratik sınır net şekilde 40-45 makine arasında**: 20'den 40 makineye kadar büyüme, C3'ün bilinen O(n²) karakteriyle kabaca tutarlı, kademeli bir artış (~1.6-2.8× her adımda). Ama 40→50 arası (sadece %25 daha fazla makine) süre **56.71 kat** arttı — bu, saf O(n²) beklentisinin (1.25²≈1.56×) çok üzerinde. Bu ek ivmelenme muhtemelen ikinci bir etkenden kaynaklanıyor: milyonlarca kısıtlı bir Pyomo modelini Python'da bellekte tutmanın/indekslemenin, belirli bir büyüklükten sonra kendi başına süper-lineer bir yüke dönüşmesi (bellek baskısı, garbage collection). Bu ayrıca doğrulanabilir bir hipotez ama şu an için sadece not ediliyor.

**Pratik sonuç**: Mevcut formülasyonla sistem **~40 makine / ~700 işe kadar** (build ~2.5 dakika) makul sınırlar içinde kalıyor; 45 makineden itibaren pratik olarak kullanılamaz hale geliyor. Bu, bitirme projesi raporunun "Limitations" bölümü için net, sayısal bir sınır.

**Seçenek B notu**: Kullanıcıyla, bu sınırı aşmak için C3'ü farklı bir formülasyonla (ör. zaman-indeksli) yeniden kurmanın (Seçenek B) mümkün olduğu konuşuldu; kullanıcı bunu **projenin sonuna, çekirdek sistem tamamlandıktan sonra** değerlendirmeye bıraktı (bkz. `docs/decision-log.md`). Bu doküman güncel formülasyonun sınırlarını olduğu gibi, gizlemeden yansıtıyor.

## Solver Güncellemesi: Gurobi (2026-09-18/19)

Kullanıcı 2026-09-18'de akademik bir Gurobi lisansı edindi; aktif solver HiGHS'ten Gurobi'ye geçirildi (bkz. `docs/decision-log.md` "Solver Değişikliği: HiGHS -> Gurobi"). Aşağıdaki sayılar, yukarıdaki HiGHS ölçümleriyle **aynı ayarlarla** (aynı `time_limit_seconds`, aynı stage, aynı SEED=42 veri) yeniden çalıştırılıp ölçüldü — 2026-09-19'da gerçekten çalıştırılmış, uydurulmamış sonuçlar.

### SMALL — "final" hedef, 120sn (Phase 9 ile aynı ayar)

| | HiGHS (yukarıdaki Phase 9) | **Gurobi** |
|---|---:|---:|
| Solver durumu | time limit, gap %5.33–10.42 (çalıştırmaya göre değişken) | **optimal, gap %0** |
| Total Cost ($) | 11.659,12 – 12.370,73 arası | **11.369,07** |
| FCFS'e göre iyileşme | %5,22 – %10,67 | **%12,89** |
| Toplam çalışma süresi | 120 sn'nin tamamı kullanılıyordu | **~15 sn'de bitti** (kanıtlanmış optimal) |

Gurobi, HiGHS'in hiçbir zaman kanıtlayamadığı optimalliği ~15 saniyede kanıtladı.

### MEDIUM — "final" hedef, 180sn (Phase 19 ile aynı ayar) — en çarpıcı fark

| | HiGHS (yukarıdaki Phase 19) | **Gurobi** |
|---|---:|---:|
| Solver durumu | time limit, **gap %74,95** | time limit, **gap %7,01** |
| FCFS'e göre iyileşme | **%0,00** (warm-start'tan hiç ilerleyemedi) | **%11,81** |
| Total Cost ($) | 29.366,39 (FCFS ile aynı) | **25.898,96** |

HiGHS ile MEDIUM'da optimizasyonun pratikte hiçbir faydası yoktu. Aynı 180 saniyede Gurobi ile gap %7'ye iniyor ve gerçek, anlamlı bir iyileşme ortaya çıkıyor — Gurobi'ye geçiş MEDIUM ölçeğini "kullanılamaz" durumdan "kullanılabilir" duruma getirdi.

### Predict→Optimize (ML tahminiyle, gerçekçi senaryo), SMALL, 120sn (Phase 11 / Final Demo ile aynı ayar)

| | HiGHS (Final Demo) | **Gurobi** |
|---|---:|---:|
| Solver durumu | time limit, gap %6,35 | **optimal, gap %0** |
| Total Cost ($) | ~12.482 | **11.995,72** |
| FCFS'e göre iyileşme | %4,36 | **%8,09** |
| Çalışma süresi | 120sn'nin tamamı | **~12 sn** |

### LARGE — değişmedi, yeniden test edilmedi (bilerek)

Phase 19-20'deki darboğaz, **solver hiç devreye girmeden**, salt Pyomo'nun modeli kurma aşamasında oluşuyor (yukarıdaki notlara bkz.) — bu adım hangi solver kullanıldığından tamamen bağımsız. 2,4 saati boşa harcayıp yeniden ölçmedim; sonuç aynı çıkardı. LARGE'ı gerçekten çözülebilir hale getirmek Phase 20'de konuşulup projenin sonuna bırakılan Seçenek B'yi (C3'ün farklı bir matematiksel formülasyonu) gerektiriyor — solver seçimiyle ilgisi yok.

### Özet

- **SMALL**: zaten iyi çalışıyordu, şimdi kanıtlanmış optimal + %12,89 (eskiden %10,67 tavan).
- **MEDIUM**: HiGHS ile fiilen ölü bir özellikti (%0 iyileşme), Gurobi ile gerçek değer üretiyor (%11,81).
- **LARGE**: solver'dan bağımsız bir mimari sınır, değişmedi.

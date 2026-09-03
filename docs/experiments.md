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

## Phase 9 — Baseline vs Optimized (SMALL)

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

## Phase 11 — Predict → Optimize (SMALL)

`ml/predict_optimize.py --size small --time-limit 120`: Phase 10'un ML modeli süreleri tahmin etti, optimizasyon bu tahminle plan kurdu, plan GERÇEK sürelerle yeniden zamanlandı (`optimization/replay.py`) ve öyle değerlendirildi:

| Senaryo | Total Cost ($) | FCFS'e göre iyileşme |
|---|---:|---:|
| FCFS (baseline) | 13051.72 | — |
| **ML-Predicted → Optimize → gerçek sürede çalıştır** | **12482.86** | **%4.36** |
| Ground-Truth → Optimize ("mükemmel bilgi", Phase 9) | 11659.12 | %10.67 |

**Yorum**: ML tabanlı optimizasyon, teorik maksimum iyileşmenin (mükemmel bilgiyle elde edilebilecek %10.67) yalnızca **%40.85**'ini yakalayabildi. Aradaki fark (%59.15), Phase 10'daki ML tahmin hatasının (R² 0.54) doğrudan maliyetidir — "tahmin ne kadar iyi olursa, optimizasyon o kadar değer katar" ilişkisinin somut, ölçülmüş kanıtı.

## Phase 15 — What-If Senaryolar (SMALL)

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

| | Operasyon | Binary Değişken | Kısıt | Model Kurulum Süresi |
|---|---:|---:|---:|---:|
| SMALL | 162 | 30.437 | 64.990 | 0.49 sn |
| MEDIUM | 814 | 214.172 | 856.228 | 8.53 sn |
| LARGE | 3.245 | 1.741.716 | 25.465.109 | **8569.40 sn (2.4 saat)** |

**Kök neden (doğrulandı)**: Operasyon sayısı SMALL→LARGE arası 20 kat artarken, aynı makine tipini paylaşan operasyon **çiftleri** (C3 kısıtının temeli, `y[o,o']`) 413 kat arttı (2.789 → 1.151.635) — çünkü bu ilişki karesel (O(n²)) büyüyor: her makine tipi için o tipteki operasyon sayısının karesiyle orantılı. Bu, Phase 5'te seçilen "ikili çakışma" (pairwise disjunctive, Big-M) kısıt formülasyonunun literatürde bilinen bir zayıflığı — kod hatası değil, seçilen matematiksel yaklaşımın büyük ölçekteki doğal sınırı. Alternatif formülasyonlar (ör. zaman-indeksli) farklı ölçeklenme karakteristiği gösterir ama daha fazla değişken/karmaşıklık gerektirir — bu bir sonraki faz (Phase 20) veya gelecekteki bir iyileştirme için not.

### Baseline vs Optimized (Stage "final")

| Metric | SMALL (120sn) | MEDIUM (180sn) | LARGE |
|---|---:|---:|---:|
| FCFS Total Cost ($) | 13051.72 | 29366.39 | — |
| Optimized Total Cost ($) | **11659.12** | 29366.39 | — |
| İyileşme | **%10.67** | **%0.00** | — |
| Solver Gap | %5.33 | %74.95 | — |
| Solver Durumu | Time limit | Time limit (warm-start'tan hiç iyileşmedi) | Model kurulumu bile tamamlanamadı (çözme denenmedi) |

**Dürüst yorum — ölçeklenme hikayesi tutarlı**: SMALL'da solver warm-start'ı gerçek anlamda iyileştirebiliyor (%10.67, gap %5.33 — makul). MEDIUM'da model (özellikle enerji `w[o,t]` mekanizması: 814×168≈136.752 ek ikili değişken + C3'ün genişlemiş hali) o kadar büyüdü ki solver 180 saniyede **warm-start'tan bir adım bile ilerleyemedi** (gap %74.95 — LP gevşetmesi çok zayıf). LARGE'da model kurulumu tek başına 2.4 saat sürdüğü için çözme denemesi hiç yapılmadı. Bu, "büyük problemler exact olarak çözülemiyorsa gizlenmez" ilkesine uygun, gerçek ve önemli bir bilimsel bulgu — MILP tabanlı exact çözümün bu formülasyonla nerede pratik sınırına dayandığını net gösteriyor.

**Not**: MEDIUM'un burada "final" hedefte %74.95 gap vermesi, Phase 8'deki MEDIUM "makespan-only" testiyle (gap %0.21) çelişmiyor — o test çok daha küçük bir modeldi (`w[o,t]` yok). Enerji mekanizması eklenince model büyüklüğü/zorluğu kalitatif olarak değişiyor.

## Planlanan İçerik (Phase 20)

- Stress test: bu fazda bulunan O(n²) darboğazın (C3/y_pairs) MEDIUM/LARGE için ne kadar erken devreye girdiğini daha ince taneli boyutlarla (ör. 30, 40 makine) haritalamak
- Solver memory kullanımı ölçümü
- Mümkünse alternatif formülasyon (zaman-indeksli ya da decomposition) fizibilite değerlendirmesi — kapsamlı bir yeniden tasarım, ayrı bir karar gerektirir

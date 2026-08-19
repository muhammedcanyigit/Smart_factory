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

## Planlanan İçerik (Phase 19-20)

- Deney tasarımı: SMALL (10 makine/50 job), MEDIUM (20 makine/250 job), LARGE (50 makine/1000 job)
- Ölçülecek metrikler: solve time, objective value, energy cost, tardiness, utilization
- Baseline vs Optimization karşılaştırması
- ML vs Ground Truth karşılaştırması
- Normal Scenario vs Failure Scenario karşılaştırması
- Stress test bulguları (solver'ın zorlandığı nokta — varsa gizlenmeden raporlanır)

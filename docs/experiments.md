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

`optimization/comparison.py --size small --time-limit 120` çalıştırıldı (warm-start: FCFS, Stage "final" — bkz. Phase 8 bulgusu, makespan yerine birleşik $ hedefiyle karşılaştırma yapılıyor):

| Metric | FCFS | EDF | Optimized |
|---|---:|---:|---:|
| Production Time (h) | 144.31 | 144.31 | 150.23 |
| Energy Cost ($) | 4858.60 | 4742.23 | 3837.17 |
| Late Jobs | 3 | 7 | 6 |
| Avg Tardiness (h) | 0.20 | 0.18 | 0.20 |
| Avg Machine Utilization | 0.120 | 0.120 | 0.121 |
| **Total Cost ($, weighted)** | **13051.72** | 12863.95 | **12370.73** |

**Optimized vs FCFS toplam maliyet iyileşmesi: %5.22** (solver durumu: time limit, gap %10.42 — kanıtlanmış optimal değil ama gerçek, ölçülmüş bir sonuç).

**Dürüst nüans — her metrik iyileşmedi**: Enerji maliyeti belirgin şekilde düştü (%21) ve bu toplam maliyeti aşağı çekti, ama Production Time arttı (144→150h) ve Late Jobs sayısı arttı (3→6). Bu beklenen bir çok-amaçlı ödünleşim: model, toplam **$ maliyetini** minimize ediyor, tek tek her metriği değil. Ağırlıklarımız (`c_time=50, c_tardy=100`) enerji tasarrufunun bazı işlerin biraz gecikmesine değdiğine "karar veriyor". Bu, `c_tardy` gibi varsayılan katsayıların sonucu doğrudan etkilediğinin somut kanıtı — Phase 19-20'deki duyarlılık analizini daha da önemli kılıyor.

**Reproducibility notu**: Veri üretimi (`SEED=42`) tam deterministik, ama **solver'ın time-limit'e dayalı sonucu değildir** — aynı model, farklı çalıştırmalarda (sistem yükü, zamanlama farkları nedeniyle) hafifçe farklı ama benzer kalitede çözümler bulabilir (ör. bu tabloda $12370.73, birkaç dakika önceki bir denemede $12263.83 çıkmıştı). Bu, MIP zaman sınırlı çözümlerin bilinen bir karakteristiği — veri üretiminin reproducibility'siyle karıştırılmamalı.

## Planlanan İçerik (Phase 19-20)

- Deney tasarımı: SMALL (10 makine/50 job), MEDIUM (20 makine/250 job), LARGE (50 makine/1000 job)
- Ölçülecek metrikler: solve time, objective value, energy cost, tardiness, utilization
- Baseline vs Optimization karşılaştırması
- ML vs Ground Truth karşılaştırması
- Normal Scenario vs Failure Scenario karşılaştırması
- Stress test bulguları (solver'ın zorlandığı nokta — varsa gizlenmeden raporlanır)

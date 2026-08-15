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

## Planlanan İçerik (Phase 19-20)

- Deney tasarımı: SMALL (10 makine/50 job), MEDIUM (20 makine/250 job), LARGE (50 makine/1000 job)
- Ölçülecek metrikler: solve time, objective value, energy cost, tardiness, utilization
- Baseline vs Optimization karşılaştırması
- ML vs Ground Truth karşılaştırması
- Normal Scenario vs Failure Scenario karşılaştırması
- Stress test bulguları (solver'ın zorlandığı nokta — varsa gizlenmeden raporlanır)

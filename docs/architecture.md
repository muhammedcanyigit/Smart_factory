# System Architecture

> Phase 22'de (mimari sadeleştirme) dolduruldu — sistem tamamlandıktan sonraki gerçek hali. Kararların gerekçeleri için bkz. [decision-log.md](decision-log.md); sayısal sonuçlar için [experiments.md](experiments.md).

## 1. Modül Sorumlulukları

| Modül | Sorumluluk | Girdi | Çıktı | Tanıtıldığı Faz |
|---|---|---|---|---|
| `data_generator/` | Sentetik fabrika verisi üretimi (deterministik, `SEED=42`) | `config/config.yaml` | `machines/jobs/operations/energy_prices/maintenance` DataFrame'leri | Phase 2 |
| `preprocessing/` | Feature engineering (`features.py`) + savunmacı veri temizleme (`cleaning.py`) | dataset dict | ML için feature tablosu / temizlenmiş dataset | Phase 10, Phase 22 |
| `baseline/` | Kural tabanlı planlayıcı (FCFS/EDF) + ortak metrik hesaplama | dataset | schedule DataFrame + metrikler | Phase 3 |
| `optimization/` | MILP modeli (Pyomo) — değişken/kısıt/amaç/solver/sonuç çıkarma | dataset (+ opsiyonel ML tahmini) | optimal/en-iyi-bulunan schedule | Phase 4-9, 11 |
| `ml/` | İşlem süresi & enerji tüketimi tahmin modelleri | feature tablosu | eğitilmiş model (`.joblib`) + tahminler | Phase 10, 12 |
| `digital_twin/` | Fabrikanın anlık durum modeli (makine/job state) | dataset | `FactoryState` nesnesi | Phase 13 |
| `simulation/` | Bir schedule'ı Digital Twin üzerinde zaman içinde oynatma + What-If senaryo dönüşümleri | schedule + dataset | güncellenmiş `FactoryState`, senaryolu dataset | Phase 14-15 |
| `backend/` | FastAPI servis katmanı — `services/pipeline.py` tüm döngüyü birleştirir, `api/routes.py` HTTP'ye açar | HTTP istek | JSON yanıt | Phase 16-17 |
| `frontend/` | Tek sayfa dashboard (vanilla JS + Plotly.js CDN, build adımı yok) | backend API | tarayıcıda görsel arayüz | Phase 17-18 |
| `tests/` | pytest test suite (minik el-hesabı örnekleriyle hızlı, <2sn) | — | doğrulama | Phase 21 |

## 2. Ana Veri Akışı (Phase 16'nın döngüsü)

```
config/config.yaml (SEED=42, dataset boyutu, solver ayarları)
        │
        ▼
data_generator.generate_dataset()  ──────────────────► data/synthetic/<size>/*.csv (opsiyonel kayıt)
        │
        ▼
┌───────────────────────────────────────────────────────────┐
│                    backend/services/pipeline.py             │
│                                                               │
│  (opsiyonel) simulation.scenarios.SCENARIOS[...] (dataset)  │
│                         │                                     │
│                         ▼                                     │
│              digital_twin.DigitalTwin(dataset)  ── t=0 durumu │
│                         │                                     │
│                         ▼                                     │
│   ml.prediction.load_model() → predict_processing_times()     │
│                         │                                     │
│                         ▼                                     │
│   optimization.model.build_model(dataset_predicted, "final")  │
│                         │                                     │
│                         ▼                                     │
│   optimization.solver.solve_with_warm_start(                  │
│       warm_start = baseline.scheduler.run_baseline(FCFS) )    │
│                         │                                     │
│                         ▼                                     │
│   ml.predict_optimize.replay_with_ground_truth()               │
│        (atama+sıra sabit, GERÇEK sürelerle yeniden zamanla)   │
│                         │                                     │
│                         ▼                                     │
│   simulation.engine.SimulationEngine(twin, schedule).run_all()│
│                         │                                     │
│                         ▼                                     │
│              {feasible, metrics, schedule, twin_snapshot}      │
└───────────────────────────────────────────────────────────┘
                         │
                         ▼
              backend/api/routes.py  (JSON)
                         │
                         ▼
              frontend/index.html  (dashboard)
```

**Neden `replay_with_ground_truth` bir ara adım**: ML tahminiyle kurulan optimizasyon planı, GERÇEK sürelerle çalıştırılınca farklı sonuç verir (bkz. Phase 11 — tahmin hatasının maliyeti %59.15 olarak ölçüldü). `optimization/replay.py`'deki ortak `replay_schedule()` fonksiyonu hem bunun için hem warm-start'ın kendi içinde tutarlı olması için (Phase 8/11) kullanılıyor — tek bir fonksiyon, iki kullanım yeri.

## 3. Solver Katmanı — Neden İki Ayrı Arayüz Var

`optimization/solver.py` (Pyomo'nun `SolverFactory('highs')` arayüzü) ve `optimization/native_solver.py` (Pyomo'yu sadece model kurmak için kullanıp çözümü doğrudan `highspy`'a devreden yol) birlikte var — tesadüf değil, Phase 7-8'de bulunan gerçek bir kütüphane hatasının sonucu: `appsi_highs` (üçüncü bir Pyomo-HiGHS köprüsü), solver "çözüm yok" dediğinde bu ortamda sonsuza kadar takılı kalıyordu. `native_solver.py`, warm-start desteğini de koruyarak bu sorunu çözüyor ve **önerilen, gerçek kullanılan yol** — `solver.py` daha basit (warm-start'sız) durumlar için hâlâ duruyor. Detay: [decision-log.md](decision-log.md) Phase 7-8.

## 4. Bilinen Sınırlamalar (Rapor "Limitations" Bölümü İçin)

- **Ölçeklenme**: Mevcut MILP formülasyonu (C3 — ikili çakışma/pairwise disjunctive kısıtı) ~40 makine/~700 işe kadar pratik; 45+ makinede model kurulumu bile dakikalar/saatler sürüyor (kök neden: O(n²) — bkz. [experiments.md](experiments.md) Phase 19-20). Alternatif formülasyon (zaman-indeksli) projenin sonuna ertelendi.
- **Kapasite kısıtı aktif değil**: `Machine.capacity` alanı üretiliyor ama Phase 5'te bilinçli olarak MILP'e bir eşitsizlik olarak eklenmedi (quantity'nin etkisi zaten `processing_time`'a gömülü, çifte sayım olurdu) — bkz. decision-log Phase 5.
- **Solver sonuçları tam deterministik değil**: Veri üretimi (`SEED=42`) deterministik ama zaman-sınırlı MIP çözümleri, sistem yüküne göre çalıştırmalar arası hafifçe farklılaşabilir (bkz. experiments.md Phase 9 notu).
- **Digital Twin gerçek zamanlı değil**: Sensör/IoT bağlantısı yok, simülasyon tabanlı bir durum modeli (Phase 0'dan beri bilinçli bir kapsam sınırı).

## 5. Klasör Yapısındaki Sadeleştirmeler (Phase 22)

- `preprocessing/cleaning.py` — Phase 0'dan beri boş stub'du; sentetik veri zaten temiz üretildiği için hiç çağrılmamıştı. Gerçek bir doğrulama/temizleme fonksiyonuyla dolduruldu (savunmacı katman + "veri temizleme" kavramının somut karşılığı).
- `experiments/optimization/` ve `experiments/ml/` klasörleri kaldırıldı — 21 faz boyunca hiç kullanılmamışlardı, tüm deney çıktıları fiilen `experiments/results/` altında birikmişti.

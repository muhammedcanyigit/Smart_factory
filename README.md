# Smart Factory — Digital Twin & Optimization

AI destekli üretim planlama, enerji optimizasyonu ve what-if simülasyon sistemi. Bir bitirme projesi ve öğrenme projesi olarak geliştirilmektedir.

## Proje Ne Yapıyor

Fabrikadaki üretim işlerinin hangi makinede, hangi sırayla ve ne zaman yapılması gerektiğini matematiksel optimizasyon (MILP) ile hesaplar; makine öğrenmesi ile işlem süresi/enerji tüketimi tahmin eder; bir Digital Twin üzerinde bu planı simüle eder; ve "makine arızalanırsa / enerji fiyatı artarsa ne olur?" tarzı what-if senaryolarını çalıştırır.

Bu proje bir karar destek sistemidir (decision support system) — gerçek bir fabrikanın kontrol sistemi değildir ve gerçek zamanlı IoT/PLC bağlantısı içermez.

## Durum

Şu an: **Phase 0-22 tamamlandı** (24 fazdan 23'ü) — sırada sadece Final Demo var. Proje tanımı → veri modeli → sentetik veri üretici → baseline → MILP → solver → baseline-vs-optimized → ML (süre+enerji tahmini) → Predict→Optimize → Digital Twin → Simülasyon → What-If senaryolar → uçtan uca pipeline → Dashboard → deneysel değerlendirme + stress test → testler → mimari sadeleştirme.

- **Projeyi hiç bilmeyen biri için, çok basit anlatım**: [PROJE-OZETI.md](PROJE-OZETI.md) — buradan başla.
- İlerleme ve gerekçeler için bkz. [CHANGELOG.md](CHANGELOG.md).
- "Neden bu kararı verdik" için bkz. [docs/decision-log.md](docs/decision-log.md).
- Sistem mimarisi ve bilinen sınırlamalar için bkz. [docs/architecture.md](docs/architecture.md).
- Deney sonuçları ve ölçeklenme bulguları için bkz. [docs/experiments.md](docs/experiments.md).

## Dashboard'ı Çalıştırma

```bash
pip install -r requirements.txt
uvicorn backend.main:app --reload
```

Tarayıcıda [http://127.0.0.1:8000/](http://127.0.0.1:8000/) — "Fabrikayı Yükle", "OPTIMIZE ET" ve What-If senaryolarını buradan deneyebilirsin.

## Testleri Çalıştırma

```bash
pytest tests/
```

21+ test, ~1.2 saniyede tamamlanır (hız için minik el-hesabı örnekleri kullanır — SMALL/MEDIUM ölçeğinde tam çözüm dakikalar sürebiliyor, bkz. [docs/experiments.md](docs/experiments.md)).

## Veri Hakkında Not

Bu projede kullanılan veri **sentetik (synthetic)** olarak üretilmektedir; gerçek bir fabrikaya ait değildir. Sonuçlar her zaman "sentetik veri setinde gözlemlenen" ifadesiyle raporlanır, gerçek fabrika verisi gibi sunulmaz. Detay için bkz. [docs/dataset.md](docs/dataset.md).

## Klasör Yapısı

```
config/            konfigürasyon dosyaları (dataset boyutu, solver seçimi, seed)
data/               ham / işlenmiş / sentetik veri (raw, processed şu an kullanılmıyor)
data_generator/     sentetik fabrika verisi üreticisi
preprocessing/      veri temizleme ve feature engineering
baseline/           kural tabanlı planlayıcı (FCFS/EDF) + ortak metrikler
ml/                 işlem süresi / enerji tahmin modelleri + Predict→Optimize
optimization/       Pyomo tabanlı MILP modeli (değişken/kısıt/amaç/solver/warm-start)
simulation/         optimizasyon planının zaman içinde oynatılması + What-If senaryolar
digital_twin/       fabrika durumunun (state) modeli
backend/            FastAPI servisi (api/ + services/pipeline.py — uçtan uca döngü)
frontend/           dashboard (vanilla JS + Plotly.js, build adımı yok)
experiments/        deney çıktıları (baseline/ ve results/)
tests/              pytest test suite
docs/               proje planı, mimari, matematiksel model, dataset, deney dokümanları
```

Modül sorumluluklarının ve veri akışının tam açıklaması: [docs/architecture.md](docs/architecture.md).

## Geliştirme Prensibi

Sistem aşamalar (phase) halinde geliştirilir; her aşama bir öncekinin çalışan versiyonu üzerine kurulur. Her yeni aşamaya geçmeden önce ne/neden/nasıl açıklanır, sonra koda geçilir. Detaylı yol haritası için bkz. [docs/project-plan.md](docs/project-plan.md).

# Smart Factory — Digital Twin & Optimization

AI destekli üretim planlama, enerji optimizasyonu ve what-if simülasyon sistemi. Bir bitirme projesi ve öğrenme projesi olarak geliştirilmektedir.

## Proje Ne Yapıyor

Fabrikadaki üretim işlerinin hangi makinede, hangi sırayla ve ne zaman yapılması gerektiğini matematiksel optimizasyon (MILP) ile hesaplar; makine öğrenmesi ile işlem süresi/enerji tüketimi tahmin eder; bir Digital Twin üzerinde bu planı simüle eder; ve "makine arızalanırsa / enerji fiyatı artarsa ne olur?" tarzı what-if senaryolarını çalıştırır.

Bu proje bir karar destek sistemidir (decision support system) — gerçek bir fabrikanın kontrol sistemi değildir ve gerçek zamanlı IoT/PLC bağlantısı içermez.

## Durum

Şu an: **Phase 0-9 tamamlandı** (24 fazdan 10'u). Proje tanımı → veri modeli → sentetik veri üretici → baseline (FCFS/EDF) → matematiksel model (MILP) → Pyomo implementasyonu → solver optimizasyonu → baseline vs optimized karşılaştırması.

- **Projeyi hiç bilmeyen biri için, çok basit anlatım**: [PROJE-OZETI.md](PROJE-OZETI.md) — buradan başla.
- İlerleme ve gerekçeler için bkz. [CHANGELOG.md](CHANGELOG.md).
- "Neden bu kararı verdik" için bkz. [docs/decision-log.md](docs/decision-log.md).

## Veri Hakkında Not

Bu projede kullanılan veri **sentetik (synthetic)** olarak üretilmektedir; gerçek bir fabrikaya ait değildir. Sonuçlar her zaman "sentetik veri setinde gözlemlenen" ifadesiyle raporlanır, gerçek fabrika verisi gibi sunulmaz. Detay için bkz. [docs/dataset.md](docs/dataset.md).

## Klasör Yapısı

```
config/            konfigürasyon dosyaları (dataset boyutu, solver seçimi, seed)
data/               ham / işlenmiş / sentetik veri
data_generator/     sentetik fabrika verisi üreticisi
preprocessing/      veri temizleme ve feature engineering
ml/                 işlem süresi / enerji tahmin modelleri
optimization/       Pyomo tabanlı MILP modeli (değişken/kısıt/amaç/solver)
simulation/         optimizasyon planının zaman içinde oynatılması
digital_twin/       fabrika durumunun (state) modeli
backend/            FastAPI servisi
frontend/           dashboard
experiments/        deney sonuçları (baseline/optimization/ml)
tests/              unit testler
docs/               proje planı, mimari, matematiksel model, dataset, deney dokümanları
```

## Geliştirme Prensibi

Sistem aşamalar (phase) halinde geliştirilir; her aşama bir öncekinin çalışan versiyonu üzerine kurulur. Her yeni aşamaya geçmeden önce ne/neden/nasıl açıklanır, sonra koda geçilir. Detaylı yol haritası için bkz. [docs/project-plan.md](docs/project-plan.md).

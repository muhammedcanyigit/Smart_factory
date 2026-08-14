# Changelog

Bu dosya, projede yapılan önemli değişikliklerin kaydını tutar. En yeni değişiklik en üstte. Format ve güncelleme kuralı için bkz. [CLAUDE.md](CLAUDE.md).

## 2026-08-14 — Proje iskeleti oluşturuldu

- Phase 0 tamamlandı: proje tanımı, terminoloji, mimari diyagram, yol haritası, dataset stratejisi, matematiksel problem tanımı, riskler → `docs/project-plan.md`.
- Dataset araştırması yapıldı: birleşik gerçek dataset bulunamadı; Steel Industry Energy Consumption (UCI #851), AI4I 2020 Predictive Maintenance (UCI #601) ve Taillard/Hurink/Brandimarte job-shop benchmark instance'ları kalibrasyon/doğrulama referansı olarak seçildi. Ana veri kaynağı synthetic generator olacak (Phase 2).
- Kod içermeyen proje klasör/dosya iskeleti oluşturuldu: `config/`, `data/`, `data_generator/`, `preprocessing/`, `ml/`, `optimization/`, `simulation/`, `digital_twin/`, `backend/`, `frontend/`, `experiments/`, `tests/`, `docs/`.
- `CLAUDE.md` oluşturuldu: aşama-aşama geliştirme kuralı, terim açıklama kuralı, sonuç uydurmama kuralı ve bu CHANGELOG'un her önemli değişiklikte güncellenmesi kuralı yazıldı.

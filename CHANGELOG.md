# Changelog

Bu dosya, projede yapılan önemli değişikliklerin kaydını tutar. En yeni değişiklik en üstte. Format ve güncelleme kuralı için bkz. [CLAUDE.md](CLAUDE.md).

## 2026-08-15 — Phase 2: Synthetic Data Generator (ilk çalışan kod)

- `data_generator/schemas.py`: Machine, Job, Operation, EnergyPrice, Maintenance dataclass'ları + MachineStatus/MaintenanceType enum'ları.
- `data_generator/generator.py`: seed=42 ile deterministik sentetik veri üretici. Kurallar: süre↑→enerji↑ (korelasyon test edildi: 0.82), yaş↑→bakım olasılığı↑, ürün-makine uyumluluğu (routing/template), saatlik time-of-use enerji fiyatı (peak/off-peak).
- `config/config.yaml`'a `horizon_hours: 168` eklendi (7 günlük planlama ufku).
- Doğrulama yapıldı: iki ayrı çalıştırma birebir aynı çıktıyı üretti (reproducibility), SMALL/MEDIUM/LARGE preset'lerinin üçü de hatasız çalıştı, hiçbir required_machine_type için uygun makine eksik değil, deadline < release_time gibi saçma durum yok.
- `docs/dataset.md`'ye Operation.processing_time/energy_consumption'ın "nominal değer" olduğuna dair modelleme kararı eklendi (kod ile doküman tutarlılığı için).
- Üretilen CSV'ler (`data/synthetic/*/`) .gitignore'da — reproducible oldukları için repoya commit edilmiyor, script ile yeniden üretilebiliyor.

## 2026-08-15 — Phase 1: Veri modeli tasarlandı

- `docs/dataset.md` dolduruldu: Machine, Job, Operation, EnergyPrice, Maintenance entity'leri — alanlar, tipler, ilişkiler (ER diagram), temel iş kuralları.
- Job—Operation ilişkisine `sequence_no` eklendi (operasyonların sıralı yapılması gerekliliği için); Maintenance'a `maintenance_id` primary key eklendi.
- Henüz kod yazılmadı — bu saf tasarım dokümanıdır, Phase 2'de (synthetic generator) bu modele göre kod yazılacak.

## 2026-08-15 — GitHub reposuna bağlandı

- Local proje bağımsız bir git deposu haline getirildi (önceden `Smart_factory` klasörü, kullanıcının ev dizinine ait alakasız bir git reposunun içinde kalmıştı — buna dokunulmadı, ayrı repo kuruldu).
- Uzak repo eklendi: `https://github.com/muhammedcanyigit/Smart_factory.git`.
- GitHub'ın otomatik oluşturduğu placeholder README ile local README arasındaki merge çakışması, local (detaylı) içerik korunarak çözüldü.
- İlk commit + merge commit `main` branch'ine push edildi.

## 2026-08-14 — Proje iskeleti oluşturuldu

- Phase 0 tamamlandı: proje tanımı, terminoloji, mimari diyagram, yol haritası, dataset stratejisi, matematiksel problem tanımı, riskler → `docs/project-plan.md`.
- Dataset araştırması yapıldı: birleşik gerçek dataset bulunamadı; Steel Industry Energy Consumption (UCI #851), AI4I 2020 Predictive Maintenance (UCI #601) ve Taillard/Hurink/Brandimarte job-shop benchmark instance'ları kalibrasyon/doğrulama referansı olarak seçildi. Ana veri kaynağı synthetic generator olacak (Phase 2).
- Kod içermeyen proje klasör/dosya iskeleti oluşturuldu: `config/`, `data/`, `data_generator/`, `preprocessing/`, `ml/`, `optimization/`, `simulation/`, `digital_twin/`, `backend/`, `frontend/`, `experiments/`, `tests/`, `docs/`.
- `CLAUDE.md` oluşturuldu: aşama-aşama geliştirme kuralı, terim açıklama kuralı, sonuç uydurmama kuralı ve bu CHANGELOG'un her önemli değişiklikte güncellenmesi kuralı yazıldı.

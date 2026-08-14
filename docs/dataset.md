# Phase 1 — Data Model (Veri Modeli)

> Bu doküman fabrikanın veri modelini tanımlar: hangi entity'ler var, her birinin hangi alanları var, aralarındaki ilişkiler ne. Bu, Phase 2'deki synthetic generator'ın, Phase 4-6'daki matematiksel modelin ve Phase 10-12'deki ML modellerinin ortak referans noktasıdır. Henüz kod yazılmamıştır — bu bir tasarım dokümanıdır.

Dataset araştırması ve strateji için bkz. [project-plan.md](project-plan.md) Bölüm E.

---

## Entity'ler ve Alanları

### Machine

| Alan | Tip | Zorunlu | Açıklama |
|---|---|---|---|
| machine_id | string (PK) | evet | Benzersiz makine kimliği |
| machine_type | string | evet | Makine kategorisi (ör. "CNC", "Press", "Assembly"). Operation'ın `required_machine_type` alanıyla eşleşir |
| capacity | float | evet | Makinenin birim zamanda işleyebileceği miktar |
| status | enum | evet | `idle` \| `running` \| `maintenance` \| `broken` |
| efficiency | float (0-1) | evet | Verimlilik katsayısı — işlem süresini etkiler (düşük efficiency → daha uzun süre) |
| energy_rate | float | evet | Birim zamanda enerji tüketim oranı (kWh/saat) |
| age | int | evet | Makine yaşı (yıl) — arıza olasılığını etkiler |
| available_from | datetime | evet | Makinenin çalışabilir olduğu zaman penceresinin başlangıcı |
| available_until | datetime | evet | Makinenin çalışabilir olduğu zaman penceresinin bitişi |

### Job

| Alan | Tip | Zorunlu | Açıklama |
|---|---|---|---|
| job_id | string (PK) | evet | Benzersiz iş kimliği |
| product_type | string | evet | Hangi ürün — hangi Operation dizisinin gerekeceğini belirler |
| quantity | int | evet | Üretilecek miktar |
| priority | int | evet | Öncelik seviyesi (baseline'da ve tie-breaking'de kullanılabilir) |
| release_time | datetime | evet | Bu işin en erken başlayabileceği an |
| deadline | datetime | evet | Teslim tarihi — tardiness hesaplamasının referansı |

### Operation

Bir Job, sırayla yapılması gereken birden fazla Operation'dan oluşabilir (ör. "kesim" → "montaj" → "kalite kontrol").

| Alan | Tip | Zorunlu | Açıklama |
|---|---|---|---|
| operation_id | string (PK) | evet | Benzersiz operasyon kimliği |
| job_id | string (FK → Job.job_id) | evet | Hangi işe ait |
| sequence_no | int | evet | Job içindeki sıra numarası (1, 2, 3...) — bir önceki operasyon bitmeden bu başlayamaz |
| required_machine_type | string (FK → Machine.machine_type) | evet | Hangi makine tipinde yapılabilir |
| processing_time | float | evet | İşlem süresi (saat). Phase 10'da ML ile tahmin edilecek alan — burada ilk etapta synthetic generator tarafından üretilir |
| energy_consumption | float | evet | Enerji tüketimi (kWh). Phase 12'de ML ile tahmin edilecek alan |

### EnergyPrice

| Alan | Tip | Zorunlu | Açıklama |
|---|---|---|---|
| timestamp | datetime (PK) | evet | Zaman damgası (saatlik çözünürlük) |
| price_per_kwh | float | evet | O saatteki birim enerji fiyatı — gün içinde time-of-use mantığıyla değişir |

### Maintenance

| Alan | Tip | Zorunlu | Açıklama |
|---|---|---|---|
| maintenance_id | string (PK) | evet | Benzersiz bakım kaydı kimliği |
| machine_id | string (FK → Machine.machine_id) | evet | Hangi makine |
| start_time | datetime | evet | Bakım başlangıcı |
| end_time | datetime | evet | Bakım bitişi |
| maintenance_type | enum | evet | `scheduled` \| `emergency` |

---

## İlişkiler (ER Diagram)

```
   Job (1) ───────< (N) Operation
    │                     │
    │ deadline            │ required_machine_type
    │ release_time        ▼
    │              Machine.machine_type  (eşleşme, doğrudan FK değil)
    │                     │
    │                     │
    ▼                     ▼
 [tardiness           Machine (1) ───────< (N) Maintenance
  hesaplaması              │
  Phase 5-6'da]            │ energy_rate
                           ▼
                   EnergyPrice (zaman bazlı, bağımsız tablo —
                   Operation'ın energy_consumption'ı ile
                   optimizasyon aşamasında çarpılarak maliyete dönüşür)
```

Okunuşu:
- Bir **Job**'un birden fazla **Operation**'ı olabilir (1—N), sequence_no ile sıralıdır.
- Bir **Operation**, `required_machine_type` üzerinden bir **Machine** kategorisiyle eşleşir (doğrudan foreign key değil, tip eşleşmesi — çünkü aynı tipten birden fazla makine olabilir, optimizasyon modeli *hangi spesifik makineye* atanacağına karar verecek).
- Bir **Machine**'in birden fazla **Maintenance** kaydı olabilir (1—N).
- **EnergyPrice** zamana bağlı, bağımsız bir tablodur; Operation'ın enerji tüketimi ile çarpılarak maliyete dönüşür (Phase 6, objective function).

---

## Temel İş Kuralları (Business Rules)

Bunlar henüz kısıt (constraint) olarak kodlanmadı — Phase 5'te matematiksel kısıtlara dönüşecekler. Burada sadece veri modeli seviyesinde tutarlılık kuralları olarak not ediliyor:

1. Bir Operation, yalnızca `required_machine_type`'ı kendi `machine_type`'ına eşit olan bir Machine'e atanabilir.
2. Bir Job'un Operation'ları `sequence_no` sırasına göre yapılmalı — 2. operasyon, 1. operasyon bitmeden başlayamaz.
3. Bir Operation, `start_time`'ı atandığı Machine'in bir Maintenance penceresiyle çakışamaz.
4. Bir Operation, atandığı Machine'in `available_from`/`available_until` penceresi dışında başlayamaz/bitemez.
5. Bir Job'un ilk Operation'ı, Job'un `release_time`'ından önce başlayamaz.

---

## Sentetik Veri Notu

Bu veri modeli, Phase 2'de tamamen **sentetik (synthetic)** olarak doldurulacaktır — gerçek bir fabrikaya ait değildir. `EnergyPrice.price_per_kwh` alanının gün içi dalgalanma mantığı, Steel Industry Energy Consumption (UCI #851) datasetindeki gerçek yük örüntülerinden esinlenerek kalibre edilecektir (bkz. [project-plan.md](project-plan.md) Bölüm E). Diğer tüm alanlar kural tabanlı sentetik üretimle doldurulacaktır.

# CLAUDE.md — Bu Projede Çalışma Kuralları

Bu dosya, bu repoda çalışan Claude Code oturumları için kalıcı talimat dosyasıdır. Her oturum başında otomatik okunur.

## Proje

Smart Factory Digital Twin & Optimization — bitirme projesi + öğrenme projesi. Tam kapsam ve yol haritası: [docs/project-plan.md](docs/project-plan.md).

## Zorunlu Çalışma Kuralları

1. **Aşama aşama ilerle.** Yeni bir major phase'e başlamadan önce kullanıcıya şunu anlat: bu aşamada ne yapılıyor, neden yapılıyor, önceki aşamayla bağlantısı ne, hangi kavramları bilmesi gerekiyor, matematiksel taraf ne, kod tarafı ne, aşama sonunda ne elde edilecek. Onaydan/sorudan sonra uygulamaya geç.
2. **Terim açıklama kuralı.** Teknik bir terim ilk kullanıldığında: İngilizce adı, Türkçe karşılığı, basit açıklama, bu projede neden kullanıldığı — birlikte verilir. Sonrasında terim doğrudan kullanılabilir. Terimler [docs/project-plan.md](docs/project-plan.md) Bölüm B'deki tabloya eklenir.
3. **Sonuç uydurma.** Hiçbir performans sayısı (% iyileşme, MAE, solve time vb.) gerçek kod çalıştırılıp ölçülmeden yazılmaz.
4. **Sentetik veri dürüstlüğü.** Veri sentetik olduğu sürece "gerçek fabrikada X oldu" denmez; "sentetik veri setinde X gözlemlendi" denir. Digital Twin gerçek fabrikanın birebir modeli değildir, bu her zaman belirtilir.
5. **Gereksiz karmaşıklık ekleme.** Basit çözüm yeterliyse onu kullan. CV'de iyi görünsün diye teknoloji ekleme. Kullanıcı yanlış/gereksiz karmaşık bir yaklaşım öneriyorsa söyle.
6. **Öncelik sırası:** Correctness > Understanding > Reproducibility > Architecture > Performance > Visual polish.
7. **CHANGELOG.md güncel tutulur.** Aşağıya bak.
8. **Her commit push ile birlikte atılır.** Local commit'ten sonra hemen `git push` yapılır — ayrı onay beklenmez. (2026-08-15'te önce "sadece kullanıcı isteyince pushla" kuralı konmuştu; 2026-08-16'da kullanıcı bunu kaldırıp "her güncellemede push at" dedi — bu kural günceldir.)
9. **docs/decision-log.md güncel tutulur.** Her fazın sonunda kısa bir madde eklenir: o faza girerken öncüller neydi, hangi kararlar verildi (özellikle zor/tartışmalı modelleme kararları) ve gerekçesi, hangi problem çıktı ve nasıl çözüldü. CHANGELOG.md "ne değişti" der, bu dosya "neden böyle karar verildi" der — ikisi farklı amaçlara hizmet eder, biri diğerinin yerine geçmez. (2026-08-15'te kullanıcı tarafından istendi.)
10. **PROJE-OZETI.md güncel tutulur.** Ana klasörde, hiç teknik terim kullanmadan ("mala anlatır gibi") her fazda ne yapıldığını anlatan dosya. Her yeni faz tamamlandığında buraya da 1 bölüm eklenir (CHANGELOG/decision-log'daki teknik detay değil, sade hikaye anlatımı). Kullanıcının projeye ara verip geri döndüğünde önce buraya bakması bekleniyor. (2026-08-16'da kullanıcı tarafından istendi.)

## CHANGELOG.md Kuralı — ÖNEMLİ

Bu projede yapılan her önemli değişiklik (yeni dosya/modül eklendi, bir phase tamamlandı, mimari karar değişti, önemli bir bug fix yapıldı vb.) [CHANGELOG.md](CHANGELOG.md) dosyasına kaydedilir.

- Her oturumda, kullanıcı için anlamlı bir değişiklik yapıldıktan sonra CHANGELOG.md'ye yeni bir madde eklenir (dosyanın en üstüne, en yeni tarih en üstte).
- Format: `## YYYY-MM-DD — Kısa başlık` altında 1-4 madde: ne değişti, neden.
- Sadece kozmetik/geçici değişiklikler (deneme dosyası, typo düzeltme) CHANGELOG'a yazılmaz.
- Bu dosya bitirme projesi raporunun ilerleme kaydı ve "neden bu kararı verdik" belleği olarak da kullanılır.

## Dokümantasyon Yapısı

- `PROJE-OZETI.md` (ana klasörde) — hiç teknik terim yok, faz faz "ne yaptık, niye yaptık, ne oldu" hikayesi. En basit, en hızlı giriş noktası.
- `docs/project-plan.md` — Phase 0 proje tanımı, terminoloji, mimari, yol haritası, dataset stratejisi, riskler.
- `docs/architecture.md` — sistem mimarisi detayları (Phase 22'de ve ilerledikçe doldurulur).
- `docs/mathematical-model.md` — MILP modeli: parametreler, değişkenler, kısıtlar, amaç fonksiyonu (Phase 4-6'da doldurulur).
- `docs/dataset.md` — veri modeli, synthetic generator mantığı, referans alınan gerçek datasetler (Phase 1-2'de doldurulur).
- `docs/experiments.md` — deney tasarımı ve sonuçları (Phase 19-20'de doldurulur).
- `docs/decision-log.md` — her fazın öncülleri, kararları ve karşılaşılan problemleri (kısa, faz faz). CHANGELOG.md'den farklı: o "ne değişti" der, bu "neden böyle karar verildi" der.
- `docs/report/` — bitirme projesi raporu taslakları.

## Teknoloji Stack (özet)

Python, pandas/numpy, scikit-learn (+ gerekirse XGBoost/LightGBM), Pyomo + HiGHS (opsiyonel Gurobi), FastAPI, SQLite (gerekirse PostgreSQL), React veya hafif bir frontend, Plotly. Detay: [docs/project-plan.md](docs/project-plan.md) Bölüm 7.

# Changelog

Bu dosya, projede yapılan önemli değişikliklerin kaydını tutar. En yeni değişiklik en üstte. Format ve güncelleme kuralı için bkz. [CLAUDE.md](CLAUDE.md).

## 2026-08-19 — Phase 12: Enerji tüketimi tahmini (2. ML modeli)

- `ml/training.py` genelleştirildi (`TASKS` sözlüğü, `task` parametresi) — processing_time ve energy_consumption aynı altyapıyı paylaşıyor. `preprocessing/features.py` her iki hedef için de gereken kolonları döndürüyor. `ml/prediction.py`'ye `--task` flag'i eklendi.
- Regresyon kontrolü: Phase 10 sonucu (processing_time) refactor sonrası birebir aynı çıktı.
- **Sonuç**: energy_consumption tahmininde R² 0.93-0.99 (SMALL/MEDIUM/LARGE) — Phase 10'un tam tersi, çünkü `processing_time` feature olarak eklendi (generator'da enerji zaten süreye bağlı üretiliyordu). Bu sefer Random Forest/Gradient Boosting, Linear Regression'ı gerçekten geçti — çarpımsal (süre × makine-tipi-oranı) etkileşimi ağaç modelleri daha iyi yakalıyor.
- Phase 10 vs Phase 12 karşılaştırması `docs/decision-log.md`'ye "ne zaman ML işe yarar" dengeli örneği olarak eklendi.

## 2026-08-19 — Phase 11: Predict→Optimize + kritik warm-start hatası düzeltildi

- `optimization/replay.py` eklendi: sabit atama+sıra kararını verilen süre kaynağıyla yeniden zamanlayan ortak yardımcı (hem warm-start hem Predict→Optimize replay'i kullanıyor).
- `ml/predict_optimize.py` eklendi: ML tahmin eder → optimize eder → GERÇEK sürelerle yeniden değerlendirir.
- **Kritik hata bulundu/düzeltildi**: `optimization/warmstart.py`'nin Phase 11 için yeniden yazılan versiyonu, `replay_schedule`'da bakım pencerelerini hesaba katmıyordu — bu, SMALL+Stage"final"de warm-start'ın infeasible sayılıp reddedilmesine yol açtı (Phase 7'deki soruna geri dönüş riski). `build_maintenance_lookup` ile düzeltildi, minik örnek + SMALL yeniden doğrulandı.
- **Yan fayda**: Düzeltme, Phase 9'un SMALL sonucunu da iyileştirdi (%5.22 → %10.67) — warm-start artık düzgün kabul ediliyor. `docs/experiments.md` güncellendi.
- `optimization/native_solver.py`: ikili/tamsayı değişkenler artık yuvarlanıyor, gürültülü Pyomo domain uyarıları temizlendi.
- **Phase 11 sonucu**: ML tahmin hatası nedeniyle, teorik maksimum iyileşmenin (%10.67) sadece %40.85'i yakalanabildi (%4.36). `docs/decision-log.md` ve `docs/experiments.md`'ye detaylı yazıldı.

## 2026-08-18 — Phase 10: ML işlem süresi tahmini

- `preprocessing/features.py`: operations+jobs join, feature tablosu (Machine tablosundan bilerek join yapılmadı — spesifik makine ataması henüz yok).
- `ml/training.py`: Linear Regression / Random Forest / Gradient Boosting, ortak ColumnTransformer ön-işleme, SEED=42 train/test split.
- `ml/evaluation.py`: MAE/RMSE/R².
- `ml/prediction.py`: orkestratör, en iyi modeli `ml/models/`'e kaydediyor.
- **SMALL/MEDIUM/LARGE'da çalıştırıldı**: R² 0.24-0.64 arası — beklediğimin (çok yüksek R²) tam tersi çıktı, düzeltildi. Kök neden: generator'da `base_time` her operasyon için feature'lardan bağımsız rastgele çekiliyor (irreducible noise). Random Forest/Gradient Boosting, Linear Regression'ı çoğunlukla geçemedi — ayarlanmamış ağaç modellerinin küçük/gürültülü veride overfit etmesi.
- `docs/decision-log.md`'ye detaylı yazıldı.

## 2026-08-17 — PROJE-OZETI.md eklendi

- Yeni dosya (ana klasörde): `PROJE-OZETI.md` — Phase 0-9'u hiç teknik terim kullanmadan, hikaye anlatır gibi özetliyor. Kullanıcının "en son nerede kaldık" diye hızlıca hatırlaması için.
- `README.md` ve `CLAUDE.md` bu dosyaya referans verecek şekilde güncellendi; `CLAUDE.md`'ye kural 10 eklendi (her faz sonunda bu dosya da güncellenecek).

## 2026-08-16 — Phase 9: Baseline vs Optimized karşılaştırması

- `optimization/comparison.py` eklendi: FCFS/EDF/Optimized'ı aynı metriklerle (`baseline/metrics.py::summarize`) ve aynı $ formülüyle (`compute_total_cost`) kıyaslıyor.
- **SMALL sonucu**: Optimized, FCFS'e göre toplam maliyette **%5.22 iyileşme** ($13051.72 → $12370.73, solver gap %10.42). Enerji maliyeti %21 düştü ama production time ve late job sayısı arttı — dürüstçe raporlandı, model toplamı minimize ediyor tek tek metrikleri değil.
- Optimize edilmiş planın fiziksel geçerliliği ayrıca doğrulandı (0 hata, 162/162 operasyon).
- **Reproducibility notu eklendi**: solver'ın time-limit'e dayalı sonucu, veri üretiminin aksine tam deterministik değil — bu ayrım `docs/experiments.md`'ye işlendi.
- Sonuçlar `experiments/results/comparison_small.json` ve `optimized_schedule_small.csv`'ye kaydedildi (gitignore'da, script ile yeniden üretilebilir).
- `docs/experiments.md` ve `docs/decision-log.md` güncellendi.

## 2026-08-16 — Phase 8: MEDIUM ölçek doğrulaması

- Stage "makespan", warm-start, 60 sn: `Cmax=147.45` (baseline: 147.45), gap %0.21 — MEDIUM'da da baseline optimale çok yakın, SMALL bulgusuyla tutarlı.
- **Phase 8 tamamen kapatıldı.** Sonuç netleşti: baseline makespan'de zaten (neredeyse) optimal; asıl optimizasyon değeri "final" (birleşik $) hedefte. Bu, Phase 9'un tasarımını etkiliyor — makespan-only karşılaştırma anlamsız kalır, "final" hedefle karşılaştırma yapılmalı.

## 2026-08-16 — Phase 8 TAMAMLANDI: Native highspy warm-start

- `optimization/native_solver.py` eklendi: Pyomo'yu sadece model kurmak için kullanıp, çözümü appsi'yi bypass ederek doğrudan `highspy`'a devrediyor (appsi bu ortamda hem "çözüm yok" hem warm-start senaryosunda güvenilmez çıktığı için). Pyomo `SymbolMap` ile MPS↔Pyomo değişken eşlemesi kuruluyor.
- `optimization/solver.py`'ye `solve_with_warm_start()` eklendi — Phase 9+ için önerilen tek çağrılık arayüz.
- Doğruluk yeniden kanıtlandı (minik örnek, warm-start'lı/warm-start'sız aynı optimal sonuç).
- **SMALL, Stage "makespan"**: 300+ sn → **0.34 sn**. Baseline'ın (144.31h) zaten kanıtlanmış optimal olduğu gösterildi (Gap %0) — sistem hafif yüklü olduğu için beklenen bir sonuç, model doğruluğunun bağımsız kanıtı.
- **SMALL, Stage "final" ($ birleşik hedef)**: 120 sn'de baseline'a göre **%6.0 maliyet iyileştirildi** ($13,051.72 → $12,263.83, gap %10.4). Optimizasyonun baseline'ın göremediği enerji/tardiness boyutlarında gerçek değer kattığının ilk somut kanıtı.
- `docs/decision-log.md` detaylı güncellendi. **Push kuralı artık her commit'le birlikte otomatik.**

## 2026-08-16 — Phase 8: Warm-start denendi (appsi güvenilmez çıktı) + süre testi

- `optimization/warmstart.py` eklendi: baseline planını MILP'in tüm değişkenlerinin (x,S,C,y,z,w,T,Cmax) başlangıç değerlerine çeviriyor. Çeviri doğru çalıştığı doğrulandı (başlangıç Cmax=144.31, baseline ile birebir).
- **appsi_highs + warmstart=True denendi, yine donuk kaldı** (45 sn'de çıktı yok) — appsi'nin bu ortamda genel olarak güvenilmez olduğu netleşti (sadece "çözüm yok" durumunda değil).
- Alternatif olarak warm-start olmadan, güvenilir arayüzle 300 saniye (config varsayılanı) test edildi: `Cmax=161.72h` — 60 sn'deki 165.70h'ye göre yalnızca %2.4 iyileşme, hâlâ baseline'ın (144.31h) gerisinde. **Sonuç: salt süre artışı çözüm değil, gerçekten warm-start gerekiyor.**
- Native-highspy tabanlı warm-start (appsi'yi bypass eden, daha sağlam bir yol) bir sonraki adım olarak `docs/decision-log.md`'ye not düşüldü, bu oturumda tamamlanmadı.
- **Phase 8 bu oturum için kısmen tamamlandı**: Big-M sıkılaştırması kalıcı bir kazanç (kod ve dokümanlara işlendi); SMALL artık feasible çözüm buluyor ama baseline'ı henüz geçemiyor.

## 2026-08-16 — Phase 8: Big-M ispatlanabilir şekilde sıkılaştırıldı (336 → 168)

- `optimization/variables.py`: `S[o]/C[o]`'ya sert sınır `[0, horizon_hours]` eklendi (C1+C8'in zaten örtük garantisi, feasible çözüm elenmiyor).
- `config/config.yaml`: `big_m: 336 → 168` — matematiksel olarak türetildi (bkz. `docs/mathematical-model.md` Bölüm 5), tahmin değil.
- Doğruluk önce yeniden test edildi (minik örnek, sonuçlar birebir aynı), sonra SMALL'da denendi: eskiden 60 sn'de feasible çözüm YOK, şimdi 6. saniyede bulundu, 60 sn'de gap %12.91'e indi.
- **Yeni bulgu**: solver'ın 60 sn'de bulduğu en iyi çözüm (165.70h) hâlâ baseline FCFS'ten (144.31h) kötü; dual bound (144.31) baseline'a birebir eşit — gerçek optimalin baseline'a çok yakın olabileceğine işaret ediyor. Warm-start için güçlü bir gerekçe oluştu.
- `docs/mathematical-model.md` ve `docs/decision-log.md` güncellendi.

## 2026-08-16 — Phase 7: Pyomo implementasyonu + kritik solver hatası bulundu/düzeltildi

- `optimization/{variables,constraints,objective,solver,results,model}.py` yazıldı — Phase 4-6'daki matematiksel model birebir kodlandı.
- **Bulunan hata**: `appsi_highs` (Pyomo/HiGHS arayüzü), solver time-limit'e ulaşıp feasible çözüm bulamadığında sessizce sonsuza kadar takılı kalıyor (~115 dk boşa CPU harcandı, süreç öldürüldü). Kök neden native `highspy` ve Pyomo'nun yeni `SolverFactory('highs')` arayüzüyle karşılaştırılarak izole edildi — ikisi de doğru çalışıyor. `solver.py`, yeni arayüze + `load_solutions=False` + kontrollü `has_feasible_solution()` kontrolüne geçirildi.
- **Doğruluk kanıtlandı**: elle kurulmuş minik örnekte (2 makine, 2 job) Stage "makespan" optimal `Cmax=2.5` (elle hesapla birebir aynı), Stage "energy" solver'ı ucuz saatlere kaydırıp maliyeti teorik minimuma indirdi (`w[o,t]` mekanizması doğru çalışıyor).
- **Performans bulgusu (gizlenmedi)**: gerçek SMALL veri setinde (162 operasyon) Stage "makespan" 60 saniyede tek bir feasible çözüm bile bulamadı — Big-M disjunctive job-shop MILP'lerin bilinen bir zorluğu, kod hatası değil. Bu, planlandığı gibi Phase 8'in (solver tuning, warm-start) konusu olarak bırakıldı.
- `docs/decision-log.md`'ye tüm hata ayıklama süreci (appsi bug'ının nasıl izole edildiği) detaylı yazıldı.

## 2026-08-15 — Phase 6: Matematiksel model — amaç fonksiyonu (tamamlandı)

- `docs/mathematical-model.md`'ye amaç fonksiyonu eklendi: enerji maliyeti teriminin doğrusallaştırılması (`w[o,t]` saatlik linking değişkeni), aşamalı test planı (Stage 1 C_max / Stage 2 EnergyCost / Stage 3 tardiness / Final birleşik), ve birleşik `Z = α·C_max + EnergyCost + γ·Σ T[j]` formülü.
- **Önemli düzeltme**: İlk planlanan "3-4 fiyat bloğu" yaklaşımı, Phase 2'nin saat başına gürültülü fiyat ürettiğini fark edince terk edildi — baseline ile tutarlılık için saatlik çözünürlüğe (168 blok) geçildi. Bedeli (LARGE'da ~545.000 ek ikili değişken) gizlenmeden not edildi, Phase 8/20'de gözlemlenecek.
- Ağırlıklar (α/β/γ) rastgele seçilmedi: $ cinsine çevrildi (`c_time=50`, enerji zaten $, `c_tardy=100`) — `config/config.yaml`'a yazıldı, açıkça "varsayım" olarak işaretlendi, Phase 19-20'de duyarlılık analizi planlandı.
- **Matematiksel model (Phase 4-6) tamamlandı.** Sıradaki adım Phase 7: Pyomo implementasyonu.
- `docs/decision-log.md` ve `CLAUDE.md` (kural 9 + docs listesi) güncellendi.

## 2026-08-15 — docs/decision-log.md oluşturuldu

- Yeni dosya: `docs/decision-log.md` — CHANGELOG.md'den farklı olarak "ne değişti" değil, "neden böyle karar verildi" sorusuna cevap veriyor. Her faz için: öncüller, kararlar (gerekçesiyle), karşılaşılan problem/çözüm.
- Phase 0'dan Phase 5'e kadar (+ repo kurulumu, git push onay kuralı) geriye dönük dolduruldu — özellikle C5 kapasite modelleme kararı ve EDF/FCFS bulgusu gibi "zor" kararlar detaylandırıldı.
- `CLAUDE.md`'ye kural 9 eklendi: her faz sonunda bu dosya da güncellenecek.

## 2026-08-15 — Kural değişikliği: git push artık manuel onaylı

- `CLAUDE.md`'ye kural eklendi: local commit'ler her zamanki gibi her önemli değişiklikten sonra atılıyor, ama `git push` artık kullanıcı açıkça "pushla" demeden çalıştırılmıyor.
- Bu commit'ten itibaren local'de birikip GitHub'a gitmemiş commit'ler olabilir — kullanıcı "pushla" dediğinde hepsi tek seferde gönderilecek.

## 2026-08-15 — Phase 5: Matematiksel model — kısıtlar (constraints)

- `docs/mathematical-model.md`'ye 8 kısıt eklendi: C1 atama, C2 job-içi sıralama, C3 makine çakışmaması (Big-M + `y[o,o']`), C4 bakım çakışmaması (Big-M + `z[o,k]`), C5 kapasite, C6 release time, C7 tardiness doğrusallaştırma, C8 makine çalışma zamanı sınırı. Ayrıca makespan tanımlayıcı kısıtı (`C_max ≥ C[o]`) eklendi.
- **Önemli modelleme kararı — C5 (kapasite)**: ayrı bir MILP eşitsizliği olarak değil, `M_o` kümesinin tanımına giren bir uygunluk (eligibility) filtresi olarak modellendi. Gerekçe: `Job.quantity`'nin etkisi Phase 2'de zaten `processing_time`'a gömüldü (`quantity_factor`); ayrı bir kapasite eşitsizliği eklemek bu etkiyi iki kez saymak olurdu. Kullanıcıya açıkça belirtildi ve onaylandı.
- Big-M seçimi için not eklendi: `BigM = 2 × horizon_hours = 336`, Phase 8'de solver performansı zorlanırsa sıkılaştırma değerlendirilecek.
- Sıradaki adım Phase 6 (amaç fonksiyonu) — bu dosyada "Planlanan İçerik" olarak işaretli, henüz yazılmadı.

**Genel not**: Bundan sonraki her önemli güncellemede CLAUDE.md'deki kural gereği bu dosya (CHANGELOG.md) düzenli güncellenecek — kullanıcı projeye ne zaman dönerse dönsün "en son nerede kaldık" sorusunun cevabı burada olacak.

## 2026-08-15 — Phase 4: Matematiksel model — index kümeleri, parametreler, karar değişkenleri

- `docs/mathematical-model.md` yazıldı: `J/O/O_j/M/M_o` index kümeleri; 7 parametre grubu; 5 karar değişkeni tipi (`x[o,m]` atama, `S[o]/C[o]` zamanlama, `y[o,o']` sıralama, `T[j]` tardiness, `C_max` makespan).
- Yapısal gözlem belgelendi: ürün şablonlarında bir job içinde makine tipi tekrar etmediği için `y[o,o']` sıralama değişkeni yalnızca farklı job'lara ait operasyonlar arasında anlamlı — aynı job'un kendi operasyonları hiçbir zaman aynı makineye "yarışmıyor".
- Somut sayısal örnek eklendi (2 job, paylaşılan tek Packaging makinesi) — `baseline/scheduler.py`'nin greedy olarak elle yaptığı seçimin, optimizasyonda `x/y/S/C` değişkenleri üzerinden solver'a bırakılacağını gösteriyor.
- Henüz kısıt (Phase 5) ve amaç fonksiyonu (Phase 6) yazılmadı — bu dosyada "Planlanan İçerik" olarak işaretli.

## 2026-08-15 — Phase 3: Baseline System (FCFS/EDF)

- `baseline/scheduler.py`: greedy FCFS ve EDF üretim planlayıcı. Job içi operasyon sırasını ve makine bakım pencerelerini kontrol ediyor; `available_from/until` şimdilik zorlanmıyor (mevcut veride bilgi taşımıyor, Phase 5'te gerçek kısıt olacak).
- `baseline/metrics.py`: makespan, tardiness, enerji maliyeti, makine kullanım oranı hesaplama — bu fonksiyonlar Phase 9'da optimize edilmiş planla karşılaştırmada da aynen kullanılacak.
- Doğrulama: SMALL/MEDIUM/LARGE'da hatasız çalıştı (LARGE: 1000 job, ~0.9 saniye); üretilen planda makine çakışması yok, operasyon sırası ihlali yok, bakım çakışması yok (814/814 operasyon MEDIUM'da doğru planlandı).
- Gözlem: EDF, FCFS'ten daha fazla geciken iş üretti (SMALL'da 7 vs 3) — paylaşılan darboğaz makine (Assembly, tek makine) nedeniyle beklenen, literatürle tutarlı bir sonuç; uydurulmadı, `docs/experiments.md`'ye kaydedildi.
- `docs/experiments.md` ilk gerçek gözlemlerle dolduruldu (resmi deneyler Phase 19'da).


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

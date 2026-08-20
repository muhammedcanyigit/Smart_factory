# Decision Log (Karar Günlüğü)

Bu dosya CHANGELOG.md'den farklı bir amaca hizmet eder: CHANGELOG "hangi dosya değişti" der, bu dosya **"neden bu şekilde karar verildi, o fazda hangi öncüller vardı, hangi problem çıktı ve nasıl çözüldü"** sorusuna cevap verir. Bitirme projesi raporunun Discussion/Limitations bölümleri doğrudan buradan beslenecek.

Her fazın sonunda kısa bir madde eklenir: **Öncüller** (o faza girerken varsayılanlar) → **Kararlar** (verilenler ve gerekçesi) → **Karşılaşılan Problem / Çözüm** (varsa).

---

## Repo Kurulumu (Phase 0 sonrası, ayrı bir olay)

- **Öncül**: Proje `Smart_factory` klasöründe, henüz git deposu değil.
- **Problem**: Klasör, kullanıcının ev dizinine (home directory) ait, bambaşka bir kişinin projesine (`muhammedgaziguzel/Tarim-Projesi`) bağlı, kazara git ile izlenen bir reponun içinde kalmıştı.
- **Çözüm**: O dış repoya dokunulmadı; `Smart_factory` içinde bağımsız yeni bir `git init` yapıldı, GitHub'daki `muhammedcanyigit/Smart_factory` reposuna `origin` olarak bağlandı.
- **Problem 2**: GitHub'da oluşturulan repo boş değildi (otomatik tek satırlık README ile gelmişti); ilk `git push` "fetch first" hatasıyla reddedildi.
- **Çözüm 2**: `git fetch` + `git merge --allow-unrelated-histories`; README.md çakışması, bizim detaylı içerik lehine çözüldü.

## Phase 0 — Proje Tanımı

- **Öncül**: Gerçek fabrika verisine erişim yok; projeye "karar destek sistemi" (fabrikanın yerine karar vermez, alternatif sunar) olarak çerçeve çizildi.
- **Karar**: Öncelik sırası `Correctness > Understanding > Reproducibility > Architecture > Performance > Visual polish` olarak benimsendi — sonraki tüm fazlarda bu sıraya göre karar verildi.
- **Problem**: Web araştırmasında makine+iş+enerji+bakım hepsini içeren **birleşik** bir gerçek dataset bulunamadı.
- **Çözüm**: Üç parça gerçek dataset (Steel Industry Energy Consumption UCI#851, AI4I 2020 Predictive Maintenance UCI#601, Taillard/Hurink/Brandimarte job-shop benchmark instance'ları) **kalibrasyon/doğrulama referansı** olarak seçildi; ana veri kaynağının synthetic generator olacağına karar verildi.

## Phase 1 — Data Model

- **Öncül**: Phase 0'daki taslak alan listeleri (Machine/Job/Operation/EnergyPrice/Maintenance) temel alındı.
- **Karar**: Operation'a `sequence_no` eklendi (job içi sıralama kısıtını ifade edebilmek için gerekliydi); Maintenance'a `maintenance_id` primary key eklendi. Kullanıcı taslağı büyük ölçüde onayladı, itiraz gelmedi.

## Phase 2 — Synthetic Data Generator

- **Öncül**: `SEED=42` ile deterministik üretim; Phase 0'da tanımlanan ilişkiler (süre→enerji, yaş→arıza) korunacak.
- **Karar (önemli)**: `Operation.processing_time`/`energy_consumption`, spesifik bir makineye değil, `required_machine_type`'ın **ortalama** makinesine göre üretiliyor (nominal değer) — çünkü üretim anında operasyonun hangi spesifik makineye gideceği henüz belli değil; gerçek süre, atanan makinenin `efficiency`'sine göre sonraki fazlarda ölçekleniyor.
- **Karar**: `datetime.now()` yerine sabit `HORIZON_START = 2026-01-05` kullanıldı — aksi halde her çalıştırmada farklı tarih üretilip reproducibility bozulurdu.
- **Problem**: Yok — ama "çalışıyor" demeden önce 3 doğrulama yapıldı: iki çalıştırmanın birebir aynı çıktıyı verdiği, süre-enerji korelasyonunun (0.82) gerçekten pozitif olduğu, her makine tipinin en az bir makinesi olduğu.

## Phase 3 — Baseline System

- **Öncül**: FCFS/EDF greedy (açgözlü) mantıkla kurulacak; maintenance'a saygılı olacak.
- **Karar**: `available_from/until` penceresi bu fazda zorlanmadı — mevcut veride tüm makinelerde aynı ve bilgi taşımıyordu; C8 kısıtıyla (Phase 5) matematiksel modelde zaten ele alınacaktı.
- **Problem**: EDF, FCFS'ten daha fazla geciken iş üretti (SMALL'da 7 vs 3) — ilk bakışta hatalıymış gibi göründü.
- **Çözüm**: Kod hatası değil, gerçek bir OR (Operations Research) fenomeni olduğu araştırılıp doğrulandı: EDF yalnızca tek-makineli/release-time'sız ortamlarda maksimum gecikmeyi garantili minimize eder; bu projede paylaşılan darboğaz makineler (SMALL'da tek Assembly/Packaging makinesi) bu garantiyi geçersiz kılıyor. `docs/experiments.md`'ye kaydedildi.
- **Ek analiz**: Kullanıcı "büyük veride fark azalır mı, çünkü çakışma azalır" hipotezini sordu. MEDIUM/LARGE'da test edildi: fark gerçekten sıfıra indi, ama kullanıcının önerdiği mekanizma (çakışma azalır) **yanlıştı** — makine kullanım oranı büyüdükçe aslında artıyordu (0.12→0.44). Gerçek mekanizma: darboğaz makine sayısı arttıkça (Assembly 1→6→14) tek-nokta darboğaz ortadan kalkıyor, sıralamanın etkisi paralel makineler arasında sönümleniyor. Tek seed'lik gözlem olduğu, istatistiksel olarak kanıtlanmadığı not edildi (Phase 19-20'nin işi).

## Phase 4 — Decision Variables & Parameters

- **Öncül**: Phase 1 veri modeli + Phase 0 kavramsal tanım.
- **Karar**: 6 karar değişkeni tipi tanımlandı (`x, S, C, y, T, C_max`).
- **Yapısal gözlem**: Ürün şablonlarında bir job içinde makine tipi tekrar etmediği için `y[o,o']` sıralama değişkeni yalnızca **farklı job'lara ait** operasyonlar arasında gerekli — bu, Phase 5'teki kısıt sayısını gereksiz şişirmedi.
- **Problem**: Yok, doğrudan onaylandı.

## Phase 5 — Constraints

- **Öncül**: Phase 4 değişkenleri + Big-M yöntemi.
- **Karar (zor modelleme kararı — C5, kapasite)**: Kapasite ayrı bir MILP eşitsizliği olarak değil, `M_o` kümesinin tanımına giren bir **uygunluk (eligibility) filtresi** olarak modellendi. Gerekçe: `Job.quantity`'nin etkisi Phase 2'de zaten `processing_time`'a gömülmüştü (`quantity_factor`); ayrı bir "kapasite × süre ≥ miktar" eşitsizliği eklemek bu etkiyi iki kez saymak olurdu. Kullanıcıya açıkça sunuldu, onaylandı.
- **Karar**: `BigM = 2 × horizon_hours = 336` seçildi; Phase 8'de solver zorlanırsa sıkılaştırma değerlendirilecek.

## Workflow Kararı — Git Push Onayı

- **Karar**: Kullanıcı, `git push`'un yalnızca kendisi açıkça istediğinde yapılmasını talep etti (local commit'ler ve CHANGELOG güncellemeleri normal akışta devam ediyor). `CLAUDE.md`'ye kalıcı kural olarak eklendi.

## Phase 6 — Objective Function

- **Öncül**: Enerji maliyeti teriminin, baseline ile **tutarlı** (aynı ölçekte kıyaslanabilir) olması gerekiyordu.
- **Karar**: Enerji maliyeti, baseline'daki gibi operasyonun **başlangıç saatindeki** birim fiyat kullanılarak hesaplanacak. Kullanıcı onayladı.
- **Problem (kendi kendime fark ettim, kullanıcıya bildirdim)**: `EnergyPrice`'ın Phase 2'de saat başına gürültülü (`rng.normal`) üretildiğini hatırladım — yani fiyat sadece 3-4 kategoriye ayrılmıyor, 168 saatin her biri gerçekte farklı. İlk aklıma gelen "fiyat bloğu" (peak/off-peak/normal, ~28 blok) yaklaşımı bu gürültüyü görmezden gelip baseline'dan sapacaktı — tam da "tutarlı olsun" isteğini bozacaktı.
- **Çözüm**: MILP'te de saatlik çözünürlük (`w[o,t]`, t=0..167) kullanmaya karar verildi — baseline ile birebir aynı `EnergyPrice` tablosunu, aynı çözünürlükte okuyor. Bedeli: operasyon başına 168 ikili değişken (LARGE'da ~545.000). Bu gizlenmedi; Phase 8'de solver performansı ölçülecek, gerekirse (a) EnergyPrice'ı gürültüsüz/bloklu yeniden üretmek (her iki tarafı da güncelleyerek tutarlılığı koruyarak) ya da (b) decomposition/sezgisel yaklaşıma geçmek seçenekleri var — şimdiden karar verilmedi, Phase 20 stress test'in konusu.
- **Karar (ağırlıklar)**: α/β/γ rastgele seçilmedi — hepsi $ cinsine çevrildi (`c_time=50 $/saat`, enerji zaten $, `c_tardy=100 $/saat`). Bu sayılar gerçek fabrika ölçümü değil, açıkça belirtilmiş **varsayım**; Phase 19-20'de ±%50 duyarlılık analizi yapılacak. `config/config.yaml`'a yazıldı.

## Phase 7 — Pyomo Implementation

- **Öncül**: Phase 4-6'daki matematiksel model (`x,S,C,y,T,Cmax,w` + C1-C8 + Z) birebir Pyomo koduna dökülecekti; `optimization/{variables,constraints,objective,solver,results,model}.py` olarak modülerize edildi.
- **Kritik hata (bulundu, düzeltildi)**: İlk yazımda solver için `pyo.SolverFactory('appsi_highs')` kullanıldı. SMALL veri setinde (162 operasyon) modeli çözerken süreç **115+ dakika** boyunca hiç çıktı vermeden takılı kaldı — verilen `time_limit`'in hiçbir etkisi yokmuş gibi göründü. Süreç öldürülüp kök neden araştırıldı:
  1. Native `highspy` ile aynı model (.mps olarak dışa aktarılıp) test edildi — `time_limit` orada birebir doğru çalıştı (8.01 sn'de düzgün durdu). Demek ki HiGHS'in kendisi sorunlu değil.
  2. Pyomo'nun **yeni** `pyomo.contrib.solver` tabanlı `SolverFactory('highs')` arayüzü denendi — aynı model, aynı süre: 8.03 sn'de düzgün durdu, üstelik "uygun çözüm yok" durumunda temiz bir `NoFeasibleSolutionError` fırlattı.
  3. Sonuç: **`appsi_highs` arayüzünün, solver zaman sınırına ulaşıp hiçbir feasible çözüm bulamadığı durumda sessizce sonsuza kadar takılı kalan bir hatası var** (bu ortamdaki Pyomo 6.10.1 + highspy sürüm kombinasyonunda). Bu, kodumuzun mantık hatası değil, üçüncü parti kütüphane entegrasyon hatasıydı.
  - **Çözüm**: `optimization/solver.py`, `appsi_highs` yerine `SolverFactory('highs')` (yeni arayüz) kullanacak şekilde değiştirildi; `load_solutions=False` + `raise_exception_on_nonoptimal_result=False` ile "çözüm yok" durumu artık hem donmuyor hem de exception fırlatmıyor, kontrollü şekilde `has_feasible_solution()` ile kontrol edilebiliyor.
- **Doğrulama (Correctness > Performance önceliği gereği önce bu yapıldı)**: 2 makine (1 CNC + 1 Packaging), 2 job'luk elle kurulmuş minik bir örnekte:
  - Stage "makespan": solver optimal olarak `Cmax=2.5` saat buldu — elle hesapla birebir aynı (iki job'un da aynı iki makineyi sırayla kullanması gereken klasik 2-makine akış tipi zamanlama problemi).
  - Stage "energy": ilk 5 saati pahalı (fiyat=10), sonrasını ucuz (fiyat=1) yapan bir test fiyat eğrisiyle, solver **tüm operasyonları ucuz döneme kaydırdı**, toplam maliyeti teorik minimuma (25.0 = 25kWh×1.0) indirdi — `w[o,t]` linking mekanizmasının doğru çalıştığı kanıtlandı.
  - **Sonuç: model mantıksal olarak doğru.**
- **Problem (performans, gizlenmedi)**: Gerçek SMALL veri setinde (162 operasyon, 3221 binary değişken, 10396 kısıt, Stage "makespan") solver **60 saniyede, 2056 dal-sınır düğümü denemesine rağmen tek bir feasible çözüm bile bulamadı** (Primal bound: inf, Dual bound: 144.31). Bu, kötü kod değil — Big-M tabanlı disjunctive job-shop MILP formülasyonlarının literatürde bilinen, gerçek bir zorluğu (NP-hard problem + gevşek Big-M → zayıf LP relaxation → generic MIP sezgisellerinin feasible nokta bulmakta zorlanması).
- **Karar (ertelendi, bilinçli)**: SMALL ölçekte performansı iyileştirmek (ör. baseline'dan warm-start vermek, Big-M'i sıkılaştırmak, veya solver'a daha fazla süre tanımak) **Phase 8'in (Solver) konusu** — zaten planlanmıştı, atlanmadı. Phase 7'nin görevi "model doğru mu" sorusuna cevap vermekti, o cevaplandı.

## Phase 8 — Solver (Big-M Sıkılaştırma, 1. deneme)

- **Öncül**: Kullanıcıya iki seçenek sunuldu (warm-start vs Big-M sıkılaştırma), kullanıcı Big-M sıkılaştırmayı seçti ama riskini fark etti: "yanlış küçük M, sessizce absürt/yanlış sonuç verebilir." Bu riski gidermek için sıkılaştırmanın **tahmin değil, ispat** olması istendi.
- **Karar**: `S[o]/C[o]`'ya sert değişken sınırı `[0, horizon_hours]` eklendi (C1+C8'in zaten örtük garantisi — feasible çözüm elenmiyor). Buna dayanarak C3/C4/w-linking için `BigM = horizon_hours = 168` (eskiden `336`) matematiksel olarak türetildi (bkz. `docs/mathematical-model.md` Bölüm 5, "Big-M Seçimi Üzerine Not").
- **Doğrulama sırası (Correctness önce)**: Değişiklikten hemen sonra, önce minik elle-doğrulanabilir örnek (Phase 7'deki) tekrar çalıştırıldı — `Cmax=2.5` ve `EnergyCost=25.0` **birebir aynı** çıktı, sıkılaştırma doğruluğu bozmadı. Ancak sonra SMALL'da test edildi.
- **Sonuç (SMALL, Stage "makespan", 60 sn)**: Dramatik iyileşme — eskiden (M=336) 60 saniyede tek feasible çözüm bulunamıyordu; yenisinde (M=168) **6. saniyede** ilk feasible çözüm bulundu, 60. saniyede `Cmax=165.70h`, gap %12.91'e indi (dual bound sabit: 144.31).
- **Yeni bulgu (gizlenmedi)**: Solver'ın 60 saniyede bulduğu en iyi çözüm (165.70h), Phase 3'teki basit FCFS baseline'ından (144.31h) hâlâ **daha kötü**. Dual bound'un (144.31) baseline değeriyle bire bir aynı çıkması, gerçek optimalin baseline'a çok yakın (belki de baseline kadar iyi) olabileceğini düşündürüyor — ama solver bunu sıfırdan aramakla 60 saniyede bulamıyor. Bu, warm-start'ın (baseline'ı başlangıç çözümü verme) neden mantıklı bir sonraki adım olduğunu somut veriyle gösteriyor.

## Phase 8 — Solver (Warm-Start Denemesi)

- **Öncül**: Big-M sıkılaştırmasının ortaya çıkardığı bulgu (solver baseline'ı 60 sn'de yakalayamıyor) ışığında, `baseline/scheduler.py`'nin ürettiği FCFS planını solver'a başlangıç çözümü (warm start) olarak vermeye karar verildi.
- **Uygulama**: `optimization/warmstart.py` yazıldı — baseline schedule'ı `x[o,m], S[o], C[o], y[o,o'], z[o,k], w[o,t], T[j], Cmax` değişkenlerinin başlangıç değerlerine çeviriyor. Baseline'ın Phase 3'te tüm kısıtları (C1-C8) sağladığı zaten doğrulanmıştı, bu yüzden warm start olarak güvenli.
- **Problem**: Warm-start'ı uygulamak için `appsi_highs`'ın `config.warmstart=True` özelliği denendi (bu, Pyomo arayüzleri arasında warm-start destekleyen tek seçenekti — yeni `SolverFactory('highs')` arayüzünde warm-start desteği YOK, kaynak kodu incelenerek doğrulandı). Warm start değerleri doğru uygulandı (başlangıç `Cmax=144.31`, baseline ile birebir eşleşti — çeviri mantığı doğru çalıştığının kanıtı) ama **`appsi_highs` yine donuk kaldı** (45 saniyede hiç çıktı yok, Phase 7'deki hatayla aynı aile).
- **Karar**: `appsi_highs`, bu ortamda (Pyomo 6.10.1 + highspy) genel olarak güvenilmez olarak işaretlendi — sadece "çözüm yok" durumunda değil, warm-start senaryosunda da sorunlu. Şu an için (a) warm-start'ı native `highspy` ile (Pyomo'yu sadece model kurmak için kullanıp, MPS + sembolik etiketlerle çözümü doğrudan highspy'a vermek) uygulamak mümkün ama belirgin ek mühendislik gerektiriyor; (b) alternatif olarak, warm-start olmadan sadece daha fazla solve süresi (300 sn, config'teki varsayılan) denendi — sonuç aşağıda.
- **Ertelenen iş (gelecek referans için)**: Native highspy tabanlı warm-start uygulaması, performans çalışmasına devam edilmek istenirse (Phase 20 stress test veya daha erken) hazır bir sonraki adım olarak burada not düşülüyor — appsi güvenilmezliği nedeniyle bu oturumda tamamlanmadı.
- **(b) sonucu — sadece daha fazla süre (warm-start yok, güvenilir arayüz, 300 sn)**: `Cmax = 161.72h`. 60 saniyedeki `165.70h`'ye göre yalnızca **%2.4 iyileşme** — süreyi 5 katına çıkarmak neredeyse hiçbir işe yaramadı, hâlâ baseline'ın (144.31h) belirgin şekilde gerisinde. **Yorum**: bu, sorunun "solver'a az zaman verdik" değil, "arama sıfırdan başladığı için zayıf bölgelerde kayboluyor" olduğunu doğruluyor — yani gerçekten warm-start (veya eşdeğer bir yönlendirme) gerekiyor, salt zaman artışı çözüm değil.
- **Genel Phase 8 sonucu (bu oturum için)**: Big-M sıkılaştırması kalıcı, doğrulanmış, net bir kazanç olarak koda işlendi. Warm-start'ın native-highspy versiyonu bir sonraki performans çalışmasına bırakıldı. Bu oturumda Phase 8 "kısmen tamamlandı" olarak işaretleniyor — SMALL artık feasible çözüm buluyor ama baseline'ı henüz geçemiyor.

## Phase 8 — Solver (Native Highspy Warm-Start, TAMAMLANDI)

- **Öncül**: Kullanıcı "Seçenek 1 (warm-start) ile devam edelim, şimdi halledelim" dedi. `appsi_highs` bu ortamda genel olarak güvenilmez olduğu için (Phase 7 + önceki deneme), warm-start'ı **appsi'yi tamamen bypass ederek** uygulamaya karar verildi.
- **Uygulama — `optimization/native_solver.py`**: Pyomo modelini SADECE kurmak için kullanıp (`variables.py`/`constraints.py`/`objective.py` değişmedi), çözümü doğrudan `highspy`'a devreden yeni bir modül. Mekanizma:
  1. `model.write(..., io_options={"symbolic_solver_labels": True})` ile MPS'e yazılır, dönen `SymbolMap` her Pyomo değişkeninin MPS'teki tam adını verir (`smap.byObject[id(var)]`).
  2. Warm-start değerleri (`.value` atanmış olanlar) bu isim eşlemesiyle `highspy.HighsSolution` nesnesine, `h.setSolution(...)` ile MIP start olarak verilir.
  3. `h.run()` — native highspy, Phase 7-8 boyunca defalarca doğrulandığı gibi `time_limit`'e tam uyuyor, donmuyor.
  4. Çözüm, aynı isim eşlemesiyle Pyomo değişkenlerine geri yüklenir (`var.value = ...`) — `optimization/results.py::extract_schedule` değişmeden çalışmaya devam ediyor.
- **Doğrulama sırası (yine Correctness önce)**: Minik elle-doğrulanabilir örnekte, hem warm-start'sız hem warm-start'lı, native pipeline **birebir aynı optimal sonucu** (`Cmax=2.5`) verdi — yeni pipeline'ın kendisi de doğru.
- **SMALL sonucu — Stage "makespan"**: Warm-start ile solve süresi **300+ saniyeden 0.34 saniyeye** düştü. Solver, baseline'ın (`Cmax=144.31`) zaten **kanıtlanmış optimal** olduğunu gösterdi (Gap %0, 0 dal-sınır düğümü gerekti). **Yorum**: SMALL'da optimizasyon makespan'i baseline'dan iyileştiremiyor çünkü iyileştirecek yer yok — sistem çok hafif yüklü (Phase 3'teki %12 kullanım oranıyla tutarlı). Bu bir başarısızlık değil, modelin doğruluğunun bağımsız bir kanıtı.
- **SMALL sonucu — Stage "final" (birleşik $ hedefi, C_max+Energy+Tardiness)**: Warm-start başlangıcı $13,051.72 (baseline'ın $ karşılığı). 120 saniye sonra: **$12,263.83 (%6.0 iyileşme)**, gap %10.4 (tam optimal kanıtlanmadı ama gerçek kazanç). Cmax de mantıklı şekilde 144.31'den 150.23'e çıktı — enerji/tardiness'ten tasarruf için biraz daha üretim süresi "harcandı", beklenen çok-amaçlı ödünleşim. **Bu, baseline'ın göremediği (enerji fiyatı, ağırlıklı gecikme) boyutlarda optimizasyonun gerçek değer kattığının ilk somut kanıtı.**
- **Kalıcı değişiklik**: `optimization/solver.py`'ye `solve_with_warm_start(model, data, baseline_schedule, time_limit_seconds)` eklendi — Phase 9+'da kullanılacak önerilen, tek çağrılık arayüz.
- **MEDIUM ölçek doğrulaması (Stage "makespan", 60 sn)**: `Cmax=147.45` (baseline: `147.45`, neredeyse birebir), gap **%0.21** — MEDIUM'da da baseline optimale çok yakın, SMALL'daki bulguyla tutarlı (Phase 3'teki %27 kullanım oranıyla uyumlu, hâlâ hafif yüklü bir sistem). Toplam süre 77.6 sn (60 sn solver + model yazma/yükleme ek yükü) — LARGE ve daha zorlu (yüksek yük/sıkı deadline) senaryolar Phase 20 stress test'in konusu, burada denenmedi.
- **Phase 8 SONUÇ**: Tamamlandı. Big-M sıkılaştırma + native highspy warm-start birlikte, SMALL/MEDIUM'da solver'ı hem hızlı hem güvenilir hale getirdi. Baseline'ın makespan'de zaten (kanıtlanmış veya kanıtlanmaya çok yakın) optimal olduğu, asıl optimizasyon değerinin çok-amaçlı ($ birleşik) hedefte ortaya çıktığı netleşti — bu Phase 9'un (baseline vs optimized) tasarımını doğrudan etkiliyor: makespan-only karşılaştırma "fark yok" gösterecek, asıl anlamlı karşılaştırma "final" (birleşik) hedefle yapılmalı.

## Phase 9 — Baseline vs Optimized

- **Öncül**: Phase 8'in bulgusu gereği karşılaştırma makespan değil, birleşik $ hedefiyle yapılacaktı.
- **Uygulama**: `optimization/comparison.py` — FCFS, EDF, Optimized (Stage "final", FCFS'ten warm-start, 120 sn) aynı `baseline/metrics.py::summarize()` ile ölçülüyor; `compute_total_cost()` aynı $ formülünü (Bölüm 6.3) baseline'lara da uyguluyor ki üçü de aynı ölçekte kıyaslanabilsin.
- **Doğrulama**: Optimize edilmiş planın da (baseline gibi) makine çakışması/sıra ihlali olmadığı ayrıca kontrol edildi — 0 hata, 162/162 operasyon.
- **Sonuç (SMALL)**: Optimized, FCFS'e göre toplam maliyette **%5.22 iyileşme** ($13051.72 → $12370.73). Ama **her metrik tek tek iyileşmedi** — enerji maliyeti %21 düştü, production time ve late job sayısı arttı (144→150h, 3→6). Bu gizlenmedi: model toplamı minimize ediyor, tek tek metrikleri değil — `c_tardy/c_time` ağırlıklarının sonucu doğrudan şekillendirdiğinin somut kanıtı.
- **Yeni gözlem — reproducibility ayrımı**: Solver'ın time-limit'e dayalı sonucu, veri üretiminin aksine tam deterministik değil (aynı model farklı çalıştırmalarda hafif farklı $ değeri verebilir — ör. bu çalıştırmada $12370.73, önceki bir denemede $12263.83). Bu, MIP'lerin bilinen bir özelliği; rapora yazılırken veri-reproducibility'siyle karıştırılmaması gerektiği not edildi.

## Phase 10 — Machine Learning (İşlem Süresi Tahmini)

- **Öncül**: Machine tablosundan (efficiency, age) doğrudan join yapılamayacağı önceden belirlendi — spesifik makine ataması henüz yok (o optimizasyonun kararı, tavuk-yumurta problemi). Feature'lar sadece optimizasyon-öncesi bilinen şeylerle sınırlı tutuldu: `required_machine_type, product_type, quantity, priority, sequence_no`.
- **Uygulama**: `preprocessing/features.py` (feature tablosu), `ml/training.py` (Linear Regression / Random Forest / Gradient Boosting, ortak `ColumnTransformer` ön-işleme), `ml/evaluation.py` (MAE/RMSE/R²), `ml/prediction.py` (orkestratör + model kaydetme).
- **Yanlış tahminim, düzeltildi**: Kullanıcıya önceden "sentetik veri temiz olduğu için R² muhtemelen çok yüksek çıkar" dedim. Gerçek sonuç bunun **tersi** oldu: R² 0.24-0.64 arası, orta seviye. Kök nedeni bulundu: `data_generator/generator.py`'de `base_time = rng.uniform(base_low, base_high)` — bu değer her operasyon için **feature'lardan bağımsız, taze bir rastgele çekiliş** (ör. CNC için 0.5-2.0 saat arası, 4 katına kadar değişebilen bir aralık). Hiçbir feature bunu açıklayamaz çünkü gerçekten rastgele — yani düşük/orta R² burada **doğru ve beklenen** sonuç, model hatası değil.
- **İkinci gözlem — Random Forest/Gradient Boosting, Linear Regression'ı geçemedi** (SMALL: 0.54 vs 0.33/0.24; LARGE: 0.57 vs 0.40/0.57). Sebep: gerçek ilişki (tip bazlı seviye + miktarla çarpımsal artış) büyük ölçüde düzgün/yumuşak, üstüne büyük saf gürültü binmiş — bu tip verilerde esnek ağaç modelleri, ayarlanmamış (default) hiperparametrelerle yerel gürültüye aşırı uyum sağlayıp (overfitting) genelleme gücünü kaybedebiliyor. MEDIUM'da Gradient Boosting hafifçe öne geçti (0.641 vs 0.624) — veri arttıkça ağaç modellerinin göreceli olarak iyileştiği gözlemi bu tek örnekle sınırlı, kesin bir trend değil.
- **Ders (rapor için önemli)**: "Daha karmaşık model = daha iyi" varsayımı burada doğrulanmadı. Bu, ML mentorluğu ilkemizle (sadece yüksek R²'ye odaklanma, sonucu değerlendir) birebir örtüşen, gerçek ve dürüst bir bulgu.

## Phase 11 — Predict → Optimize Entegrasyonu

- **Öncül**: ML'in tahminiyle kurulan plan gerçek hayatta GERÇEK sürelerle çalışacağı için, üç adımlı bir akış tasarlandı: tahmin et → o tahminle optimize et → kararı (atama+sıra) sabit tutup gerçek sürelerle yeniden zamanla ("replay"). `optimization/replay.py` bu son adım için hem burada hem Phase 8'in warm-start'ında ortak kullanılacak şekilde yazıldı.
- **Kritik hata (bulundu, düzeltildi)**: `replay_schedule` ilk yazımda bakım pencerelerini hesaba katmıyordu (baseline'ın kendi mantığında olan "bakımdan kaçınma" adımı kopyalanmamıştı). Bu, `optimization/warmstart.py`'nin Phase 11 için yeniden yazılan versiyonunda gizli bir regresyona yol açtı: SMALL + Stage "final" testinde warm-start artık **infeasible** sayılıp reddediliyordu (`c4_maintenance_after` kısıtında 3.937 saatlik ihlal), solver da warm-start'sız 60 saniyede hiç çözüm bulamıyordu (Phase 7'deki orijinal soruna geri dönüş). Kök neden HiGHS log'unda "Row infeasibilities" mesajıyla yakalandı, `replay_schedule`'a bakım-kaçınma mantığı (`build_maintenance_lookup` + iteratif itme) eklenerek düzeltildi. Düzeltme sonrası minik örnek ve SMALL karşılaştırması yeniden doğrulandı.
- **Yan düzeltme**: `optimization/native_solver.py`'nin çözüm yükleme adımı, HiGHS'in ham float çıktısını (ör. `0.999999998` gibi) doğrudan Pyomo değişkenlerine yazıyordu, bu da onlarca zararsız ama gürültülü domain uyarısına yol açıyordu. İkili/tamsayı değişkenler artık yuvarlanıyor, alt sınırın altına düşen küçük negatif sayısal gürültü (ör. `T[j]=-1e-15`) sınıra kırpılıyor.
- **Beklenmedik iyi haber**: Bu düzeltme, sadece hatayı gidermekle kalmadı — Phase 9'un SMALL sonucunu da **iyileştirdi** (%5.22 → %10.67), çünkü warm-start artık gerçekten kabul ediliyor. `docs/experiments.md`'deki Phase 9 tablosu bu yeni, doğru sayıyla güncellenmeli (bir sonraki adımda yapılacak).
- **Sonuç (SMALL, ML tahminiyle optimize edilip GERÇEK sürede değerlendirilen plan)**:

| Senaryo | Toplam Maliyet | FCFS'e göre iyileşme |
|---|---:|---:|
| FCFS (baseline) | $13051.72 | — |
| ML-Predicted → Optimize → gerçek sürede çalıştır (Phase 11) | $12482.86 | %4.36 |
| Ground-Truth → Optimize (Phase 9, "mükemmel bilgi") | $11659.12 | %10.67 |

  ML tabanlı optimizasyon, teorik maksimum iyileşmenin (%10.67) sadece **%40.85**'ini yakalayabildi (%4.36). Bu, ML tahmin hatasının optimizasyon kalitesine olan gerçek maliyetini gösteren, uydurulmamış bir sonuç — "Predict→Optimize" zincirinin neden önemli olduğunun somut kanıtı.

## Phase 12 — Enerji Tüketimi Tahmini (2. ML modeli)

- **Öncül**: Phase 10'un altyapısı (aynı 3 model, aynı ColumnTransformer mantığı) yeniden kullanılacaktı. `ml/training.py` bunun için genelleştirildi (`TASKS` sözlüğü, `task` parametresi) — sabit kodlanmış processing_time feature'ları yerine, `preprocessing/features.py::build_feature_table` artık her iki hedef için de gereken tüm kolonları (`processing_time` VE `energy_consumption`) döndürüyor.
- **Tasarım kararı — processing_time bir FEATURE olarak eklendi**: `data_generator/generator.py`'de `energy_consumption = processing_time × reference_energy_rate × noise` ilişkisi olduğundan, `processing_time`'ı enerji tahmininde girdi olarak kullanmak mantıklı ve gerçekçi (gerçek dünyada da süre bilgisi enerji tahmininde kullanılır). Eğitim/test'te ground-truth `processing_time` kullanıldı; gerçek Predict→Optimize akışında (Phase 11'deki gibi) bunun yerine Phase 10 modelinin tahmini beslenebilir.
- **Regresyon kontrolü**: Refactor sonrası Phase 10'un processing_time sonucu (SMALL: 0.5378/0.3268/0.2389) birebir aynı çıktı — genelleştirme mevcut davranışı bozmadı.
- **Sonuç — bu sefer R² gerçekten yüksek çıktı (0.93-0.99)**: SMALL/MEDIUM/LARGE'ın hepsinde. Phase 10'un tam tersi bir durum — burada `processing_time` çok güçlü, neredeyse deterministik bir öngörücü.
- **İkinci gözlem — bu sefer ağaç modelleri gerçekten kazandı**: Random Forest/Gradient Boosting, Linear Regression'ı üçünde de geçti (ör. LARGE: 0.985/0.985 vs 0.947). Sebep: gerçek ilişki `processing_time × machine_type'a-özgü-oran` şeklinde **çarpımsal bir etkileşim** içeriyor; ağaç modelleri (özellikle bir kategorik + bir sayısal feature'ın çarpımsal etkileşimini) bu tür yapıları yakalamakta linear regression'dan (interaction term eklenmediği sürece) doğal olarak daha güçlü.
- **Phase 10 vs Phase 12 karşılaştırması (rapor için değerli)**: Aynı altyapı, iki farklı sonuç — biri ML'in saf gürültü karşısında zorlandığı durum (Phase 10, R²~0.5), diğeri güçlü bir öngörücü + çarpımsal etkileşim olduğunda ağaç modellerinin gerçekten fayda sağladığı durum (Phase 12, R²~0.98). İkisi birlikte "ne zaman ML işe yarar, ne zaman yaramaz" sorusuna dengeli bir cevap veriyor.

## Phase 13 — Digital Twin

- **Öncül**: Bu faz sadece state (durum) veri yapısını ve başlangıç durumunu kuracaktı — zamanı ilerletme mantığı bilinçli olarak Phase 14'e bırakıldı (roadmap'te ayrı fazlar).
- **Uygulama**: `digital_twin/machine.py` (MachineState — `data_generator/schemas.py`'deki `MachineStatus` enum'u yeniden kullanıldı, kopyalanmadı), `digital_twin/job.py` (JobState + JobStatus: queued/running/completed/delayed), `digital_twin/state.py` (FactoryState — tüm makine/job durumları + `snapshot()`, `machine_utilization()`, `completed_jobs()` gibi sorgu fonksiyonları), `digital_twin/factory.py` (DigitalTwin — dataset'ten başlangıç durumu kurar, `reset()` ile t=0'a döner).
- **Doğrulama**: SMALL/MEDIUM/LARGE'da başlangıç durumu dataset'teki gerçek makine/job sayılarıyla karşılaştırıldı (10/50, 20/250, 50/1000 — hepsi eşleşti); t=0'da tüm makinelerin idle, tüm işlerin queued olduğu, `reset()` sonrası state'in aynı çıktığı doğrulandı.

## Phase 14 — Simulation (Discrete-Event Simülasyon Motoru)

- **Öncül**: Bir schedule'ı (baseline ya da optimize edilmiş, ortak DataFrame formatı) Digital Twin üzerinde zaman içinde oynatacak bir motor kuracaktık. Enerji maliyeti tutarlılığı için operasyonun BAŞLANGIÇ saatindeki fiyat kullanılacaktı (Phase 6/9'daki kuralla aynı).
- **Uygulama**: `simulation/events.py` (Event tipi: OPERATION_START/END, MAINTENANCE_START/END), `simulation/engine.py` (SimulationEngine — event queue kurar, aynı andaki END'leri START'lardan önce işler, `step()/run_to()/run_all()` ile ilerler).
- **Doğrulama — çapraz kontrol (en güçlü doğrulama yöntemi)**: FCFS baseline planı simülasyondan geçirilip, Faz 3'ün BAĞIMSIZ `baseline/metrics.py::summarize()` hesaplamasıyla karşılaştırıldı — toplam enerji (2211.27 kWh), enerji maliyeti ($4858.60), geciken iş sayısı (3) **birebir** eşleşti. Simülasyon sonunda tüm işlerin tamamlandığı (queued/running=0) doğrulandı.
- **Küçük bir tanım farkı bulundu, açıklandı (hata değil)**: Simülasyon sonunda `avg_machine_utilization=0.14` iken baseline metrics `0.12` veriyordu. Sebebi: `FactoryState.machine_utilization()` paydayı `current_time` (simülasyonun bittiği an, 144.31h) alıyor, `baseline/metrics.py::compute_utilization` ise sabit `horizon_hours` (168h) kullanıyor — iki farklı, kendi içinde tutarlı tanım (`0.12 × 168/144.31 = 0.1397 ≈ 0.14` ile doğrulandı). Karıştırılmaması için burada not düşüldü.

## Phase 15 — What-If Scenario Engine

- **Öncül**: Minimum 3 senaryo istenmişti (orijinal projede 6 örnek: makine arızası, enerji fiyatı, sipariş artışı, deadline sıkılaşması, bakım süresi uzaması, kapasite azalması).
- **Kapsam kararı (dürüstçe)**: "Sipariş artışı" (quantity'nin processing_time'a etkisi sadece veri üretimi anında hesaba katılıyor, üretim sonrası değiştirmek otomatik yansımıyor) ve "kapasite azalması" (Phase 5'te capacity'nin aktif kısıt olmadığına karar verilmişti — hiçbir gözlemlenebilir etkisi olmazdı) kapsam dışı bırakıldı. Bunun yerine 4 tam anlamlı senaryo uygulandı: machine_failure, energy_price_change, deadline_shift, maintenance_duration_change.
- **Uygulama**: `simulation/scenarios.py` — her senaryo dataset'in değiştirilmiş bir kopyasını döner; `optimization/comparison.py::run_comparison` bir `dataset` parametresi kabul edecek şekilde genişletildi (senaryolu dataset de aynı altyapıdan geçebilsin diye).
- **Kritik hata (bulundu, düzeltildi)**: M003 (SMALL'daki tek Assembly makinesi, Phase 3'ten beri bilinen darboğaz) tüm ufuk boyunca "arızalı" yapılınca, baseline (warm-start için kullanılıyor) o tipteki operasyonları makul bir zamana yerleştiremeyip ufkun çok ötesine (217+ saat) taşan zamanlar üretti — bu da `S/C` değişkenlerinin sert sınırını (`0,168`) ihlal edip onlarca Pyomo uyarısına ve sonunda çökme hatasına yol açtı.
  - **Kök neden ayrımı**: Bu bir kod hatası değil — matematiksel olarak GERÇEKTEN çözümsüz (infeasible) bir durum (tek Assembly makinesi tüm ufuk boyunca yoksa, o tipteki hiçbir operasyon planlanamaz). Sorun, sistemin bunu zarifçe raporlamak yerine çökmesiydi.
  - **Çözüm**: `optimization/comparison.py::run_comparison`, çözüm bulunamadığında (`has_feasible_solution_native`) artık `{"feasible": False, "solver_status": ...}` döndürüyor, exception fırlatmıyor. `optimization/warmstart.py`'de warm-start değerleri de `horizon_hours`'a kırpılıyor (asıl çözümsüzlüğü gizlemeden, sadece gereksiz uyarıları önlüyor).
- **Sonuçlar (SMALL, "final" hedefiyle optimize edilmiş plan, orijinal vs senaryo)**:

| Senaryo | Total Cost: Önce → Sonra | Not |
|---|---|---|
| Machine M003 failure (yedeksiz) | — | **INFEASIBLE** — hiçbir geçerli plan yok |
| Machine M001 failure (yedekli, 3 CNC'den biri) | $11,659.12 → $12,747.22 (+%9.3) | Sistem yeni, daha pahalı ama geçerli bir plan buldu |
| Energy price +20% | $11,659.12 → $14,023.44 (+%20.3) | Enerji maliyeti $3900→$5830 (+%49); ilginç: production time ve late jobs hafifçe DÜŞTÜ (144.31, 3) — enerji göreceli olarak daha pahalı olunca model zamanlama/gecikmeyi görece daha çok önemsedi |
| Deadline shift −12h (daha sıkı) | $11,659.12 → $38,011.34 (+%226) | Geciken iş 4'ten **41'e** çıktı (50 işten) — SMALL'daki deadline'ların ne kadar gevşek/hassas olduğunu gösteriyor |
| Maintenance duration +50% | $11,659.12 → $14,039.78 (+%20.4) | Late jobs 4→5, tardiness 0.09h→0.39h |

- **Genel değerlendirme**: İki uç örnek (M003 infeasible vs M001 feasible-ama-pahalı) somut bir iş sonucu gösteriyor: "kritik makine tiplerinde tek nokta bağımlılığı olmamalı" — yedeği olmayan bir makinenin arızası sistemi tamamen durdururken, yedeği olan bir makinenin arızası sadece maliyeti artırıyor. Deadline senaryosu ise sistemin deadline baskısına ne kadar duyarlı olduğunu (4→41 geciken iş) çarpıcı şekilde gösteriyor.

## Phase 16 — Tüm Döngünün Entegrasyonu

- **Öncül**: Önceki fazlarda ayrı ayrı kurulan parçaları (Digital Twin, ML tahmini, optimizasyon, simülasyon, senaryo) tek fonksiyonla çalışan bir akışa bağlamak — yeni matematik/algoritma yok, sadece doğru sırayla birleştirme.
- **Uygulama**: `backend/services/pipeline.py::run_pipeline(size, scenario_name=None, scenario_kwargs=None)`. `ml/predict_optimize.py::run_predict_optimize` ve `optimization/comparison.py::run_comparison`'a önceden eklenen `dataset` parametresi burada da kullanıldı — senaryo dalı ayrı bir kod yolu değil, aynı fonksiyonlara senaryolu dataset'in verilmesiyle çalışıyor (Phase 15'teki "re-optimization" ilkesiyle aynı).
- **Akış**: Factory Data → (opsiyonel senaryo dönüşümü) → Digital Twin (başlangıç durumu) → ML tahmini + Optimizasyon + gerçek süreyle yeniden değerlendirme (Phase 11) → Simulation (planı Digital Twin üzerinde oynat, Phase 14) → sonuç.
- **Doğrulama — çapraz kontrol**: Senaryosuz ve senaryolu (M001 arızası) her iki çalıştırmada da `twin_snapshot`'taki `delayed_jobs`/`total_energy_cost` değerleri, `metrics`'teki `late_jobs`/`energy_cost` ile **birebir eşleşti** — pipeline'ın tüm parçaları doğru bağlandığının kanıtı. Senaryolu koşuda `current_time_hours=168.0` çıktı (üretim 144.69h'de bitmiş olsa da) — sebebi mantıklı: M001'in "arıza" bakım olayı tüm ufku (0-168h) kapladığı için simülasyonun son olayı bu bakımın bitişi oluyor, hata değil.
- **Sonuç**: `backend/services/pipeline.py`, Phase 17'nin (Dashboard/API) doğrudan çağıracağı tek giriş noktası olarak hazır.

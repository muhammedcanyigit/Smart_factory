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

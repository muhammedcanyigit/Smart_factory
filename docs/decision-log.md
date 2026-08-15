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

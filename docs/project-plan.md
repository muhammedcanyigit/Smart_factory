# PHASE 0 — Proje Tanımı (Project Definition)

> Bu doküman, bitirme projesi raporunun "Introduction / Problem Definition / Motivation / Dataset" bölümlerinin ilk taslağıdır. Proje ilerledikçe güncellenecektir. Henüz hiç kod yazılmamıştır.

---

## A — Project Overview (Basit Anlatım)

Bir fabrikayı düşün. İçinde farklı makineler var; her makine belirli işleri belirli sürelerde yapabiliyor. Fabrikaya sürekli üretim siparişleri (job'lar) geliyor, her siparişin bir teslim tarihi (deadline) var. Fabrika müdürü her gün şu soruyla uğraşıyor: "Hangi işi hangi makineye, hangi sırayla vereyim ki hem işler zamanında bitsin hem de enerji faturası şişmesin?"

Bu proje, bu soruyu insan yerine matematiksel bir modelin ve yapay zekânın çözmesini sağlayan bir **karar destek sistemi (decision support system)** kuruyor. Sistem gerçek bir fabrikaya bağlanmıyor; onun yerine fabrikanın davranışını bilgisayarda taklit eden bir **Digital Twin (Dijital İkiz)** inşa ediyoruz — yani makinelerin, işlerin, enerji tüketiminin ve bakım durumlarının sayısal bir modelini.

Sistem üç ana yetenek üzerine kurulu. Birincisi **optimizasyon**: hangi işin hangi makineye, ne zaman atanacağını matematiksel olarak en iyi şekilde hesaplamak. İkincisi **makine öğrenmesi (machine learning)**: bir işin bir makinede ne kadar süreceğini ve ne kadar enerji harcayacağını geçmiş verilerden öğrenerek tahmin etmek. Üçüncüsü **simülasyon ve senaryo analizi**: "bir makine bozulursa ne olur?", "enerji fiyatı %20 artarsa ne olur?" gibi sorulara, sistemi yeniden çalıştırarak cevap vermek.

Gerçek bir fabrikanın verisine erişimimiz olmadığı için başlangıçta **synthetic (yapay/sentetik) veri** kullanacağız — ama bu veri rastgele sayı yığını değil, gerçek fabrika mantığına uygun kurallarla (ör. uzun işlem = daha çok enerji, yaşlı makine = daha çok arıza riski) üretilecek. Ayrıca ilgili gerçek açık veri setlerini (UCI, Kaggle) inceleyip projeye nerede katkı sağlayabileceklerini değerlendireceğiz.

Projenin sonunda ortaya çıkacak şey: kullanıcının fabrika durumunu gördüğü, "OPTIMIZE ET" dediğinde sistemin en iyi üretim planını hesapladığı, bu planı bir simülasyonla "çalıştırdığı", ve kullanıcının "makine bozulursa ne olur?" gibi what-if senaryoları deneyip sonucu anında karşılaştırabildiği bir **dashboard**.

Önemli bir felsefi nokta: bu sistem fabrika müdürünün yerine karar vermiyor. Ona "işte alternatifler, işte bunların sonuçları" diyor. Bu yüzden "karar destek sistemi" — otomasyon sistemi değil.

Akademik dürüstlük açısından da net olmak gerekiyor: veri sentetik olduğu sürece sonuçlar "gerçek fabrikada X oldu" değil, "sentetik veri setinde X gözlemlendi" şeklinde raporlanacak. Hiçbir performans sayısı, model gerçekten o sayıyı üretmeden yazılmayacak.

---

## B — Terminology (Terminoloji Tablosu)

| English | Türkçe | Basit Açıklama | Bu Projede Neden Kullanılıyor |
|---|---|---|---|
| Digital Twin | Dijital İkiz | Fiziksel bir sistemin (burada: fabrika) bilgisayardaki durum/davranış modeli. Sensör verisi yerine simüle edilmiş veriyle çalışır. | Fabrikanın makine/iş/enerji durumunu tek bir "state" (durum) nesnesinde tutup, optimizasyon sonucunu bu durum üzerinde test etmek için. |
| MILP (Mixed Integer Linear Programming) | Karma Tamsayılı Doğrusal Programlama | Bazı değişkenlerin 0/1 ya da tam sayı olduğu, geri kalanının sürekli (ondalıklı) olabildiği doğrusal optimizasyon türü. | Bir işin bir makineye atanıp atanmadığı gibi "evet/hayır" kararları binary (0/1) değişkenlerle modellenecek. |
| Decision Variable | Karar Değişkeni | Optimizasyon modelinin "hangi değeri seçeceğim?" diye çözdüğü bilinmeyen. | Örn. `x[j,m]` = job j, makine m'ye atansın mı atanmasın mı — modelin bulacağı cevap. |
| Objective Function | Amaç Fonksiyonu | Modelin en küçük (veya en büyük) yapmaya çalıştığı tek sayısal ifade. | "Toplam üretim süresi + enerji maliyeti + gecikme" gibi bir toplamı minimize edeceğiz. |
| Constraint | Kısıt | Çözümün uyması zorunlu kural. | "Bir makine aynı anda iki iş yapamaz" gibi fiziksel gerçekleri modele dayatmak için. |
| Feasible Solution | Uygun/Olurlu Çözüm | Tüm kısıtları sağlayan (ama en iyi olmak zorunda olmayan) çözüm. | Modelin ürettiği her cevabın gerçekten uygulanabilir olduğunu garanti etmek için. |
| Optimal Solution | Optimal (En İyi) Çözüm | Tüm uygun çözümler arasında amaç fonksiyonunu en iyi yapan çözüm. | Solver'ın bize "işte matematiksel olarak en iyisi bu" diyebilmesi için. |
| Makespan | Toplam Tamamlanma Süresi | Tüm işlerin bittiği en geç zaman anı. | İlk optimizasyon hedefimiz: makespan'i minimize etmek. |
| Tardiness | Gecikme | Bir işin deadline'ından ne kadar geç bittiği (geç değilse 0). | İkinci/üçüncü aşamada amaç fonksiyonuna eklenecek — kullanıcıya "kaç iş kaç saat geç kaldı" göstermek için. |
| Baseline | Referans/Kıyas Yöntemi | Optimizasyon kullanmadan, basit bir kuralla (ör. sırayla atama) üretilen plan. | Optimizasyonun gerçekten fayda sağladığını sayısal olarak kanıtlayabilmek için karşılaştırma noktası. |
| Synthetic Data | Sentetik/Yapay Veri | Gerçek ölçüm değil, kurallara göre bilgisayarda üretilmiş veri. | Gerçek fabrika verisine erişimimiz olmadığı için, gerçekçi ilişkiler içeren yapay veri üreteceğiz. |
| Feature Engineering | Öznitelik Mühendisliği | Ham veriden, modelin öğrenmesine yardımcı yeni değişkenler türetmek. | Ör. "makine yaşı × geçmiş kullanım oranı" gibi bir özniteliğin arıza tahminine yardımcı olması. |
| Predict → Optimize | Tahmin Et → Optimize Et | Önce ML ile bilinmeyen bir değeri tahmin edip, bu tahmini optimizasyon modeline parametre olarak vermek. | ML'in işlem süresini tahmin etmesi, optimizasyonun bu tahmin üzerinden plan kurması. |
| What-If / Scenario Analysis | Ne-Olursa-Öyle / Senaryo Analizi | "X değişirse sonuç ne olur?" sorusunu, veriyi değiştirip modeli yeniden çalıştırarak cevaplamak. | Makine arızası, enerji fiyat artışı gibi durumları test etmek için. |
| Discrete-Event Simulation | Kesikli Olay Simülasyonu | Sistemin zamanının sürekli değil, "olaylar" (iş başlar/biter) arasında atlayarak ilerletildiği simülasyon türü. | Optimizasyon planını "zaman içinde çalıştırıp" makine/iş durumlarını adım adım güncellemek için. |
| Multi-Objective Optimization | Çok Amaçlı Optimizasyon | Birden fazla (bazen çelişen) hedefi aynı anda dengeleyen optimizasyon. | Üretim süresi, enerji maliyeti ve gecikmenin aynı anda dengelenmesi gerektiği için. |
| Solver | Çözücü | Matematiksel modeli sayısal olarak çözen yazılım motoru. | Kurduğumuz MILP modelini gerçekten "çözecek" olan HiGHS/Gurobi gibi programlar. |
| Pyomo | Pyomo | Python'da matematiksel optimizasyon modeli kurmayı sağlayan kütüphane. | Modelimizi (değişken, kısıt, amaç fonksiyonu) Python koduna dökmek için. |
| HiGHS | HiGHS | Açık kaynak, ücretsiz bir MILP/LP solver'ı. | Herkeste çalışabilen, lisans gerektirmeyen varsayılan solver'ımız. |
| R² / MAE / RMSE | R² / Ortalama Mutlak Hata / Kök Ortalama Kare Hata | ML regresyon modelinin tahmin başarısını ölçen istatistikler. | İşlem süresi/enerji tahmin modelinin ne kadar isabetli olduğunu raporlamak için. |
| Machine Utilization | Makine Kullanım Oranı | Bir makinenin toplam süre içinde ne kadarını çalışarak geçirdiği (%). | Baseline vs optimized karşılaştırmasında verimliliği göstermek için. |

Bu liste sabit değil — yeni bir terim ilk geçtiğinde aynı formatta açıklayıp bu tabloya ekleyeceğim.

---

## C — System Architecture (ASCII Diagram)

```
┌───────────────────────────────────────────────────────────────────────┐
│                              DASHBOARD                                 │
│   Factory Overview | Production | Energy | Optimization | What-If      │
└──────────────────────────────────▲──────────────────────────┬─────────┘
                                    │ REST API (JSON)          │ user action
                                    │                          ▼
┌───────────────────────────────────┴─────────────────────────────────┐
│                          BACKEND (FastAPI)                          │
│   /machines  /jobs  /optimize  /simulate  /scenario  /results       │
└───┬───────────────┬────────────────┬───────────────┬────────────────┘
    │                │                │               │
    ▼                ▼                ▼               ▼
┌────────┐   ┌───────────────┐  ┌────────────┐  ┌──────────────────┐
│Database│   │ Data Generator │  │     ML     │  │   Digital Twin    │
│(SQLite)│   │ (synthetic)    │  │(sklearn/   │  │  state: machines, │
│machines│   │ machines, jobs,│  │ XGBoost)   │  │  jobs, energy,    │
│jobs,   │   │ energy price,  │  │ predicts:  │  │  maintenance      │
│energy, │   │ maintenance    │  │ time, energy│ └────────┬──────────┘
│results │   └───────────────┘  └──────┬─────┘          │
└────────┘                             │ predicted params │
                                        ▼                  │
                              ┌──────────────────┐         │
                              │   OPTIMIZATION    │         │
                              │ (Pyomo + HiGHS)   │         │
                              │ vars/constraints/  │        │
                              │ objective/solver   │        │
                              └─────────┬──────────┘        │
                                        │ optimal schedule    │
                                        ▼                     ▼
                              ┌──────────────────────────────────┐
                              │           SIMULATION              │
                              │  schedule'ı zaman içinde oynatır,  │
                              │  Digital Twin state'ini günceller  │
                              └─────────────────┬──────────────────┘
                                                 │
                                                 ▼
                              ┌──────────────────────────────────┐
                              │      WHAT-IF SCENARIO ENGINE       │
                              │ machine failure / price / demand   │
                              │ → state değiştir → re-optimize     │
                              └──────────────────────────────────┘
```

Ana döngü (Phase 16'daki döngünün özeti):

```
Factory Data → Digital Twin State → ML Predictions → Optimization
     ↑                                                      │
     └──────────── Scenario / New Data ← Simulation ←────────┘
```

---

## D — Project Roadmap (Phase 0 → Final)

| Phase | İçerik | Çıktı |
|---|---|---|
| 0 | Proje tanımı, kapsam, gereksinimler | Bu doküman |
| 1 | Veri modeli tasarımı (Machine, Job, Operation, EnergyPrice, Maintenance) | Şema (ER diagram + alan tanımları) |
| 2 | Synthetic data generator (SMALL/MEDIUM/LARGE, seed=42) | Çalışan Python üretici + örnek CSV/DB |
| 3 | Baseline scheduler (FCFS / EDF) | Baseline metrikleri (süre, enerji, geciken iş) |
| 4 | Matematiksel model tasarımı (kod yok) | Karar değişkenleri, parametreler dokümanı |
| 5 | Kısıtların tanımı | Kısıt listesi + matematiksel formülasyon |
| 6 | Amaç fonksiyonu (önce makespan, sonra enerji, sonra tardiness) | Objective formülasyonu + α/β/γ gerekçesi |
| 7 | Pyomo implementasyonu | `optimization/` modülü |
| 8 | Solver entegrasyonu (HiGHS varsayılan, Gurobi opsiyonel) | Config üzerinden solver seçimi |
| 9 | Baseline vs Optimized karşılaştırma | Karşılaştırma tablosu + % iyileşme |
| 10 | ML: işlem süresi tahmini (Linear → RF → GB/XGBoost) | Eğitilmiş model + MAE/RMSE/R² |
| 11 | Predict → Optimize entegrasyonu | ML çıktısının optimizasyona parametre olması |
| 12 | Enerji tüketimi tahmini (opsiyonel 2. ML modeli) | Enerji tahmin modeli |
| 13 | Digital Twin state katmanı | `digital_twin/` modülü |
| 14 | Simülasyon (planın zaman içinde oynatılması) | `simulation/` modülü |
| 15 | What-If Scenario Engine (min. 3 senaryo) | Senaryo çalıştırma + karşılaştırma |
| 16 | Tüm döngünün entegrasyonu | Uçtan uca çalışan pipeline |
| 17 | Dashboard (Factory/Production/Energy/Optimization/Digital Twin/What-If) | Frontend |
| 18 | Before/After görselleştirme | Grafikler |
| 19 | Deneysel değerlendirme (SMALL/MEDIUM/LARGE deneyleri) | Deney tablosu |
| 20 | Stress test (solve time, memory, ölçeklenebilirlik) | Stress test raporu |
| 21 | Testler (unit + edge case) | `tests/` modülü |
| 22 | Nihai mimari sadeleştirme | Klasör yapısı gözden geçirme |
| Final | Uçtan uca demo (Dashboard → Optimize → Simulate → What-If) | Demo senaryosu |

Kural: Her phase'e başlamadan önce sana o phase'in "ne/neden/nasıl"ını anlatacağım, koda öyle geçeceğiz.

---

## E — Dataset Strategy (Araştırma Sonucu)

Web üzerinde Kaggle, UCI, GitHub ve akademik kaynaklarda araştırma yaptım. Sonuç: **projenin ihtiyaç duyduğu "tek, birleşik, gerçek fabrika veri seti" (makine + iş + enerji fiyatı + bakım + deadline hepsi bir arada) mevcut değil.** Ama işimize yarayacak, gerçek ölçümlere dayanan parça veri setleri var. Bunları **doğrudan ana veri kaynağı olarak değil, synthetic generator'ı gerçekçi kılmak için kalibrasyon/referans** olarak kullanacağız.

### Bulunan ilgili gerçek/açık kaynaklar

**1. Steel Industry Energy Consumption Dataset (UCI #851)**
- Kaynak: gerçek bir fabrika — DAEWOO Steel Co., Gwangyang, Güney Kore. UCI Machine Learning Repository, lisans CC BY 4.0.
- İçerik: kWh cinsinden enerji tüketimi, reaktif güç, güç faktörü, CO2, gün içi zaman damgası (gece yarısından saniye), hafta içi/sonu, "Light/Medium/Maximum Load" tipi.
- Projeye uygunluğu: **Gerçek** bir fabrikanın enerji tüketim örüntüsünü (zamana göre, yük tipine göre nasıl değiştiğini) görmek için kullanılabilir. Doğrudan job-level (iş bazlı) veri değil, bu yüzden optimizasyon modeline direkt giremez — ama synthetic generator'daki "enerji tüketimi zamana/yüke göre nasıl dalgalanmalı" kuralını gerçekçi kalibre etmek için referans olacak.
- Eksik: job/deadline/machine-assignment bilgisi yok, fiyat (price_per_kwh) sütunu yok — bunlar sentetik olarak eklenecek (ör. Türkiye/genel TOU — time-of-use tarife mantığıyla saatlik fiyat eğrisi).

**2. AI4I 2020 Predictive Maintenance Dataset (UCI #601, Kaggle üzerinde de mevcut)**
- Kaynak: UCI, lisans CC BY 4.0. Kendisi de **sentetik** ama endüstri motive edilmiş (bunu dataset sayfası açıkça belirtiyor) — 10.000 satır, hava/işlem sıcaklığı, tur hızı, tork, takım aşınması ve 5 farklı arıza tipi (TWF, HDF, PWF, OSF, RNF).
- Projeye uygunluğu: Makine arızası ile "kullanım/aşınma" arasındaki ilişkiyi nasıl modelleyeceğimize dair gerçekçi bir şablon. Maintenance/failure olasılığı kurallarımızı (ör. yaş arttıkça arıza riski artar, bakım sonrası azalır) bu datasetteki değişken tiplerine benzer şekilde kuracağız.
- Doğrudan kullanım: İleri seviye opsiyonel özellik olan **Predictive Maintenance** (Bölüm 13, "İleri Seviye Opsiyonel Özellikler") için gerçek bir eğitim verisi olarak doğrudan kullanılabilir — kendi sentetik verimize ek olarak, ayrı bir deney olarak.

**3. Job Shop / Flexible Job Shop Scheduling Benchmark Instances (Taillard, Hurink, Brandimarte, OR-Library; GitHub: `SchedulingLab/fjsp-instances`, `ai-for-decision-making-tue/JSSP_Environments`, `VincentALBoyer/GFJSP`, enerji-farkında versiyon: `hamcruise/FJSP-TOU`)**
- Kaynak: Akademik literatürde onlarca yıldır kullanılan, optimal/en iyi bilinen çözümleri belli olan standart test problemleri (kamuya açık, akademik kullanım serbest).
- Projeye uygunluğu: Bunlar "gerçek fabrika verisi" değil ama **optimizasyon modelimizin doğruluğunu kanıtlamak** için çok değerli: modelimizi bu klasik instance'lardan biri üzerinde çalıştırıp, literatürdeki bilinen optimal değerle karşılaştırabiliriz. Bu, "modelimiz doğru çalışıyor" iddiasını sentetik kendi verimizin ötesinde bağımsız olarak doğrular. `FJSP-TOU` özellikle enerji fiyatı zaman-dilimine göre değişen (time-of-use) senaryolar içeriyor — Phase 6/12 enerji-maliyet objective'i için ilham/referans olabilir.
- Eksiklik: Bakım (maintenance), deadline/tardiness, makine yaşlanması gibi bizim modelimizin bazı boyutları bu klasik setlerde yok.

### Sonuç ve Strateji

Uygun **tek bir birleşik gerçek dataset bulunamadı** — bu beklenen bir durumdu, çünkü "makine+iş+enerji+bakım" hepsini içeren, açık lisanslı, kamuya açık bir endüstriyel dataset pratikte neredeyse hiç yok (bu firmalar için hassas operasyonel veridir). Bu yüzden:

1. **Ana veri: synthetic generator** (Phase 2) — deterministik seed (`SEED=42`), gerçekçi ilişkiler içerecek (süre↑→enerji↑, yaş↑→arıza riski↑, bakım sonrası hata↓, ürün-makine uyumluluğu, saatlik enerji fiyatı eğrisi).
2. **Kalibrasyon referansı**: Steel Industry Energy dataset'inden gerçek enerji tüketim dağılım/örüntüsü (ör. yük tipine göre kWh dağılımı) örnek alınarak sentetik enerji üretim kuralları gerçekçi sınırlarda tutulacak.
3. **Bağımsız doğrulama**: Taillard/Hurink/Brandimarte instance'larından biri üzerinde optimizasyon modelimiz çalıştırılıp literatür sonucuyla karşılaştırılacak (Phase 19 deneylerine ek deney olarak).
4. **Opsiyonel ek deney**: AI4I 2020 üzerinde gerçek/sentetik-ama-bağımsız bir arıza tahmini modeli eğitilip, kendi generator'ımızın ürettiği arıza mantığıyla karşılaştırılabilir (Bölüm 13 "Predictive Maintenance" için).

Rapor bölümünde bu üç kaynak da "Dataset" ve "Related Work" bölümlerinde referans gösterilecek; hangi sonucun sentetik veriden, hangisinin dış kaynaktan geldiği her zaman açıkça belirtilecek.

---

## F — Mathematical Problem (Kod Öncesi, Kavramsal)

Türkçe problem tanımı: Elimizde bir **makine kümesi** ve bir **iş kümesi** var. Her iş, belirli bir makine tipinde, belirli bir sürede işlenebiliyor ve belirli miktarda enerji tüketiyor. Amacımız, hangi işin hangi makineye, ne zaman atanacağına karar vermek; öyle ki hem fiziksel kurallar (bir makine aynı anda tek iş yapar, bakımdaki makineye iş verilmez, vb.) ihlal edilmesin hem de toplam üretim süresi, enerji maliyeti ve gecikmeler mümkün olduğunca az olsun.

- **Parameters (Parametreler)**: Modelin bilmesi gereken, bizim önceden verdiğimiz sabit sayılar. Örn. her işin süresi, her makinenin enerji tüketim oranı, her işin deadline'ı. Bunlar Phase 2'de synthetic generator'dan, ileride Phase 10-12'de ML tahminlerinden gelecek.
- **Decision Variables (Karar Değişkenleri)**: Modelin bizim için "bulacağı" bilinmeyenler. En temel değişken `x[j,m]` — job j'nin machine m'ye atanıp atanmadığı (0/1). Buna ek olarak her işin başlama zamanı (`start[j]`) ve bitiş zamanı (`completion[j]`) gibi sürekli değişkenler de olacak.
- **Objective Function (Amaç Fonksiyonu)**: Karar değişkenlerinin aldığı değerlere göre hesaplanan, minimize etmek istediğimiz tek sayı. İlk aşamada sadece makespan (en geç biten işin zamanı); sonra buna enerji maliyeti ve gecikme cezası eklenip ağırlıklı toplam haline gelecek.
- **Constraints (Kısıtlar)**: Karar değişkenlerinin alabileceği değerleri sınırlayan eşitlik/eşitsizlikler — "her iş tam olarak bir makineye atanmalı", "aynı makinede iki iş zaman olarak çakışamaz" gibi. Bunlar olmadan model fiziksel olarak imkânsız planlar üretebilir (ör. bir makinenin aynı anda 5 iş yapması).

Bu dört kavram (parameters, decision variables, objective, constraints) her matematiksel optimizasyon modelinin iskeletidir — Phase 4-6'da bunları somut olarak (hangi indeks, hangi formül) birlikte kuracağız, henüz kod yazmadan.

---

## G — ML'in Projedeki Rolü

Machine Learning bu projede **kural koymuyor, tahmin ediyor.** İki net görevi var:

1. **İşlem süresi tahmini (Phase 10-11)**: Gerçek hayatta bir işin bir makinede tam olarak ne kadar süreceği baştan kesin bilinmez — makinenin o anki yükü, ürün tipi, makinenin yaşı gibi faktörlere bağlıdır. Optimizasyon modeli bir sayıya ihtiyaç duyar (`processing_time[j,m]`); bu sayıyı sabit/varsayılan vermek yerine, geçmiş verilerden öğrenmiş bir ML modelinden (Linear Regression → Random Forest → Gradient Boosting) tahmin ederek alacağız. Bu **Predict → Optimize** akışının kalbi: ML "muhtemelen ne kadar sürer" der, optimizasyon bu tahmine göre "en iyi planı" kurar.
2. **Enerji tüketimi tahmini (Phase 12, opsiyonel ikinci model)**: Aynı mantıkla, bir işin ne kadar enerji harcayacağını tahmin edip optimizasyonun enerji-maliyeti amaç fonksiyonuna besleyecek.

ML'in **yapmadığı** şey: hangi işin hangi makineye gideceğine karar vermek. O karar tamamen optimizasyon modelinin (MILP) işi. ML sadece optimizasyona daha gerçekçi girdi sağlıyor. Model performansı MAE/RMSE/R² ile ölçülecek ama tek başına yüksek R² hedef değil — asıl soru "bu tahminler optimizasyon sonucunu anlamlı şekilde iyileştiriyor mu?"

---

## H — Digital Twin'in Projedeki Rolü

Digital Twin burada fabrikanın **fiziksel ikizi değil, durum ve davranış modeli.** Somut olarak şunu tutan bir yazılım katmanı: şu anda hangi makine hangi işi yapıyor, hangi makineler boşta/bakımda, hangi işler tamamlandı/gecikti, toplam ne kadar enerji harcandı, simülasyon saati kaçta.

Rolü üç aşamada devreye giriyor:

1. **Optimizasyon sonucunu "gerçeğe" dökme (Phase 14, Simulation)**: Optimizasyon bize statik bir plan verir ("job 12 → machine 1, 08:00-08:35"). Digital Twin bu planı zaman içinde adım adım "oynatarak" makine durumlarını günceller — böylece planın fabrika davranışına nasıl dönüştüğünü görebiliriz, sadece bir tablo değil, zaman içinde akan bir durum.
2. **What-if senaryoların temeli (Phase 15)**: "Machine 3 bozulursa ne olur?" sorusunu cevaplamak için önce Digital Twin state'inde o makineyi "arızalı" yapıyoruz, sonra optimizasyonu bu yeni state ile tekrar çalıştırıyoruz. Digital Twin olmadan "yeni durum" kavramının net bir temsili olmaz.
3. **Dashboard'ın veri kaynağı (Phase 17)**: Dashboard'daki "Factory Overview", "Digital Twin" panelleri doğrudan bu state'i gösterir.

Netlik için tekrar vurgu: bu Digital Twin gerçek zamanlı sensör verisiyle beslenmiyor (proje sınırları, Bölüm 12'de belirtildiği gibi IoT/PLC entegrasyonu kapsam dışı). Bu bir **simülasyon tabanlı** dijital ikiz — akademik olarak bu ayrımı rapor boyunca koruyacağız.

---

## I — Final Demo (Adım Adım Kullanıcı Deneyimi)

1. Kullanıcı dashboard'ı açar → mevcut fabrika durumu (makineler, işler) listelenir.
2. Baseline plan (ör. FCFS) otomatik gösterilir: üretim süresi, enerji maliyeti, geciken iş sayısı.
3. Kullanıcı **OPTIMIZE** butonuna basar.
4. Arka planda: ML modelleri işlem süresi/enerji tahminlerini üretir → bu tahminler Pyomo/HiGHS optimizasyon modeline parametre olarak girer → solver optimal (veya belirli sürede bulunan en iyi) planı döndürür.
5. Digital Twin bu planı simüle eder, zaman içinde makine durumlarını günceller.
6. Dashboard Before/After: Baseline vs Optimized tablosu ve grafikleri gösterilir (% iyileşme dahil, gerçek sayılardan hesaplanmış).
7. Kullanıcı What-If panelinden bir senaryo seçer (ör. "Machine 03 fails").
8. Digital Twin state güncellenir (o makine artık kullanılamaz), optimizasyon bu yeni koşullarla yeniden çalışır.
9. Yeni plan, eski optimal plan ve orijinal baseline ile birlikte karşılaştırmalı gösterilir.

---

## J — Risks (Teknik Riskler ve Azaltma Planı)

| Risk | Etkisi | Azaltma |
|---|---|---|
| MILP modeli büyük dataset'te (LARGE: 50 makine/1000 job) makul sürede çözülemeyebilir | Deney/demo yapılamaz hale gelir | Küçük veriyle geliştir, solver time-limit + "best found solution" kabul et, Phase 20'de bunu açıkça ölç ve raporla (gizlemek yerine bilimsel bulgu olarak sun) |
| Synthetic data gerçekçi olmayabilir, sonuçlar "oyuncak" görünebilir | Akademik güvenilirlik zayıflar | Gerçek datasetlerle (Steel Industry, AI4I2020) kalibrasyon; ilişkileri (yaş→arıza, süre→enerji) literatüre dayandırma; sınırlamaları raporda açıkça yazma |
| ML tahminleri optimizasyonu yanlış yönlendirebilir (kötü tahmin → kötü plan) | Predict→Optimize zincirinin zayıf halkası | Model performansını MAE/RMSE/R² ile izle; ML olmadan (gerçek/varsayılan değerlerle) optimizasyon sonucuyla karşılaştır, farkı ölç |
| Kapsam çok büyük (22 phase) — bitirme projesi süresinde tamamlanamayabilir | Proje yarım kalır | Fazları küçük çalışan sistemler halinde ilerlet (Phase 0-9 = minimum uygulanabilir sistem); ileri özellikler (robust/stochastic opt, RL) opsiyonel bırakılır |
| Multi-objective ağırlıkları (α, β, γ) keyfi seçilirse sonuçlar "istenen sonuca göre ayarlanmış" görünebilir | Bilimsel savunulabilirlik zayıflar | Ağırlıkları duyarlılık analiziyle (sensitivity analysis) test et, seçim gerekçesini raporla, alternatif ağırlıklarla sonucun nasıl değiştiğini göster |
| Digital Twin / gerçek fabrika ayrımı bulanıklaşabilir | Akademik dürüstlük sorunu | Rapor ve dashboard'da her zaman "simulated / synthetic" ibaresi; hiçbir yerde "gerçek fabrikada" ifadesi kullanılmayacak |

---

*Sonraki adım: Phase 1 (Data Model) — makine, iş, operasyon, enerji fiyatı ve bakım entity'lerinin alanlarını birlikte netleştireceğiz. Sen onay/soru sorana kadar koda geçmiyorum.*

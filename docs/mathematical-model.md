# Mathematical Optimization Model

> Bu doküman MILP modelini aşamalı olarak inşa eder. Bu sürüm **Phase 4** (index kümeleri, parametreler, karar değişkenleri) ve **Phase 5** (kısıtlar) içeriğini kapsar. Amaç fonksiyonu (Phase 6) henüz yazılmadı, aşağıda "Planlanan İçerik" altında listelidir.

Kavramsal problem tanımı için bkz. [project-plan.md](project-plan.md) Bölüm F. Veri modeli için bkz. [dataset.md](dataset.md).

---

## 1. Index Kümeleri (Sets)

| Sembol | Anlamı |
|---|---|
| `J` | Tüm işler (jobs) kümesi |
| `O` | Tüm operasyonlar kümesi |
| `O_j ⊆ O` | Job `j`'ye ait operasyonlar, `sequence_no` sırasına göre |
| `M` | Tüm makineler kümesi |
| `M_o ⊆ M` | Operasyon `o` için uygun makineler — yani `machine_type = o.required_machine_type` olan makineler |

**Yapısal gözlem**: Bu projedeki ürün şablonlarında (`PRODUCT_TEMPLATES`, bkz. `data_generator/generator.py`) her operasyon dizisi **farklı** makine tiplerinden oluşuyor (aynı job içinde bir makine tipi tekrar etmiyor). Bu yüzden aynı job'a ait iki operasyon için `M_o ∩ M_o' = ∅` her zaman doğrudur — yani bir işin kendi operasyonları asla aynı makineye "yarışarak" gelmez. Aşağıda tanımlanacak sıralama değişkeni `y[o,o']` bu yüzden yalnızca **farklı job'lara ait**, aynı makine tipini paylaşan operasyon çiftleri için anlamlıdır. Aynı job içindeki sıralama (operasyon k+1, operasyon k'dan sonra başlamalı) çok daha basit bir kısıtla (Phase 5) ifade edilecek.

---

## 2. Parametreler (Parameters)

Modelin bilmesi gereken, veriden gelen sabitler:

| Sembol | Anlamı | Kaynak (dataset.md) |
|---|---|---|
| `p_o` | Operasyon `o`'nun nominal işlem süresi (saat) | `Operation.processing_time` |
| `e_o` | Operasyon `o`'nun nominal enerji tüketimi (kWh) | `Operation.energy_consumption` |
| `eff_m` | Makine `m`'nin verimlilik katsayısı (0-1) | `Machine.efficiency` |
| `r_j` | Job `j`'nin release_time'ı | `Job.release_time` |
| `d_j` | Job `j`'nin deadline'ı | `Job.deadline` |
| `price_t` | `t` saatindeki birim enerji fiyatı | `EnergyPrice.price_per_kwh` |
| `[ms_m, me_m]` | Makine `m`'nin her bir bakım aralığının başlangıç/bitişi | `Maintenance.start_time/end_time` |
| `BigM` | Disjunctive kısıtlar için yeterince büyük sabit | Model kurulumunda hesaplanır (ör. planlama ufkunun 2 katı) |

**Not**: `p_o` ve `e_o`, `required_machine_type`'ın *ortalama* makinesine göre üretilmiş nominal değerlerdir (bkz. dataset.md'deki modelleme kararı). Gerçek süre, atanan makinenin `eff_m`'sine göre karar değişkenleri üzerinden hesaplanır — aşağıya bakınız.

---

## 3. Karar Değişkenleri (Decision Variables)

### 3.1 — Atama Değişkeni: `x[o,m] ∈ {0,1}`, `m ∈ M_o`

Operasyon `o`, makine `m`'ye atanırsa `1`, atanmazsa `0`. Bu, modelin çözeceği **temel** karardır — Phase 0'da bahsettiğimiz `x[j,m]`'nin, iş yerine operasyon seviyesinde somutlaşmış hali.

Her operasyon tam olarak bir makineye atanmalıdır (bu bir kısıt, Phase 5'te yazılacak):
`Σ_{m ∈ M_o} x[o,m] = 1`

### 3.2 — Zamanlama Değişkenleri: `S[o] ≥ 0`, `C[o] ≥ 0` (sürekli)

- `S[o]`: operasyon `o`'nun başlama zamanı (planlama ufkunun başlangıcından itibaren saat cinsinden).
- `C[o]`: operasyon `o`'nun bitiş zamanı.

Bitiş zamanı, atanan makinenin verimliliğine göre hesaplanır:

```
C[o] = S[o] + Σ_{m ∈ M_o} x[o,m] · (p_o / eff_m)
```

Bu ifade **doğrusaldır** (linear) çünkü `x[o,m]` binary ve `p_o/eff_m` sabit bir katsayı — MILP'in "linear" tarafını bozmuyor. `x[o,m]` sadece bir tek `m` için 1 olabileceğinden, toplam aslında tek bir terime indirgenir (atanan makinenin süresi).

### 3.3 — Sıralama (Precedence) Değişkeni: `y[o,o'] ∈ {0,1}`

Yalnızca `M_o ∩ M_o' ≠ ∅` olan (aynı makine tipini paylaşabilen, farklı job'lara ait — yukarıdaki yapısal gözlem gereği) operasyon çiftleri `(o, o')` için tanımlıdır:

- `y[o,o'] = 1` → `o`, `o'`'den önce başlar (ikisi aynı makineye denk gelirse)
- `y[o,o'] = 0` → `o'`, `o`'dan önce başlar

Bu değişken tek başına bir şey zorlamaz; Phase 5'te Big-M yöntemiyle "eğer ikisi de aynı makineye atandıysa, sıralamaya uy" kısıtına bağlanacak.

### 3.4 — Tardiness Değişkeni: `T[j] ≥ 0` (sürekli)

Job `j`'nin gecikmesi. `T[j] = max(0, C[son operasyon] - d_j)` — bu "max" ifadesi MILP'te doğrudan yazılamaz (doğrusal değil), Phase 5'te iki eşitsizlikle (`T[j] ≥ C[...] - d_j` ve `T[j] ≥ 0`) doğrusallaştırılacak.

### 3.5 — Makespan Değişkeni: `C_max ≥ 0` (sürekli)

Tüm operasyonların en geç bitiş zamanı. `C_max ≥ C[o]` (her `o` için) kısıtıyla Phase 5'te tanımlanacak.

---

## 4. Somut Sayısal Örnek

Soyut kalmaması için küçük bir örnek: 2 job, aynı makine tipini (`Packaging`) paylaşan 2 operasyon.

- Job A'nın son operasyonu `o1` (Packaging gerektiriyor), nominal süre `p_o1 = 0.3` saat.
- Job B'nin son operasyonu `o2` (Packaging gerektiriyor), nominal süre `p_o2 = 0.2` saat.
- Uygun makineler: `M_o1 = M_o2 = {M005}` (SMALL preset'te tek Packaging makinesi, `eff_M005 = 0.9`).

Model çözünce şunları bulur (örnek, gerçek çözüm değil):

- `x[o1, M005] = 1`, `x[o2, M005] = 1` (ikisi de bu tek makineye gitmek *zorunda*, başka seçenek yok)
- `M_o1 ∩ M_o2 = {M005} ≠ ∅` olduğu için `y[o1,o2]` tanımlı bir değişken
- Diyelim model `y[o1,o2] = 1` buldu → `o1` önce işlenecek
- `S[o1] = 10.0`, `C[o1] = 10.0 + 0.3/0.9 = 10.33`
- `o2`, `M005` boşalmadan başlayamaz → `S[o2] ≥ C[o1] = 10.33` (bu, Phase 5'te `y[o1,o2]` ile Big-M üzerinden kurulacak kısıt)
- `S[o2] = 10.33`, `C[o2] = 10.33 + 0.2/0.9 = 10.55`

Bu örnek, `baseline/scheduler.py`'de greedy olarak "elle" yaptığımız şeyin (en erken uygun makineyi bul, bakım/çakışma varsa ertele) matematiksel modelde nasıl `x`, `y`, `S`, `C` değişkenleriyle *karar olarak bırakıldığını* gösteriyor — baseline'da biz sıralamayı greedy kuralla seçtik, optimizasyon modelinde `y[o,o']`'yi solver seçecek.

---

## 5. Kısıtlar (Constraints)

Aşağıdaki 8 kısıt, Phase 4'teki değişkenleri gerçek fiziksel kurallara bağlar. Sıra, `project-plan.md`'deki orijinal listeyle aynı.

### C1 — Atama (her operasyon tam olarak bir makineye)

```
Σ_{m∈M_o} x[o,m] = 1     ∀o∈O
```

### C2 — Job içi sıralama (operasyonlar sırayla yapılmalı)

Job `j`'nin ardışık operasyonları `o_k, o_{k+1} ∈ O_j` (sequence_no'ya göre) için:

```
S[o_{k+1}] ≥ C[o_k]
```

Bu tek kısıt hem "önceki operasyon bitmeden sonraki başlayamaz" kuralını hem de "bir job aynı anda birden fazla yerde olamaz" kuralını karşılar — çünkü operasyonlar zaten zaman ekseninde art arda dizilmiş oluyor.

### C3 — Makine çakışmaması (bir makine aynı anda iki iş yapamaz)

`M_o ∩ M_o' ≠ ∅` olan her `(o,o')` çifti (yapısal gözlem gereği: farklı job'lara ait, aynı `required_machine_type`) ve her `m ∈ M_o ∩ M_o'` için:

```
S[o'] ≥ C[o]  − BigM·(1−y[o,o']) − BigM·(2−x[o,m]−x[o',m])
S[o]  ≥ C[o'] − BigM·y[o,o']     − BigM·(2−x[o,m]−x[o',m])
```

Okunuşu: `x[o,m]=x[o',m]=1` ise (ikisi de gerçekten aynı `m`'ye atandıysa) son terim sıfırlanır ve `y[o,o']` hangisinin önce olduğunu zorunlu kılar. Aksi halde (biri ya da ikisi de `m`'ye atanmadıysa) kısıt otomatik gevşer, bağlayıcı olmaz.

### C4 — Bakım çakışmaması (bakımdaki makineye operasyon atanamaz)

Makine `m`'nin her bakım aralığı `k` (`[ms_{m,k}, me_{m,k}]`) için, `m ∈ M_o` olan her operasyon `o` ve yeni bir sıralama değişkeni `z[o,k] ∈ {0,1}` ile:

```
C[o] ≤ ms_{m,k} + BigM·(1−z[o,k]) + BigM·(1−x[o,m])
S[o] ≥ me_{m,k} − BigM·z[o,k]     − BigM·(1−x[o,m])
```

Aynı C3 mantığı: `x[o,m]=1` ise operasyon ya bakımdan tamamen önce bitecek (`z[o,k]=1`) ya da bakımdan tamamen sonra başlayacak (`z[o,k]=0`).

### C5 — Makine kapasitesi → **kısıt değil, uygunluk (eligibility) filtresi**

Önceki mesajda konuştuğumuz gibi: `Job.quantity`'nin etkisi Phase 2'de `processing_time` üretilirken zaten süreye gömüldü (`quantity_factor`). Ayrı bir "kapasite × süre ≥ miktar" eşitsizliği eklemek bu etkiyi iki kez saymak olur. Bunun yerine kapasite, `M_o` kümesinin **tanımına** giriyor:

```
M_o = { m ∈ M : machine_type(m) = required_machine_type(o)  AND  capacity_m ≥ capacity_min(o) }
```

Yani yetersiz kapasiteli makineler zaten `M_o`'ya girmiyor, `x[o,m]` değişkeni onlar için hiç tanımlanmıyor bile. `capacity_min(o)`'nun somut değeri Phase 7 implementasyonunda netleşecek.

### C6 — Release time (job, release_time'dan önce başlayamaz)

Job `j`'nin ilk operasyonu `o_1 ∈ O_j` için:

```
S[o_1] ≥ r_j
```

(Sonraki operasyonlar için ayrıca gerekmiyor — C2 zaten zinciri ileri taşıyor.)

### C7 — Tardiness doğrusallaştırma

`max(0, x)` ifadesi MILP'te doğrudan yazılamaz (doğrusal değildir); iki eşitsizlikle doğrusallaştırılır. Job `j`'nin son operasyonu `o_last ∈ O_j` için:

```
T[j] ≥ C[o_last] − d_j
T[j] ≥ 0
```

Solver, amaç fonksiyonunda `T[j]`'yi minimize etmeye çalıştığı için (Phase 6), `T[j]` gereksiz yere büyük seçilmez — bu iki eşitsizlik `T[j] = max(0, C[o_last]-d_j)` ile aynı sonucu garanti eder.

### C8 — Makine çalışma zamanı sınırı

Her operasyon `o` ve `m ∈ M_o` için:

```
S[o] ≥ available_from_m − BigM·(1−x[o,m])
C[o] ≤ available_until_m + BigM·(1−x[o,m])
```

### Tanımlayıcı Kısıt — Makespan (Phase 6'nın amaç fonksiyonu için gerekli)

```
C_max ≥ C[o]     ∀o∈O
```

### Big-M Seçimi Üzerine Not

`BigM = 2 × horizon_hours` (yani `336`) makul bir başlangıç değeri — `S[o]` ve `C[o]` zaten `[0, horizon_hours]` aralığında sınırlı olduğundan bu değer tüm "gevşetme" durumlarını güvenle kapsıyor. Gereğinden büyük bir `BigM` seçmek yanlış sonuç vermez ama solver'ı yavaşlatabilir/sayısal hassasiyet sorunu yaratabilir (OR literatüründe bilinen bir husus); Phase 8'de solver performansı zorlanırsa bu değeri sıkılaştırmayı (ör. her kısıt için ayrı, daha küçük bir M hesaplamayı) tekrar değerlendireceğiz.

---

## 6. Planlanan İçerik (henüz yazılmadı)

- **Phase 6 — Objective Function**: önce `min C_max`, sonra `min α·C_max + β·enerji_maliyeti`, sonra `+ γ·Σ T[j]`; α/β/γ seçim gerekçesi.
- **Phase 7'ye referans**: her formülün Pyomo kodundaki karşılığı (`optimization/variables.py`, `constraints.py`, `objective.py`).

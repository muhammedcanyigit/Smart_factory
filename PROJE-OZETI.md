# Şu Ana Kadar Ne Yaptık? (Basit Anlatım)

Bu dosya, projede şu ana kadar olan biteni **hiçbir teknik bilgi gerektirmeden**, sondan başa sırayla değil, baştan sona, hikaye gibi anlatıyor. Amaç: bir gün ara verip geri döndüğünde, ya da birine "biz ne yaptık" diye anlatman gerektiğinde, buraya bakıp 5 dakikada hatırlaman.

Diğer dosyalarla karışmasın diye: `CHANGELOG.md` "hangi dosya değişti" der (teknik), `docs/decision-log.md` "neden bu kararı verdik" der (teknik). Bu dosya ise "ne yaptık, niye yaptık, başımıza ne geldi" der — hiç teknik terim kullanmadan.

---

## Önce: Bu Proje Ne?

Bir fabrika düşün. İçinde makineler var, makineler ürün üretiyor. Her ürünün belirli işlemlerden geçmesi gerekiyor (önce kesim, sonra montaj, sonra paketleme gibi). Fabrika müdürü her gün şunu düşünüyor: "Hangi işi hangi makineye vereyim ki hem işler zamanında bitsin hem de elektrik faturası şişmesin?"

Biz bu soruyu bir bilgisayar programının çözmesini sağlıyoruz. Gerçek bir fabrikamız yok, o yüzden bilgisayarda **sahte ama gerçekçi** bir fabrika kurduk (gerçek fabrika verisi gibi davranan, ama uydurma sayılarla dolu bir sistem). Bu, senin bitirme projen.

---

## Faz 0 — Planı Yaptık

Kod yazmadan önce oturup "biz tam olarak ne yapacağız" diye yazdık: hangi bölümler olacak, hangi teknolojileri kullanacağız, ne kadar büyük bir iş bu. İnternette hazır bir "fabrika verisi" var mı diye araştırdık — tam istediğimiz gibi bir şey bulamadık (üç farklı parça buldu, ama tam uyan yoktu), o yüzden **kendi sahte verimizi** üretmeye karar verdik.

Ayrıca bir GitHub hesabı/deposu kurduk — bu, kodumuzun internette güvenli bir yedeğinin tutulduğu yer. Küçük bir karışıklık oldu (klasörün yanlış yerde olması) ama düzelttik.

## Faz 1 — Fabrikanın "Kutucuklarını" Tasarladık

Bir fabrikayı bilgisayara anlatmak için, önce "neyi kaydedeceğiz" diye karar verdik. 5 tane "kutucuk" (kategori) belirledik:
- **Makine**: hangi makine, ne tip, ne kadar verimli, kaç yaşında
- **İş (Job)**: hangi ürün, ne kadar miktar, ne zaman teslim edilmeli
- **Operasyon**: bir işin alt adımları (kesim, montaj, paketleme gibi)
- **Enerji Fiyatı**: saatine göre elektrik ne kadara geliyor
- **Bakım**: hangi makine ne zaman bakımda, çalışamıyor

## Faz 2 — Sahte Ama Gerçekçi Veri Ürettik

Bir program yazdık, bu program "hayali" bir fabrika üretiyor: 10 makine, 50 iş (küçük versiyon), veya istersek 50 makine 1000 iş (büyük versiyon). Önemli olan: bu sayılar rastgele değil, **mantıklı ilişkiler** içeriyor — mesela uzun süren bir iş daha çok elektrik harcıyor, yaşlı bir makine daha sık bozuluyor, gece elektriği gündüzden ucuz. Aynı "tohum sayısını" (SEED=42) kullandığımız sürece, program her seferinde **aynı** sahte fabrikayı üretiyor — bu önemli, çünkü bilimsel bir projede "ben bunu tekrar üretebiliyor muyum" sorusunun cevabı hep "evet" olmalı.

## Faz 3 — En Basit Planı Denedik (Karşılaştırma Noktası)

Henüz hiç "akıllı" bir şey yapmadan, en basit yöntemle bir plan çıkardık: işleri sıraya koy, makineler boşaldıkça ata. İki basit kural denedik: "önce gelen önce işlenir" (FCFS) ve "teslim tarihi yakın olan önce işlenir" (EDF).

Burada ilginç bir şey oldu: EDF'in FCFS'ten **daha kötü** sonuç verdiğini gördük (daha çok iş gecikti). İlk başta "bir hata mı yaptık" diye şüphelendik ama araştırınca gerçek bir sebebi olduğunu bulduk: fabrikada bazı makine tiplerinden sadece 1 tane vardı, bu tek makine bir "darboğaz" (tıkanma noktası) oluyordu, ve EDF bazı işleri öne alırken başkalarını daha çok geciktiriyordu. Bunu sakladık değil, olduğu gibi yazdık — çünkü bilimsel dürüstlük önemli.

Bu basit planlar, ileride "gerçekten daha akıllı bir yöntem işe yaradı mı" diye ölçebilmemiz için bir **karşılaştırma çıtası** oldu.

## Faz 4-6 — Matematiği Kurduk (Henüz Kod Yok)

Burada kağıt üzerinde (kod yazmadan) şunu tanımladık: bilgisayarın "karar vermesi gereken şeyler" ne (hangi iş hangi makineye, ne zaman başlayacak), "uyması gereken kurallar" ne (bir makine aynı anda 2 iş yapamaz, bakımdaki makineye iş verilemez, iş teslim tarihinden önce başlayamaz gibi 8 tane kural), ve "neyi en aza indirmeye çalışacağı" ne (süre + elektrik parası + gecikme cezası, hepsini dolar cinsine çevirip topladık).

Bu üçü (kararlar, kurallar, hedef) birleşince ortaya bir **matematik bulmacası** çıkıyor — bilgisayar bu bulmacayı çözerek en iyi planı bulacak.

## Faz 7 — Matematiği Bilgisayara Yazdırdık (İlk Gerçek Kod)

Kağıt üzerindeki matematiği, bilgisayarın anlayacağı bir dile (Pyomo adlı bir araç) çevirdik. Burada ilginç bir macera yaşadık: kullandığımız "çözücü" program (bilgisayara matematik bulmacasını çözdüren araç) bazen **sonsuza kadar donup kalıyordu**, hiçbir şey söylemeden. Sebebini araştırdık, üç farklı yöntemle test ettik, ve gerçekten bir yazılım hatası olduğunu bulduk (bizim hatamız değil, kullandığımız aracın hatası). Başka bir yönteme geçerek düzelttik.

Sonra, küçük ve elle kontrol edebileceğimiz bir örnekle ("2 makine, 2 iş" gibi minik bir senaryo) test ettik — bilgisayarın bulduğu cevap, elle hesapladığımızla birebir aynı çıktı. Yani **model doğru çalışıyor**, kanıtladık.

## Faz 8 — Hız Sorununu Çözdük

Küçük örnekte her şey mükemmeldi ama gerçek (162 işlemlik) veri setinde bilgisayar **60 saniyede hiçbir çözüm bile bulamadı**. Bu, kötü kod yazdığımız için değil — bu tip matematik bulmacalarının bilinen, zor bir özelliği.

İki şey yaptık:
1. Matematiksel formülasyonu daha "sıkı" hale getirdik (gereksiz gevşeklikleri kaldırdık) — bu, çözümü biraz hızlandırdı ama yeterli olmadı.
2. **En etkili çözüm**: bilgisayara "sıfırdan arama" yerine, Faz 3'teki basit planı "işte sana hazır, geçerli bir başlangıç noktası" diye verdik (buna "warm start" — ısınmış başlangıç deniyor). Sonuç inanılmazdı: **300 saniyeden 0.34 saniyeye** düştü ve bilgisayar bize "bu zaten en iyi çözüm, daha iyisi yok" diye kanıtladı.

Bir de şunu keşfettik: basit plan (Faz 3) zaten "en hızlı" olma konusunda neredeyse mükemmeldi — çünkü fabrikamız çok yoğun değildi. Asıl fark, **elektrik parası ve gecikme cezasını birlikte düşününce** ortaya çıkıyordu.

## Faz 9 — "Gerçekten İşe Yarıyor mu?" Sorusunu Cevapladık

Basit planla, akıllı (optimize edilmiş) planı yan yana koyduk. Sonuç: akıllı plan, toplam maliyeti (süre + elektrik + gecikme cezası, hepsi dolar cinsinden) **%5.22 azalttı**. Elektrik masrafı %21 düştü. Ama dürüst olmak gerekirse, her şey iyileşmedi — üretim süresi biraz uzadı, geciken iş sayısı biraz arttı. Çünkü bilgisayar "toplamda en ucuza" gelen planı arıyor, tek tek her şeyi değil.

---

## Şu An Neredeyiz?

24 aşamadan **10'unu bitirdik** (Faz 0'dan Faz 9'a kadar). Bir fabrikanın verisini ürettik, en basit planı kurduk, matematik bulmacasını kurup çözdürdük, ve "akıllı planın gerçekten işe yaradığını" kanıtladık.

## Sırada Ne Var?

**Faz 10**: Şu ana kadar "bir işlem ne kadar sürer" bilgisini biz uydurduk (sahte veri üretirken). Şimdi bunun yerine, bilgisayara geçmiş verilerden **öğrenmesini** öğreteceğiz — yapay zeka/makine öğrenmesi devreye giriyor. Sonra bu tahminleri, Faz 7-9'da kurduğumuz "en iyi planı bul" sistemine besleyeceğiz.

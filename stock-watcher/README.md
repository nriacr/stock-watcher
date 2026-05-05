# Stok Takip Home Assistant Add-on

Bu eklenti, verdiğiniz ürün sayfalarını düzenli aralıklarla kontrol eder. Sayfada stokta olduğunu gösteren ifadeler bulunursa Pushover üzerinden bildirim gönderir.

## Ayarlar

- `products`: Kontrol edilecek ürün listesi. Her ürün için `name` ve `url` girilir.
- `check_interval_minutes`: Kontrol sıklığı. Varsayılan 60 dakikadır.
- `in_stock_keywords`: Sayfada görülürse ürün stokta kabul edilen ifadeler.
- `out_of_stock_keywords`: Sayfada görülürse ürün stokta değil kabul edilen ifadeler. Bu liste önceliklidir.
- `pushover_user_key`: Pushover kullanıcı anahtarı.
- `pushover_api_token`: Pushover uygulama API token değeri.
- `notify_once`: Ürün stoktayken her ürün için yalnızca bir kere bildirim gönderir. Ürün tekrar stok dışı görünüp sonra stoğa girerse yeniden bildirir.

Örnek ürün listesi:

```yaml
products:
  - name: "Ekran Kartı"
    url: "https://magaza.example/urun-1"
  - name: "SSD"
    url: "https://magaza.example/urun-2"
```

## Home Assistant'a Ekleme

1. Bu klasörü GitHub'a yeni bir repository olarak yükleyin.
2. Home Assistant'ta `Ayarlar > Eklentiler > Eklenti Mağazası` sayfasına girin.
3. Sağ üstteki üç noktadan `Repositories` bölümünü açın.
4. GitHub repository linkinizi ekleyin.
5. `Stok Takip` eklentisini kurun.
6. Eklenti ayarlarına ürün linklerinizi ve Pushover bilgilerinizi girin.
7. Eklentiyi başlatın.

## Notlar

Bazı mağazalar stok bilgisini JavaScript ile sonradan yükler. Bu durumda sayfanın normal HTML içeriğinde stok yazısı görünmeyebilir. Böyle bir siteyle karşılaşırsanız ürün linkini ve sayfada stokta/stokta değil görünen metinleri netleştirerek anahtar kelimeleri güncelleyin.

# Stok Takip Home Assistant Add-on

Bu eklenti, verdiğiniz ürün sayfalarını düzenli aralıklarla kontrol eder. Her ürün kendi stok anahtar kelimeleriyle değerlendirilir ve stokta görünürse Pushover üzerinden bildirim gönderir.

## Ayarlar

- `pushover_user_key`: Pushover kullanıcı anahtarı.
- `pushover_api_token`: Pushover uygulama API token değeri.
- `check_interval_minutes`: Kontrol sıklığı. Varsayılan 60 dakikadır.
- `notify_once`: Ürün stoktayken her ürün için yalnızca bir kere bildirim gönderir. Ürün tekrar stok dışı görünüp sonra stoğa girerse yeniden bildirir.
- `request_timeout_seconds`: Sayfa ve Pushover istekleri için zaman aşımı.
- `user_agent`: Ürün sayfası kontrolünde kullanılacak tarayıcı kimliği.
- `products`: Kontrol edilecek ürün listesi. Her ürün için `name`, `url`, `in_stock_keywords` ve `out_of_stock_keywords` girilir.

Örnek ürün listesi:

```yaml
products:
  - name: "Ekran Kartı"
    url: "https://magaza.example/urun-1"
    in_stock_keywords:
      - "sepete ekle"
      - "stokta"
    out_of_stock_keywords:
      - "stokta yok"
      - "tükendi"
  - name: "SSD"
    url: "https://magaza.example/urun-2"
    in_stock_keywords:
      - "hemen al"
    out_of_stock_keywords:
      - "geçici olarak temin edilemiyor"
```

## Home Assistant'a Ekleme

1. Bu klasörü GitHub'a yeni bir repository olarak yükleyin.
2. Home Assistant'ta `Ayarlar > Eklentiler > Eklenti Mağazası` sayfasına girin.
3. Sağ üstteki üç noktadan `Repositories` bölümünü açın.
4. GitHub repository linkinizi ekleyin.
5. `Stok Takip` eklentisini kurun.
6. Eklenti ayarlarına Pushover bilgilerinizi ve ürün listenizi girin.
7. Eklentiyi başlatın.

## Notlar

Bazı mağazalar stok bilgisini JavaScript ile sonradan yükler. Bu durumda sayfanın normal HTML içeriğinde stok yazısı görünmeyebilir. Böyle bir siteyle karşılaşırsanız ürün linkini ve sayfada stokta/stokta değil görünen metinleri netleştirerek anahtar kelimeleri güncelleyin.

# Stok Takip Home Assistant Add-on

Bu eklenti, verdiğiniz ürün sayfalarını düzenli aralıklarla kontrol eder. Her ürün kendi stok anahtar kelimeleriyle değerlendirilir ve stokta görünürse Pushover üzerinden bildirim gönderir.

## Ayarlar

- `products`: Kontrol edilecek ürün listesi. Her ürün için `name`, `enabled`, `url`, `check_interval_minutes`, `in_stock_keywords` ve `out_of_stock_keywords` girilir.
- `pushover_user_key`: Pushover kullanıcı anahtarı.
- `pushover_api_token`: Pushover uygulama API token değeri.
- `notify_once_in_24h`: Ürün stokta kalmaya devam ederse aynı ürün için 24 saat boyunca tekrar bildirim göndermez. Ürün stok dışına düşerse sayaç sıfırlanır.
- `user_agent`: Ürün sayfasına istek atarken kullanılan tarayıcı kimliğidir. Genelde değiştirmeyin; site istekleri engellerse bilgisayarınızdaki Chrome veya Safari User-Agent değeriyle değiştirilebilir.

Örnek ürün listesi:

```yaml
products:
  - name: "Ekran Kartı"
    enabled: true
    url: "https://magaza.example/urun-1"
    check_interval_minutes: 15
    in_stock_keywords:
      - "sepete ekle"
      - "stokta"
    out_of_stock_keywords:
      - "stokta yok"
      - "tükendi"
  - name: "SSD"
    enabled: false
    url: "https://magaza.example/urun-2"
    check_interval_minutes: 120
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

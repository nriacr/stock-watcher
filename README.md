# Stok Takip Home Assistant Add-on Repository

Bu repository, Raspberry Pi 4 üzerinde Home Assistant OS içinde çalışacak bir stok takip eklentisi içerir.

Eklenti saat başı ürün sayfasını kontrol eder ve ürün stoğa girerse Pushover bildirimi gönderir.

## GitHub'a Yükleme

```bash
git init
git add .
git commit -m "Add Home Assistant stock watcher add-on"
git branch -M main
git remote add origin https://github.com/nriacr/stock-watcher.git
git push -u origin main
```

GitHub repository adresi: https://github.com/nriacr/stock-watcher

## Home Assistant'ta Kurulum

1. Home Assistant'ta `Ayarlar > Eklentiler > Eklenti Mağazası` bölümüne girin.
2. Sağ üst menüden `Repositories` kısmını açın.
3. GitHub repository adresinizi ekleyin.
4. `Stok Takip` eklentisini kurup ayarlarını doldurun.

## Gerekli Bilgiler

- Ürün linki
- Pushover User Key
- Pushover API Token
- Stokta olduğunu gösteren metinler
- Stokta olmadığını gösteren metinler

# Maske Deneyi (yarı-sentetik, gerçek yüz fotoğrafı)

Deneme sayısı: 4, süre: 20 s, HR ~ U(60,100) BPM, titreme frekansı ~ U(0.9, 2.5) Hz, titreme genliği %1 (güçlü: %2), baş ötelemesi 6 px

## Ortalama mutlak hata (BPM)

|                                                |   titreme |   titreme+hareket |   güçlü titreme+hareket |
|:-----------------------------------------------|----------:|------------------:|------------------------:|
| klasik (tüm yüz) / maskesiz                    |      3.14 |              4.77 |                    2.23 |
| klasik (tüm yüz) / ikili (klasik)              |     32.95 |             32.96 |                   32.93 |
| klasik (tüm yüz) / yumuşak (önerilen)          |      0.15 |              0.24 |                    0.14 |
| önerilen (füzyon+Viterbi) / maskesiz           |      0.07 |              0.27 |                    0.14 |
| önerilen (füzyon+Viterbi) / ikili (klasik)     |     32.94 |             32.98 |                   32.96 |
| önerilen (füzyon+Viterbi) / yumuşak (önerilen) |      0.08 |              0.09 |                    0.06 |

## Titreme frekansına kilitlenme oranı (%)

|                                                |   titreme |   titreme+hareket |   güçlü titreme+hareket |
|:-----------------------------------------------|----------:|------------------:|------------------------:|
| klasik (tüm yüz) / maskesiz                    |         0 |                 0 |                       0 |
| klasik (tüm yüz) / ikili (klasik)              |       100 |               100 |                     100 |
| klasik (tüm yüz) / yumuşak (önerilen)          |         0 |                 0 |                       0 |
| önerilen (füzyon+Viterbi) / maskesiz           |         0 |                 0 |                       0 |
| önerilen (füzyon+Viterbi) / ikili (klasik)     |       100 |               100 |                     100 |
| önerilen (füzyon+Viterbi) / yumuşak (önerilen) |         0 |                 0 |                       0 |

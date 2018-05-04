joe
===

A simple CLI trading client for stellar

What you can do with joe (append --test flag to run it on testnet):
1. Add/remove/Details for user
e.g.
```
> joe add_user GBGW5K72BGPT5RH6V42LKNCLEFCPJR4NLLPH65XG4SJWF4TRKMKYRO6U
> joe remove_user #remove the added user
> joe account #see the details of the added user
```

2. Add/remove trust for certain asset
e.g.
```
> joe trust CNY GAREELUB43IRHWEASCFBLKHURCGMHE5IF6XSE7EXDLACYHGRHM43RFOX
> joe detrust CNY
```

3. Place buy offer non-native asset using native asset (user will be prompted for secret key):
```
> joe buy CNY 100.5 2.2674 #buys 100.5 CNY at price 2.2674 CNY/XLM
```

4. Place sell offer for non-native asset to get native asset (user will be prompted for secret key):
```
> joe sell CNY 100.5 0.355 #sells 100.5 CNY at price 0.355 XLM/CNY
```

5. See the offers for the current user for specific asset
```
> joe list_offers CNY
```

6. Remove the specific offer (user will be prompted for secret key):
```
> joe remove_offer 4321934
```

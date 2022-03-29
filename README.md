# Disclaimer
This is a very simple trading bot, and I would hesitate to even call it a strategy. Please use this repo only as a reference and not to acutally use with your own money. I'm not responsible if this bot blows up your account!

# Simple Kucoin Bot
This bot will take a kucoin futures ticker and trade long only according to set parameters.

# Required Parameters
Provide these either via environment variables or in a .env file
* KUCOIN_API_KEY -> Ex: "this-is-the-key"
* KUCOIN_API_SECRET -> Ex: "this-is-the-secret"
* KUCOIN_API_PASSPHRASE -> Ex: "passphrase"
* KUCOIN_API_URL -> Ex: "https://api-futures.kucoin.com"
* KUCOIN_PAIR -> Ex: "ETHUSDTM"
* KUCOIN_MAX_LEVERAGE -> Ex: "10.0"
* KUCOIN_TAKE_PROFIT_PERCENT -> Ex: "50.0"
* KUCOIN_STOP_LOSS_PERCENT -> Ex: "15.0"
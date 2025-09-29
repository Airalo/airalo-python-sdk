# Airalo Python SDK
Airalo's Python SDK provides simple integration with the REST API and an extra layer of convenience on top.
The SDK supports:
- automatic authentication
- optional caching and rate‑limit handling
- fetching packages: local, global, country, and all combined
- auto‑pagination on package endpoints
- ordering packages
- bulk ordering different packages and quantities at once
- top‑up ordering
- unified JSON responses as standard Python dicts
- works on Linux, macOS, and Windows

# Requisites
- Python >= `3.11`
- `requests` installed (the SDK depends on it)

# Installation
Install via pip:
```bash
pip install airalo-sdk
```

# Initialization
Object usage:
```python
from airalo import Airalo

alo = Airalo({
    "client_id": "<YOUR_API_CLIENT_ID>",     # mandatory
    "client_secret": "<YOUR_API_CLIENT_SECRET>",  # mandatory
})

all_packages = alo.get_all_packages(flat=True)
```

# Responses
The SDK returns standard Python dicts. You can access keys directly or convert to strings with `json.dumps` if needed.

# Methods Interface
<h2> Packages </h2>

>**_NOTE:_**  
>Passing `True` to the `flat` parameter makes the response significantly more compact and easy to handle. However it differs from the main one returned from the endpoints. Be mindful when you need the original vs the compact version.

`def get_all_packages(flat: bool = False, limit: int | None = None, page: int | None = None) -> dict | None`  
Fetching all Airalo packages. By default the response mirrors the packages REST endpoint (more here: https://developers.partners.airalo.com/get-packages-11883036e0). Passing `flat=True` returns package objects in a single data object, example:
```json
{
  "data": [
    {
      "package_id": "meraki-mobile-7days-1gb",
      "slug": "greece",
      "type": "sim",
      "price": 5,
      "net_price": 4,
      "amount": 1024,
      "day": 7,
      "is_unlimited": false,
      "title": "1 GB - 7 Days",
      "data": "1 GB",
      "short_info": "This eSIM doesn't come with a phone number.",
      "voice": null,
      "text": null,
      "plan_type": "data",
      "activation_policy": "first-usage",
      "operator": {
        "title": "Meraki Mobile",
        "is_roaming": true,
        "info": [
          "LTE Data-only eSIM.",
          "Rechargeable online with no expiry.",
          "Operates on the Wind network in Greece."
        ]
      },
      "countries": [
        "GR"
      ],
      "prices": {
        "net_price": {
          "AUD": 6.44,
          "BRL": 23.52,
          "GBP": 3.2,
          "AED": 14.68,
          "EUR": 3.84,
          "ILS": 14.32,
          "JPY": 616.67,
          "MXN": 82.72,
          "USD": 4.0,
          "VND": 100330.0
        },
        "recommended_retail_price": {
          "AUD": 10.07,
          "BRL": 36.75,
          "GBP": 5.0,
          "AED": 22.93,
          "EUR": 6.01,
          "ILS": 22.38,
          "JPY": 963.54,
          "MXN": 129.25,
          "USD": 6.25,
          "VND": 156765.62
        }
      }
    },
    {
      "package_id": "meraki-mobile-7days-1gb-topup",
      "slug": "greece",
      "type": "topup",
      "price": 5,
      "net_price": 4,
      "amount": 1024,
      "day": 7,
      "is_unlimited": false,
      "title": "1 GB - 7 Days",
      "data": "1 GB",
      "short_info": null,
      "voice": null,
      "text": null,
      "plan_type": "data",
      "activation_policy": "first-usage",
      "operator": {
        "title": "Meraki Mobile",
        "is_roaming": true,
        "info": [
          "LTE Data-only eSIM.",
          "Rechargeable online with no expiry.",
          "Operates on the Wind network in Greece."
        ]
      },
      "countries": [
        "GR"
      ],
      "prices": {
        "net_price": {
          "AUD": 6.44,
          "BRL": 23.52,
          "GBP": 3.2,
          "AED": 14.68,
          "EUR": 3.84,
          "ILS": 14.32,
          "JPY": 616.67,
          "MXN": 82.72,
          "USD": 4.0,
          "VND": 100330.0
        },
        "recommended_retail_price": {
          "AUD": 10.07,
          "BRL": 36.75,
          "GBP": 5.0,
          "AED": 22.93,
          "EUR": 6.01,
          "ILS": 22.38,
          "JPY": 963.54,
          "MXN": 129.25,
          "USD": 6.25,
          "VND": 156765.62
        }
      }
    }
  ]
}
```
By default no limit is applied if `limit` is empty.  
By default it auto‑paginates all pages (multiple calls) or if `page` is provided it will be the starting index.

`def get_local_packages(flat: bool = False, limit: int | None = None, page: int | None = None) -> dict | None`  
Fetching local packages. Same behavior as above.

`def get_global_packages(flat: bool = False, limit: int | None = None, page: int | None = None) -> dict | None`  
Fetching global packages. Same behavior as above.

`def get_country_packages(country_code: str, flat: bool = False, limit: int | None = None) -> dict | None`  
Fetching country‑specific packages. Same behavior as above.

`def get_sim_packages(flat: bool = False, limit: int | None = None, page: int | None = None) -> dict | None`  
Fetching SIM‑only packages without top‑ups. Same behavior as above.

<h2> Orders </h2>

`def order(package_id: str, quantity: int, description: str | None = None) -> dict | None`  
Places an order for a given package id and calls the `order` endpoint.  
Full response example: https://developers.partners.airalo.com/submit-order-11883024e0
```python
order = alo.order(package_id, 1)
```

`def order_async(package_id: str, quantity: int, webhook_url: str | None = None, description: str | None = None) -> dict | None`  
Places an async order for a given package id and calls the `order-async` endpoint.  
Docs: https://developers.partners.airalo.com/submit-order-async-11883025e0
```python
order_async = alo.order_async(package_id, 1, "https://your-webhook.com")
```

`def order_with_email_sim_share(package_id: str, quantity: int, esim_cloud: dict, description: str | None = None) -> dict | None`  
Places an order and emails the end user with an eSIMs Cloud sharing link (and optional PDF). `esim_cloud` must include `to_email` and `sharing_option` of `["link"]`, `["pdf"]`, or both. Optional `copy_address` list.
```python
order = alo.order_with_email_sim_share(
  package_id, 1,
  {
    "to_email": "end.user.email@domain.com",        # mandatory
    "sharing_option": ["link", "pdf"],              # mandatory
    "copy_address": ["other.user.email@domain.com"] # optional
  }
)
```

`def order_bulk(packages: dict[str, int], description: str | None = None) -> dict | None`  
Parameters: `packages` mapping where the key is the package id and the value is the desired quantity.  
Parallel ordering for multiple packages (up to 50 different package ids) within the same call. Example:
```python
all_packages = alo.get_all_packages(True)
first_package = all_packages["data"][0]["package_id"]
second_package = all_packages["data"][1]["package_id"]

orders = alo.order_bulk({
    first_package: 2,
    second_package: 1,
})
```
Example response:
```json
{
  "change-7days-1gb": {
    "data": {
      "id": 77670,
      "code": "20240514-077670",
      "currency": "USD",
      "package_id": "change-7days-1gb",
      "quantity": 1,
      "type": "sim",
      "description": "Bulk order placed via Airalo Python SDK",
      "esim_type": "Prepaid",
      "validity": 7,
      "package": "Change-1 GB - 7 Days",
      "data": "1 GB",
      "price": 4.5,
      "created_at": "2024-05-14 11:48:47",
      "manual_installation": "<p><b>eSIM name:</b> Change</p><p><b>Coverage: </b>United States</p><p><b>To manually activate the eSIM on your eSIM capable device:</b></p><ol><li>Settings > Cellular/Mobile > Add Cellular/Mobile Plan.</li><li>Manually enter the SM-DP+ Address and activation code.</li><li>Confirm eSIM plan details.</li><li>Label the eSIM.</li></ol><p><b>To access Data:</b></p><ol><li>Enable data roaming.</li></ol>",
      "qrcode_installation": "<p><b>eSIM name:</b> Change</p><p><b>Coverage: </b>United States</p><p><b>To activate the eSIM by scanning the QR code on your eSIM capable device you need to print or display this QR code on other device:</b></p><ol><li>Settings > Cellular/Mobile > Add Cellular/Mobile Plan.</li><li>Scan QR code.</li><li>Confirm eSIM plan details.</li><li>Label the eSIM.</li></ol><p><b>To access Data:</b></p><ol><li>Enable data roaming.</li></ol>",
      "installation_guides": {
        "en": "https://www.airalo.com/help/getting-started-with-airalo"
      },
      "text": null,
      "voice": null,
      "net_price": 3.6,
      "sims": [
        {
          "id": 102795,
          "created_at": "2024-05-14 11:48:47",
          "iccid": "893000000000034143",
          "lpa": "lpa.airalo.com",
          "imsis": null,
          "matching_id": "TEST",
          "qrcode": "LPA:1$lpa.airalo.com$TEST",
          "qrcode_url": "https://airalo.com/qr?expires=1802000927&id=137975&signature=b4e731d218fdc707b677c89d54d41773d250a38c160cf7d97f6e9493b5fec0ee",
          "airalo_code": null,
          "apn_type": "automatic",
          "apn_value": null,
          "is_roaming": true,
          "confirmation_code": null,
          "apn": {
            "ios": {
              "apn_type": "automatic",
              "apn_value": null
            },
            "android": {
              "apn_type": "automatic",
              "apn_value": null
            }
          },
          "msisdn": null
        },
        {
          "id": 102795,
          "created_at": "2024-05-14 11:48:47",
          "iccid": "893000000000034143",
          "lpa": "lpa.airalo.com",
          "imsis": null,
          "matching_id": "TEST",
          "qrcode": "LPA:1$lpa.airalo.com$TEST",
          "qrcode_url": "https://airalo.com/qr?expires=1802000927&id=137975&signature=b4e731d218fdc707b677c89d54d41773d250a38c160cf7d97f6e9493b5fec0ee",
          "airalo_code": null,
          "apn_type": "automatic",
          "apn_value": null,
          "is_roaming": true,
          "confirmation_code": null,
          "apn": {
            "ios": {
              "apn_type": "automatic",
              "apn_value": null
            },
            "android": {
              "apn_type": "automatic",
              "apn_value": null
            }
          },
          "msisdn": null
        }
      ]
    },
    "meta": {
      "message": "success"
    }
  },
  "change-7days-1gb-topup": {
    "data": {
      "id": 77671,
      "code": "20240514-077671",
      "currency": "USD",
      "package_id": "change-7days-1gb-topup",
      "quantity": 1,
      "type": "sim",
      "description": "Bulk order placed via Airalo Python SDK",
      "esim_type": "Prepaid",
      "validity": 7,
      "package": "Change-1 GB - 7 Days",
      "data": "1 GB",
      "price": 4.5,
      "created_at": "2024-05-14 11:48:47",
      "manual_installation": "<p><b>eSIM name:</b> Change</p><p><b>Coverage: </b>United States</p><p><b>To manually activate the eSIM on your eSIM capable device:</b></p><ol><li>Settings > Cellular/Mobile > Add Cellular/Mobile Plan.</li><li>Manually enter the SM-DP+ Address and activation code.</li><li>Confirm eSIM plan details.</li><li>Label the eSIM.</li></ol><p><b>To access Data:</b></p><ol><li>Enable data roaming.</li></ol>",
      "qrcode_installation": "<p><b>eSIM name:</b> Change</p><p><b>Coverage: </b>United States</p><p><b>To activate the eSIM by scanning the QR code on your eSIM capable device you need to print or display this QR code on other device:</b></p><ol><li>Settings > Cellular/Mobile > Add Cellular/Mobile Plan.</li><li>Scan QR code.</li><li>Confirm eSIM plan details.</li><li>Label the eSIM.</li></ol><p><b>To access Data:</b></p><ol><li>Enable data roaming.</li></ol>",
      "installation_guides": {
        "en": "https://www.airalo.com/help/getting-started-with-airalo"
      },
      "text": null,
      "voice": null,
      "net_price": 3.6,
      "sims": [
        {
          "id": 102796,
          "created_at": "2024-05-14 11:48:47",
          "iccid": "893000000000034144",
          "lpa": "lpa.airalo.com",
          "imsis": null,
          "matching_id": "TEST",
          "qrcode": "LPA:1$lpa.airalo.com$TEST",
          "qrcode_url": "https://airalo.com/qr?expires=1802000927&id=137976&signature=978adede2174b6de7d2502841d6d901d417d643570dd6172c71733cde5f72503",
          "airalo_code": null,
          "apn_type": "automatic",
          "apn_value": null,
          "is_roaming": true,
          "confirmation_code": null,
          "apn": {
            "ios": {
              "apn_type": "automatic",
              "apn_value": null
            },
            "android": {
              "apn_type": "automatic",
              "apn_value": null
            }
          },
          "msisdn": null
        }
      ]
    },
    "meta": {
      "message": "success"
    }
  }
}
```
>**_NOTE:_**  
>Each package id is a key in the returned response. The quantity of `sims` represents the ordered quantity.  
><b>If an error occurs in a parallel order, the error response is assigned to that package id key. Validate each item.</b>

Example error:
```json
{
  "change-7days-1gb": {"data":{"quantity":"The quantity may not be greater than 50."},"meta":{"message":"the parameter is invalid"}},
  "change-7days-1gb-topup": {
    "data": {
      "id": 77671,
      "code": "20240514-077671",
      "currency": "USD",
      "package_id": "change-7days-1gb-topup",
      "quantity": 1,
      "type": "sim",
      "description": "Bulk order placed via Airalo Python SDK",
      "esim_type": "Prepaid",
      "validity": 7,
      "package": "Change-1 GB - 7 Days",
      "data": "1 GB",
      "price": 4.5,
      "created_at": "2024-05-14 11:48:47",
      "manual_installation": "<p><b>eSIM name:</b> Change</p><p><b>Coverage: </b>United States</p><p><b>To manually activate the eSIM on your eSIM capable device:</b></p><ol><li>Settings > Cellular/Mobile > Add Cellular/Mobile Plan.</li><li>Manually enter the SM-DP+ Address and activation code.</li><li>Confirm eSIM plan details.</li><li>Label the eSIM.</li></ol><p><b>To access Data:</b></p><ol><li>Enable data roaming.</li></ol>",
      "qrcode_installation": "<p><b>eSIM name:</b> Change</p><p><b>Coverage: </b>United States</p><p><b>To activate the eSIM by scanning the QR code on your eSIM capable device you need to print or display this QR code on other device:</b></p><ol><li>Settings > Cellular/Mobile > Add Cellular/Mobile Plan.</li><li>Scan QR code.</li><li>Confirm eSIM plan details.</li><li>Label the eSIM.</li></ol><p><b>To access Data:</b></p><ol><li>Enable data roaming.</li></ol>",
      "installation_guides": {
        "en": "https://www.airalo.com/help/getting-started-with-airalo"
      },
      "text": null,
      "voice": null,
      "net_price": 3.6,
      "sims": [
        {
          "id": 102796,
          "created_at": "2024-05-14 11:48:47",
          "iccid": "893000000000034144",
          "lpa": "lpa.airalo.com",
          "imsis": null,
          "matching_id": "TEST",
          "qrcode": "LPA:1$lpa.airalo.com$TEST",
          "qrcode_url": "https://airalo.com/qr?expires=1802000927&id=137976&signature=978adede2174b6de7d2502841d6d901d417d643570dd6172c71733cde5f72503",
          "airalo_code": null,
          "apn_type": "automatic",
          "apn_value": null,
          "is_roaming": true,
          "confirmation_code": null,
          "apn": {
            "ios": {
              "apn_type": "automatic",
              "apn_value": null
            },
            "android": {
              "apn_type": "automatic",
              "apn_value": null
            }
          },
          "msisdn": null
        }
      ]
    },
    "meta": {
      "message": "success"
    }
  }
}
```

`def order_async_bulk(packages: dict[str, int], webhook_url: str | None = None, description: str | None = None) -> dict | None`  
Parallel async ordering for multiple packages (up to 50 different ids) within the same call.
```python
orders = alo.order_async_bulk({ first_package: 2, second_package: 1 }, "https://your-webhook.com")
```
Example response:
```json
{
  "change-7days-1gb": {
    "data": {
      "request_id": "PWhB8cr-QXPssdA2O2RRvzaeT",
      "accepted_at": "2024-07-17 10:10:31"
    },
    "meta": {
      "message": "success"
    }
  },
  "change-30days-10gb": {
    "data": {
      "request_id": "nYcMsdlgtCsE_sXFAE0vdikSd",
      "accepted_at": "2024-07-17 10:10:31"
    },
    "meta": {
      "message": "success"
    }
  }
}
```

`def order_bulk_with_email_sim_share(packages: dict[str, int], esim_cloud: dict, description: str | None = None) -> dict | None`  
Parallel ordering for multiple packages with eSIMs Cloud email share.
```python
orders = alo.order_bulk_with_email_sim_share(
  { first_package: 2, second_package: 1 },
  {
    "to_email": "end.user.email@domain.com",           # mandatory
    "sharing_option": ["link", "pdf"],                 # mandatory
    "copy_address": ["another.user.email@domain.com"], # optional
  }
)
```

<h2> Vouchers </h2>

`def voucher(usage_limit: int, amount: int, quantity: int, is_paid: bool | None = False, voucher_code: str | None = None) -> dict | None`  
Calls the `voucher` endpoint.
```python
vouchers = alo.voucher(40, 22, 1, False, "ABC111")
```
Example response:
```json
{
  "data": {
    "id": 8,
    "code": "ABC111",
    "usage_limit": 40,
    "amount": 22,
    "is_paid": false,
    "created_at": "2024-06-10 07:23:24"
  },
  "meta": { "message": "success" }
}
```

<h2> Esim Vouchers </h2>

`def esim_vouchers(vouchers: list[dict]) -> dict | None`  
Calls `voucher/esim`. Full response: https://developers.partners.airalo.com/esim-voucher-11883065e0
```python
vouchers = alo.esim_vouchers([{ "package_id": "package_slug", "quantity": 2 }])
```
Example response:
```json
{
  "data": [
    {
      "package_id": "package_slug",
      "codes": [
        "BIXLAAAA",
        "BSXLAAAA"
      ]
    }
  ],
  "meta": {
    "message": "success"
  }
}
```

<h2> Topups </h2>

`def topup(package_id: str, iccid: str, description: str | None = None) -> dict | None`  
Places a top‑up for a given `package_id` and `iccid`. Full response: https://developers.partners.airalo.com/submit-top-up-order-11883026e0
```python
order = alo.order(package_id, 1)
iccid = order["data"]["sims"][0]["iccid"]
topup = alo.topup(package_id, iccid)
```

<h2> Sim Usage </h2>

`def sim_usage(iccid: str) -> dict | None`  
Calls `simUsage`. Full response: https://developers.partners.airalo.com/get-usage-data-text-voice-11883030e0
```python
usage = alo.sim_usage(iccid)
```

`def sim_usage_bulk(iccids: list[str]) -> dict | None`  
Parallel usage calls for multiple ICCIDs.  
```python
usage = alo.sim_usage_bulk(["870000000001", "870000000002", "870000000003", "870000000004"])
```
>**_NOTE:_**  
>Each ICCID is a key in the returned response.  
><b>If an error occurs in a parallel usage call, the error response is assigned to that ICCID key.</b>

<h2> Sim Topups </h2>

`def get_sim_topups(iccid: str) -> dict | None`  
Fetches available top‑ups for an `iccid`. Full response: https://developers.partners.airalo.com/get-top-up-package-list-11883031e0
```python
available_topups = alo.get_sim_topups(iccid)
```

<h2> Sim Package History </h2>

`def get_sim_package_history(iccid: str) -> dict | None`  
Fetches package history for an `iccid`. Full response: https://developers.partners.airalo.com/get-esim-package-history-11883032e0
```python
sim_package_history = alo.get_sim_package_history(iccid)
```

<h2> Exchange Rates </h2>

`def get_exchange_rates(date: str | None = None, source: str | None = None, from_currency: str | None = None, to: str | None = None) -> dict | None`  
Fetches exchange rates.  
`date` - `YYYY-MM-DD` format. If not provided, current date is used.  
`source` - keep `None`.  
`from_currency` - usually `USD`.  
`to` - comma‑separated list of currency codes, e.g. `"AUD,GBP,EUR"`.
```python
exchange_rates = alo.get_exchange_rates()
```
Example:
```python
exchange_rates = alo.get_exchange_rates("2025-01-30", None, None, "AUD,GBP,EUR")
```
```json
{
    "data": {
        "date": "2025-01-30",
        "rates": [
            {
                "from": "USD",
                "mid": "1.6059162",
                "to": "AUD"
            },
            {
                "from": "USD",
                "mid": "0.80433592",
                "to": "GBP"
            },
            {
                "from": "USD",
                "mid": "0.96191527",
                "to": "EUR"
            }
        ]
    },
    "meta": {
        "message": "success"
    }
}
```

<h2> Sim Instructions </h2>

`def get_installation_instructions(params: dict) -> dict | None`  
Provide `{"iccid": "<ICCID>", "language": "en"}`. Full response: https://developers.partners.airalo.com/get-installation-instructions-11883029e0
```python
instructions = alo.get_installation_instructions({"iccid": "893000000000002115", "language": "en"})
```
Example response:
```json
{
  "data": {
    "instructions": {
      "language": "EN",
      "ios": [
        {
          "model": null,
          "version": "15.0,14.0.,13.0,12.0",
          "installation_via_qr_code": {
            "steps": {
              "1": "Go to Settings > Cellular/Mobile > Add Cellular/Mobile Plan.",
              "2": "Scan the QR Code.",
              "3": "Tap on 'Add Cellular Plan'.",
              "4": "Label the eSIM.",
              "5": "Choose preferred default line to call or send messages.",
              "6": "Choose the preferred line to use with iMessage, FaceTime, and Apple ID.",
              "7": "Choose the eSIM plan as your default line for Cellular Data and do not turn on 'Allow Cellular Data Switching' to prevent charges on your other line.",
              "8": "Your eSIM has been installed successfully, please scroll down to see the settings for accessing data."
            },
            "qr_code_data": "5a30d830-cfa9-4353-8d76-f103351d53b6",
            "qr_code_url": "https://www.conroy.biz/earum-dolor-qui-molestiae-at"
          },
          "installation_manual": {
            "steps": {
              "1": "Go to Settings > Cellular/Mobile > Add Cellular/Mobile Plan.",
              "2": "Tap on 'Enter Details Manually'.",
              "3": "Enter your SM-DP+ Address and Activation Code.",
              "4": "Tap on 'Add Cellular Plan'.",
              "5": "Label the eSIM.",
              "6": "Choose preferred default line to call or send messages.",
              "7": "Choose the preferred line to use with iMessage, FaceTime, and Apple ID.",
              "8": "Choose the eSIM plan as your default line for Cellular Data and do not turn on 'Allow Cellular Data Switching' to prevent charges on your other line.",
              "9": "Your eSIM has been installed successfully, please scroll down to see the settings for accessing data."
            },
            "smdp_address_and_activation_code": "6a7f7ab6-6469-461d-8b17-2ee5c0207d22"
          },
          "network_setup": {
            "steps": {
              "1": "Select your  eSIM under 'Cellular Plans'.",
              "2": "Ensure that 'Turn On This Line' is toggled on.",
              "3": "Go to 'Network Selection' and select the supported network.",
              "4": "Need help? Chat with us."
            },
            "apn_type": "manual",
            "apn_value": "globaldata",
            "is_roaming": null
          }
        },
        {
          "model": null,
          "version": null,
          "installation_via_qr_code": {
            "steps": {
              "1": "Go to Settings > Cellular/Mobile Data > Add eSIM or Set up Cellular/Mobile Service > Use QR Code on your device. ",
              "2": "Scan the QR code available on the  app, then tap “Continue” twice and wait for a while. Your eSIM will connect to the network, this may take a few minutes, then tap “Done”.",
              "3": "Choose a label for your new eSIM plan.",
              "4": "Choose “Primary” for your default line, then tap “Continue”.",
              "5": "Choose “Primary” you want to use with iMessage and FaceTime for your Apple ID, then tap “Continue”.",
              "6": "Choose your new eSIM plan for cellular/mobile data, then tap “Continue”."
            },
            "qr_code_data": "5a30d830-cfa9-4353-8d76-f103351d53b6",
            "qr_code_url": "https://www.conroy.biz/earum-dolor-qui-molestiae-at"
          },
          "installation_manual": {
            "steps": {
              "1": "Go to Settings > Cellular/Mobile Data > Add eSIM or Set up Cellular/Mobile Service > Use QR Code on your device.",
              "2": "Tap “Enter Details Manually” and enter the SM-DP+ Address and Activation Code available on the  app by copying them, tap “Next”, then tap “Continue” twice and wait for a while. Your eSIM will connect to the network, this may take a few minutes, then tap “Done”.",
              "3": "Choose a label for your new eSIM plan.",
              "4": "Choose “Primary” for your default line, then tap “Continue”.",
              "5": "Choose “Primary” you want to use with iMessage and FaceTime for your Apple ID, then tap “Continue”.",
              "6": "Choose your new eSIM plan for cellular/mobile data, then tap “Continue”."
            },
            "smdp_address_and_activation_code": "6a7f7ab6-6469-461d-8b17-2ee5c0207d22"
          },
          "network_setup": {
            "steps": {
              "1": "Go to “Cellular/Mobile Data”, then select the recently downloaded eSIM on your device. Enable the “Turn On This Line” toggle, then select your new eSIM plan for cellular/mobile data. ",
              "2": "Tap “Network Selection”, disable the “Automatic” toggle, then select the supported network available on the  app manually if your eSIM has connected to the wrong network."
            },
            "apn_type": "manual",
            "apn_value": "globaldata",
            "is_roaming": null
          }
        }
      ],
      "android": [
        {
          "model": null,
          "version": null,
          "installation_via_qr_code": {
            "steps": {
              "1": "Go to Settings > Connections > SIM Card Manager.",
              "2": "Tap on 'Add Mobile Plan'.",
              "3": "Tap on 'Scan Carrier QR Code' and tap on 'Add'.",
              "4": "When the plan has been registered, tap 'Ok' to turn on a new mobile plan.",
              "5": "Your eSIM has been installed successfully, please scroll down to see the settings for accessing data."
            },
            "qr_code_data": "5a30d830-cfa9-4353-8d76-f103351d53b6",
            "qr_code_url": "https://www.conroy.biz/earum-dolor-qui-molestiae-at"
          },
          "installation_manual": {
            "steps": {
              "1": "Go to Settings > Connections > SIM Card Manager.",
              "2": "Tap on 'Add Mobile Plan'.",
              "3": "Tap on 'Scan Carrier QR Code' and tap on 'Enter code instead'.",
              "4": "Enter the Activation Code (SM-DP+ Address & Activation Code).",
              "5": "When the plan has been registered, tap 'Ok' to turn on a new mobile plan.",
              "6": "Your eSIM has been installed successfully, please scroll down to see the settings for accessing data."
            },
            "smdp_address_and_activation_code": "6a7f7ab6-6469-461d-8b17-2ee5c0207d22"
          },
          "network_setup": {
            "steps": {
              "1": "In the 'SIM Card Manager' select your  eSIM.",
              "2": "Ensure that your eSIM is turned on under 'Mobile Networks'.",
              "3": "Enable the Mobile Data.",
              "4": "Go to Settings > Connections > Mobile networks > Network Operators.",
              "5": "Ensure that the supported network is selected.",
              "6": "Need help? Chat with us."
            },
            "apn_type": "automatic",
            "apn_value": "globaldata",
            "is_roaming": null
          }
        },
        {
          "model": null,
          "version": null,
          "installation_via_qr_code": {
            "steps": {
              "1": "Go to Settings > Network & internet.",
              "2": "Tap on the '+' (Add) icon next to the Mobile network.",
              "3": "Tap 'Next' when asked, “Don’t have a SIM card?”.",
              "4": "Scan the QR Code.",
              "5": "Your eSIM has been installed successfully, please scroll down to see the settings for accessing data."
            },
            "qr_code_data": "5a30d830-cfa9-4353-8d76-f103351d53b6",
            "qr_code_url": "https://www.conroy.biz/earum-dolor-qui-molestiae-at"
          },
          "installation_manual": {
            "steps": {
              "1": "Go to Settings > Network & internet.",
              "2": "Tap on the '+' (Add) icon next to the Mobile network.",
              "3": "Tap on 'Next' when asked, “Don’t have a SIM card?”.",
              "4": "Tap 'Enter Code Manually'. You will be asked to enter your Activation Code (SM-DP+ Adress & Activation Code).",
              "5": "Your eSIM has been installed successfully, please scroll down to see the settings for accessing data."
            },
            "smdp_address_and_activation_code": "6a7f7ab6-6469-461d-8b17-2ee5c0207d22"
          },
          "network_setup": {
            "steps": {
              "1": "Go to Network & internet and tap on 'Mobile network'.",
              "2": "Connect manually to the supported network.",
              "3": "Turn on eSIM under 'Mobile network'.",
              "4": "Enable the Mobile Data.",
              "5": "Need help? Chat with us."
            },
            "apn_type": "automatic",
            "apn_value": "globaldata",
            "is_roaming": null
          }
        },
        {
          "model": "Galaxy",
          "version": "1",
          "installation_via_qr_code": {
            "steps": {
              "1": "Go to “Settings”, tap “Connections”, then tap “SIM card manager” on your device.",
              "2": "Tap “Add mobile plan”, then tap “Scan carrier QR code”.",
              "3": "Tap “Enter activation code”.",
              "4": "Enter the SM-DP+ Address & Activation Code by copying it, tap “Connect”, then tap “Confirm”."
            },
            "qr_code_data": "5a30d830-cfa9-4353-8d76-f103351d53b6",
            "qr_code_url": "https://www.conroy.biz/earum-dolor-qui-molestiae-at"
          },
          "installation_manual": {
            "steps": {
              "1": "Go to “Settings”, tap “Connections”, then tap “SIM card manager” on your device.",
              "2": "Tap “Add mobile plan”, then tap “Scan carrier QR code”.",
              "3": "Tap “Enter activation code”.",
              "4": "Enter the SM-DP+ Address & Activation Code by copying it, tap “Connect”, then tap “Confirm”."
            },
            "smdp_address_and_activation_code": "6a7f7ab6-6469-461d-8b17-2ee5c0207d22"
          },
          "network_setup": {
            "steps": {
              "1": "Go to “Settings”, tap “Connections”, then tap “SIM card manager” on your device.",
              "2": "Tap “Add mobile plan”, then tap “Scan carrier QR code”.",
              "3": "Tap “Enter activation code”.",
              "4": "Enter the SM-DP+ Address & Activation Code by copying it, tap “Connect”, then tap “Confirm”."
            },
            "apn_type": "automatic",
            "apn_value": "globaldata",
            "is_roaming": null
          }
        }
      ]
    }
  },
  "meta": {
    "message": "success"
  }
}
```

<h2> Future Orders </h2>

`def create_future_order(package_id: str, quantity: int, due_date: str, webhook_url: str | None = None, description: str | None = None, brand_settings_name: str | None = None, to_email: str | None = None, sharing_option: list[str] | None = None, copy_address: list[str] | None = None) -> dict | None`  
Places a future order via `future-orders`.  
>**_NOTE:_**  
>`due_date` must be in UTC and format `YYYY-MM-DD HH:MM`.
```python
future_order = alo.create_future_order(
  "package_id", 1, "2025-03-10 10:00",
  "https://your-webhook.com",
  "Test description from Python SDK",
  None,
  "end.user.email@domain.com",
  ["link", "pdf"],
  ["other.user.email@domain.com"]
)
```
Example response:
```json
{
  "data": {
    "request_id": "bUKdUc0sVB_nXJvlz0l8rTqYR",
    "due_date": "2025-03-10 10:00",
    "latest_cancellation_date": "2025-03-09 10:00"
  },
  "meta": { "message": "success" }
}
```

<h2> Cancel Future Orders </h2>

`def cancel_future_order(request_ids: list[str]) -> dict | None`  
Cancels future orders via `cancel-future-orders`.
```python
cancel_future = alo.cancel_future_order(["request_id_1", "request_id_2", "request_id_3"])
```
Example response:
```json
{ "data": {}, "meta": { "message": "Future orders cancelled successfully" } }
```

<h2> Get Compatible Devices </h2>

`def get_compatible_devices() -> dict | None`  
Calls the compatible eSIM devices endpoint.
```python
devices = alo.get_compatible_devices()
```
Example response:
```json
{
    "data": [
        {
            "os": "android",
            "brand": "ABCTECH",
            "name": "X20"
        },
        {
            "os": "android",
            "brand": "Asus",
            "name": "ZenFone Max Pro M1 (ZB602KL) (WW) / Max Pro M1 (ZB601KL) (IN)"
        },
        {
            "os": "android",
            "brand": "Asus",
            "name": "ZenFone Max Pro M1 (ZB602KL) (WW) / Max Pro M1 (ZB601KL) (IN)"
        },
        ...
        ...
        ...
    ]
}
```

# Technical notes
- Auth tokens are cached by the SDK for performance.
- Package responses are cached for a 1h period.
- The SDK raises exceptions on non‑2xx responses.
- Validate each item when using bulk or parallel calls.

<!-- Header -->
![alt Header of the EnergyZero package](https://raw.githubusercontent.com/klaasnicolaas/python-energyzero/main/assets/header_energyzero-min.png)

<!-- PROJECT SHIELDS -->
[![GitHub Release][releases-shield]][releases]
[![Python Versions][python-versions-shield]][pypi]
![Project Stage][project-stage-shield]
![Project Maintenance][maintenance-shield]
[![License][license-shield]](LICENSE)

[![GitHub Activity][commits-shield]][commits-url]
[![PyPi Downloads][downloads-shield]][downloads-url]
[![GitHub Last Commit][last-commit-shield]][commits-url]
[![Open in Dev Containers][devcontainer-shield]][devcontainer]

[![Build Status][build-shield]][build-url]
[![Typing Status][typing-shield]][typing-url]
[![Code Coverage][codecov-shield]][codecov-url]
[![OpenSSF Scorecard][scorecard-shield]][scorecard-url]

Asynchronous Python client for the EnergyZero API.

## About

A python package with which you can retrieve the dynamic energy/gas prices from [EnergyZero][energyzero] and can therefore also be used for third parties who purchase their energy via EnergyZero, such as:

- [ANWB Energie](https://www.anwb.nl/huis/energie/anwb-energie)
- [Energie van Ons](https://www.energie.vanons.org)
- [GroeneStroomLokaal](https://www.groenestroomlokaal.nl)
- [Mijndomein Energie](https://www.mijndomein.nl/energie)
- [SamSam](https://www.samsam.nu)
- [ZonderGas](https://www.zondergas.nu)

## Installation

```bash
pip install energyzero
```

## Example

```python
import asyncio
from datetime import UTC, datetime, timedelta

from energyzero import EnergyZero, Interval, PriceType


async def main() -> None:
    """Fetch today/tomorrow energy prices using the REST backend (default)."""
    async with EnergyZero() as client:
        today = datetime.now(UTC).astimezone().date()
        tomorrow = today + timedelta(days=1)

        electricity_today = await client.get_electricity_prices(
            start_date=today,
            interval=Interval.QUARTER,
            price_type=PriceType.ALL_IN,
        )
        gas_today = await client.get_gas_prices(
            start_date=today,
            price_type=PriceType.ALL_IN,
        )

        # Loop over additional days as needed
        electricity_tomorrow = await client.get_electricity_prices(
            start_date=tomorrow,
            interval=Interval.HOUR,
            price_type=PriceType.MARKET_WITH_VAT,
        )
        gas_tomorrow = await client.get_gas_prices(
            start_date=tomorrow,
            price_type=PriceType.MARKET,
        )

        print(electricity_today.average_price, gas_today.current_price)
        print(electricity_tomorrow.average_price, gas_tomorrow.current_price)


if __name__ == "__main__":
    asyncio.run(main())
```

More examples can be found in the [examples folder](./examples/).
* `examples/graphql/*` targets the GraphQL backend (multi-day ranges).
* `examples/rest/*` shows REST API usage (single-day requests, quarter-hour data).

## Data
> [!NOTE]
> Currently tested primarily with day-ahead pricing (today/tomorrow).

You can retrieve both electricity and gas pricing data using this package. With v5.0 we support two official backends:

**REST (default)**
- `APIBackend.REST` — Public REST API.
- Electricity: hourly + quarter-hour. Gas: daily.
- Single date per call; `end_date` must equal `start_date` if provided.

**GraphQL (optional)**
- `APIBackend.GRAPHQL` — GraphQL endpoint with multi-day ranges and extended metadata (`TimeRange`, averages).
- `end_date` is required; electricity is always hourly (`interval` is ignored).

## ⚡ Electricity Prices

Electricity prices change **every hour**. Prices for the next day are typically published between **14:00–15:00**.

### Common fields (`EnergyPrices`)

- `current_price` — Current electricity price for the active hour/time range
- `average_price` — Average price over the selected period
- `extreme_prices` — Tuple `(min_price, max_price)`
- `pct_of_max_price` — Current price expressed as % of the maximum
- `price_at_time(moment)` — Look up the price for a specific UTC timestamp
- `timestamp_prices` — List of `{"timerange": TimeRange, "price": float}` entries
- `highest_price_time_range` / `lowest_price_time_range` — TimeRange with highest/lowest price
- `time_ranges_priced_equal_or_lower` — Number of ranges priced ≤ current price

## 🔥 Gas Prices

Gas prices are **fixed for 24 hours**, and a new daily rate applies starting at **06:00** each morning.

### Common fields (`EnergyPrices`)

- `current_price` — Current gas price for today
- `average_price` — Average price over the requested period
- `extreme_prices` — Tuple `(min_price, max_price)`
- `price_at_time(moment)` — Price lookup for a UTC timestamp
- `timestamp_prices` — `{"timerange": TimeRange, "price": float}` entries
- `highest_price_time_range` / `lowest_price_time_range` — TimeRange with highest/lowest price
- `pct_of_max_price`, `time_ranges_priced_equal_or_lower` — Not applicable for gas prices

## Client Methods (REST + GraphQL)

### `get_electricity_prices()`

| Parameter    | Type        | Description                                    |
|--------------|-------------|------------------------------------------------|
| `start_date` | `date`      | Start of the period (local timezone).          |
| `end_date`   | `date`      | End of the period (local timezone).            |
| `interval`   | `Interval`  | REST only: `Interval.QUARTER` or `Interval.HOUR`. Ignored by GraphQL. |
| `price_type` | `PriceType` | Type of price to return. See `PriceType` for options (default `ALL_IN`). |

---

### `get_gas_prices()`

| Parameter    | Type        | Description                                    |
|--------------|-------------|------------------------------------------------|
| `start_date` | `date`      | Start of the period (local timezone).          |
| `end_date`   | `date`      | End of the period (local timezone).            |
| `price_type` | `PriceType` | Type of price to return. See `PriceType` for options (default `ALL_IN`). |

---

### `PriceType`

Specifies the type of prices returned by both backends.

| Value                | Description                                                                                                    |
|----------------------|----------------------------------------------------------------------------------------------------------------|
| `MARKET`             | Wholesale market price excluding VAT and without additional surcharges (REST `base`, GraphQL `energyPriceExcl`) |
| `MARKET_WITH_VAT`    | Market price including VAT but still without surcharges (REST `base_with_vat`, GraphQL `energyPriceIncl`)       |
| `ALL_IN_EXCL_VAT`    | Market price plus surcharges excluding VAT (REST `all_in`, GraphQL `energyPriceExcl` + `additionalCosts.priceExcl`) |
| `ALL_IN`             | Final consumer rate including VAT and surcharges (REST `all_in_with_vat`, GraphQL `energyPriceIncl` + `additionalCosts.priceIncl`). |

Used in: `get_electricity_prices`, `get_gas_prices`

---

### `Interval`

Specifies the interval for REST API requests:

| Value | Description |
|-------|-------------|
| `Interval.QUARTER` | 15-minute electricity prices |
| `Interval.HOUR`    | Hourly electricity prices    |
| `Interval.DAY`     | Daily gas prices             |

## Contributing

This is an active open-source project. We are always open to people who want to
use the code or contribute to it.

We've set up a separate document for our
[contribution guidelines](CONTRIBUTING.md).

Thank you for being involved! :heart_eyes:

## Setting up development environment

The simplest way to begin is by utilizing the [Dev Container][devcontainer]
feature of Visual Studio Code or by opening a CodeSpace directly on GitHub.
By clicking the button below you immediately start a Dev Container in Visual Studio Code.

[![Open in Dev Containers][devcontainer-shield]][devcontainer]

This Python project relies on [Poetry][poetry] as its dependency manager,
providing comprehensive management and control over project dependencies.

You need at least:

- Python 3.12+
- [Poetry][poetry-install]

### Installation

Install all packages, including all development requirements:

```bash
poetry install
```

_Poetry creates by default an virtual environment where it installs all
necessary pip packages_.

### Prek

This repository uses the [prek][prek] framework, all changes
are linted and tested with each commit. To setup the prek check, run:

```bash
poetry run prek install
```

And to run all checks and tests manually, use the following command:

```bash
poetry run prek run --all-files
```

### Testing

It uses [pytest](https://docs.pytest.org/en/stable/) as the test framework. To run the tests:

```bash
poetry run pytest
```

To update the [syrupy](https://github.com/tophat/syrupy) snapshot tests:

```bash
poetry run pytest --snapshot-update
```

## Migration

Upgrading from v4.x? See [MIGRATION_V5.md](./MIGRATION_V5.md) for a summary of breaking changes and examples for REST and GraphQL.

## License

MIT License

Copyright (c) 2022-2025 Klaas Schoute

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.

[energyzero]: https://www.energyzero.nl

<!-- MARKDOWN LINKS & IMAGES -->
[build-shield]: https://github.com/klaasnicolaas/python-energyzero/actions/workflows/tests.yaml/badge.svg
[build-url]: https://github.com/klaasnicolaas/python-energyzero/actions/workflows/tests.yaml
[commits-shield]: https://img.shields.io/github/commit-activity/y/klaasnicolaas/python-energyzero.svg
[commits-url]: https://github.com/klaasnicolaas/python-energyzero/commits/main
[codecov-shield]: https://codecov.io/gh/klaasnicolaas/python-energyzero/branch/main/graph/badge.svg?token=29Y5JL4356
[codecov-url]: https://codecov.io/gh/klaasnicolaas/python-energyzero
[devcontainer-shield]: https://img.shields.io/static/v1?label=Dev%20Containers&message=Open&color=blue&logo=visualstudiocode
[devcontainer]: https://vscode.dev/redirect?url=vscode://ms-vscode-remote.remote-containers/cloneInVolume?url=https://github.com/klaasnicolaas/python-energyzero
[downloads-shield]: https://img.shields.io/pypi/dm/energyzero
[downloads-url]: https://pypistats.org/packages/energyzero
[license-shield]: https://img.shields.io/github/license/klaasnicolaas/python-energyzero.svg
[last-commit-shield]: https://img.shields.io/github/last-commit/klaasnicolaas/python-energyzero.svg
[maintenance-shield]: https://img.shields.io/maintenance/yes/2025.svg
[project-stage-shield]: https://img.shields.io/badge/project%20stage-production%20ready-brightgreen.svg
[pypi]: https://pypi.org/project/energyzero/
[python-versions-shield]: https://img.shields.io/pypi/pyversions/energyzero
[typing-shield]: https://github.com/klaasnicolaas/python-energyzero/actions/workflows/typing.yaml/badge.svg
[typing-url]: https://github.com/klaasnicolaas/python-energyzero/actions/workflows/typing.yaml
[releases-shield]: https://img.shields.io/github/release/klaasnicolaas/python-energyzero.svg
[releases]: https://github.com/klaasnicolaas/python-energyzero/releases
[scorecard-shield]: https://api.scorecard.dev/projects/github.com/klaasnicolaas/python-energyzero/badge
[scorecard-url]: https://scorecard.dev/viewer/?uri=github.com/klaasnicolaas/python-energyzero

[poetry-install]: https://python-poetry.org/docs/#installation
[poetry]: https://python-poetry.org
[prek]: https://github.com/j178/prek

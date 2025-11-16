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

from datetime import date
from energyzero import EnergyZero


async def main() -> None:
    """Show example on fetching the energy prices from EnergyZero."""
    async with EnergyZero() as client:
        start_date = date(2022, 12, 7)
        end_date = date(2022, 12, 7)

        energy = await client.get_electricity_prices(start_date, end_date)
        gas = await client.get_gas_prices(start_date, end_date)


if __name__ == "__main__":
    asyncio.run(main())
```

More examples can be found in the [examples folder](./examples/).

## Data

> **Note:** Currently tested primarily with day-ahead pricing (today/tomorrow).

You can retrieve both electricity and gas pricing data using this package. Each data type supports a set of common fields, with some additional properties depending on whether you use the **GraphQL** or **legacy REST** endpoint.

## ⚡ Electricity Prices

Electricity prices change **every hour**. Prices for the next day are typically published between **14:00–15:00**.

### Common fields (`Electricity` and `EnergyPrices`)

- `current_price` — Current electricity price for the current hour or time range
- `average_price` — Average price over the selected period
- `extreme_prices` — Tuple of `(min_price, max_price)`
- `pct_of_max_price` — Current price as a percentage of the maximum
- `price_at_time(moment)` — Get price for a specific `datetime`
- `timestamp_prices` — List of hourly price entries:
  - REST: `{"timestamp": datetime, "price": float}`
  - GraphQL: `{"timerange": TimeRange, "price": float}`

### GraphQL-only (`get_electricity_prices()`)

- `highest_price_time_range` — `TimeRange` where the price is highest
- `lowest_price_time_range` — `TimeRange` where the price is lowest
- `time_ranges_priced_equal_or_lower` — Count of hours where the price is less than or equal to the current

### REST-only (`get_electricity_prices_legacy()`)

- `highest_price_time` — Timestamp of the highest hourly price
- `lowest_price_time` — Timestamp of the lowest hourly price
- `hours_priced_equal_or_lower` — Count of hours with a price ≤ current price

## 🔥 Gas Prices

Gas prices are **fixed for 24 hours**, and a new daily rate applies starting at **06:00** each morning.

### Common fields (`Gas` and `EnergyPrices`)

- `current_price` — Current gas price for today
- `average_price` — Average gas price over the selected period
- `extreme_prices` — Tuple of `(min_price, max_price)`
- `price_at_time(moment)` — Get price for a specific `datetime`
- `timestamp_prices` — List of daily price entries:
  - REST: `{"timestamp": datetime, "price": float}`
  - GraphQL: `{"timerange": TimeRange, "price": float}`

### GraphQL-only (`get_gas_prices()`)

- `highest_price_time_range` — Time range with the highest daily price
- `lowest_price_time_range` — Time range with the lowest daily price
- `pct_of_max_price` — Current price as a percentage of the maximum
- `time_ranges_priced_equal_or_lower` — Count of days with a price ≤ current price

## Modern GraphQL Methods

### `get_electricity_prices()`

| Parameter    | Type        | Description                                    |
|--------------|-------------|------------------------------------------------|
| `start_date` | `date`      | Start of the period (local timezone).          |
| `end_date`   | `date`      | End of the period (local timezone).            |
| `price_type` | `PriceType` | Type of price to return: `ALL_IN` or `MARKET`. |

---

### `get_gas_prices()`

| Parameter    | Type        | Description                                    |
|--------------|-------------|------------------------------------------------|
| `start_date` | `date`      | Start of the period (local timezone).          |
| `end_date`   | `date`      | End of the period (local timezone).            |
| `price_type` | `PriceType` | Type of price to return: `ALL_IN` or `MARKET`. |

---

## Legacy REST Methods

### `get_electricity_prices_legacy()`

| Parameter    | Type                | Description                                          |
|--------------|---------------------|------------------------------------------------------|
| `start_date` | `date`              | Start of the period (local timezone).                |
| `end_date`   | `date`              | End of the period (local timezone).                  |
| `interval`   | `Interval`          | Data interval (see `Interval` enum values).           |
| `vat`        | `VatOption \| None` | VAT inclusion (included by default). |

---

### `get_gas_prices_legacy()`

| Parameter    | Type                | Description                                          |
|--------------|---------------------|------------------------------------------------------|
| `start_date` | `date`              | Start of the period (local timezone).                |
| `end_date`   | `date`              | End of the period (local timezone).                  |
| `interval`   | `Interval`          | Data interval (see `Interval` enum values).           |
| `vat`        | `VatOption \| None` | VAT inclusion (included by default). |

## Enum Options

### `VatOption`

Defines whether prices returned by legacy methods should include VAT.

| Value          | Description                     |
|----------------|---------------------------------|
| `INCLUDE`      | Return prices **including VAT** |
| `EXCLUDE`      | Return prices **excluding VAT** |

Used in: `get_electricity_prices_legacy`, `get_gas_prices_legacy`
> 📝 Ignored in GraphQL methods (`get_electricity_prices`, `get_gas_prices`)

---

### `PriceType`

Specifies the type of prices returned by GraphQL methods.

| Value       | Description                                                          |
|-------------|----------------------------------------------------------------------|
| `MARKET`    | Raw wholesale market price (excludes tax, VAT, and purchasing costs) |
| `ALL_IN`    | Final consumer price (includes energy tax, VAT, and purchase fees)   |

Used in: `get_electricity_prices`, `get_gas_prices`

---

### `Interval`

Specifies the interval for prices returned by the legacy methods.

| Value        | Description    |
|--------------|----------------|
| `DAY = 4`    | Daily prices   |
| `MONTH = 5`  | Monthly prices |
| `YEAR = 6`   | Yearly prices  |
| `WEEK = 9`   | Weekly prices  |

Used in: `get_electricity_prices_legacy`, `get_gas_prices_legacy`

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

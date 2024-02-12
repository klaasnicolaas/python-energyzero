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

[![Code Quality][code-quality-shield]][code-quality]
[![Build Status][build-shield]][build-url]
[![Typing Status][typing-shield]][typing-url]

[![Maintainability][maintainability-shield]][maintainability-url]
[![Code Coverage][codecov-shield]][codecov-url]

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

## Data

**note**: Currently only tested for day/tomorrow prices

You can read the following datasets with this package:

### Electricity prices

The energy prices are different every hour, after 15:00 (more usually already at 14:00) the prices for the next day are published and it is therefore possible to retrieve these data.

- Current/Next[x] hour electricity market price (float)
- Average electricity price (float)
- Lowest energy price (float)
- Highest energy price (float)
- Time of highest price (datetime)
- Time of lowest price (datetime)
- Percentage of the current price compared to the maximum price
- Number of hours with the current price or lower (int)

### Gas prices

The gas prices do not change per hour, but are fixed for 24 hours. Which means that from 06:00 in the morning the new rate for that day will be used.

- Current/Next[x] hour gas market price (float)
- Average gas price (float)
- Lowest gas price (float)
- Highest gas price (float)

## Example

```python
import asyncio

from datetime import date
from energyzero import EnergyZero, VatOption


async def main() -> None:
    """Show example on fetching the energy prices from EnergyZero."""
    async with EnergyZero(vat=VatOption.INCLUDE) as client:
        start_date = date(2022, 12, 7)
        end_date = date(2022, 12, 7)

        energy = await client.energy_prices(start_date, end_date)
        gas = await client.gas_prices(start_date, end_date)


if __name__ == "__main__":
    asyncio.run(main())
```

### Class Parameters

| Parameter | value Type | Description |
| :-------- | :--------- | :---------- |
| `vat` | enum (default: **VatOption.INCLUDE**) | Include or exclude VAT on class level |

### Function Parameters

| Parameter | value Type | Description |
| :-------- | :--------- | :---------- |
| `start_date` | datetime | The start date of the selected period |
| `end_date` | datetime | The end date of the selected period |
| `interval` | integer (default: **4**) | The interval of data return (**day**, **week**, **month**, **year**) |
| `vat` | enum (default: class value) | Include or exclude VAT (**VatOption.INCLUDE** or **VatOption.EXCLUDE**) |

**Interval**
4: Dag
5: Maand
6: Jaar
9: Week

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

- Python 3.11+
- [Poetry][poetry-install]

Install all packages, including all development requirements:

```bash
poetry install
```

Poetry creates by default an virtual environment where it installs all
necessary pip packages, to enter or exit the venv run the following commands:

```bash
poetry shell
exit
```

Setup the pre-commit check, you must run this inside the virtual environment:

```bash
pre-commit install
```

*Now you're all set to get started!*

As this repository uses the [pre-commit][pre-commit] framework, all changes
are linted and tested with each commit. You can run all checks and tests
manually, using the following command:

```bash
poetry run pre-commit run --all-files
```

To run just the Python tests:

```bash
poetry run pytest
```

To update the [syrupy](https://github.com/tophat/syrupy) snapshot tests:

```bash
poetry run pytest --snapshot-update
```

## License

MIT License

Copyright (c) 2022-2024 Klaas Schoute

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
[code-quality-shield]: https://github.com/klaasnicolaas/python-energyzero/actions/workflows/codeql.yaml/badge.svg
[code-quality]: https://github.com/klaasnicolaas/python-energyzero/actions/workflows/codeql.yaml
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
[maintenance-shield]: https://img.shields.io/maintenance/yes/2024.svg
[maintainability-shield]: https://api.codeclimate.com/v1/badges/615e7a78f1a6191d4731/maintainability
[maintainability-url]: https://codeclimate.com/github/klaasnicolaas/python-energyzero/maintainability
[project-stage-shield]: https://img.shields.io/badge/project%20stage-production%20ready-brightgreen.svg
[pypi]: https://pypi.org/project/energyzero/
[python-versions-shield]: https://img.shields.io/pypi/pyversions/energyzero
[typing-shield]: https://github.com/klaasnicolaas/python-energyzero/actions/workflows/typing.yaml/badge.svg
[typing-url]: https://github.com/klaasnicolaas/python-energyzero/actions/workflows/typing.yaml
[releases-shield]: https://img.shields.io/github/release/klaasnicolaas/python-energyzero.svg
[releases]: https://github.com/klaasnicolaas/python-energyzero/releases

[poetry-install]: https://python-poetry.org/docs/#installation
[poetry]: https://python-poetry.org
[pre-commit]: https://pre-commit.com

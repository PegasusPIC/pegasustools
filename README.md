# PegasusTools

[![Actions Status][actions-badge]][actions-link]
[![pre-commit.ci status][pre-commit-badge]][pre-commit-link]
[![Documentation Status][rtd-badge]][rtd-link]

[![PyPI version][pypi-version]][pypi-link]
[![PyPI platforms][pypi-platforms]][pypi-link]
[![Code style: Ruff][ruff-badge]][ruff-link]

<!-- [![GitHub Discussion][github-discussions-badge]][github-discussions-link] -->

<!-- SPHINX-START -->

<!-- prettier-ignore-start -->
[actions-badge]:            https://github.com/PegasusPIC/pegasustools/workflows/CI/badge.svg
[actions-link]:             https://github.com/PegasusPIC/pegasustools/actions
<!-- [github-discussions-badge]: https://img.shields.io/static/v1?label=Discussions&message=Ask&color=blue&logo=github
[github-discussions-link]:  https://github.com/PegasusPIC/pegasustools/discussions -->
[pypi-link]:                https://pypi.org/project/pegasustools/
[pypi-platforms]:           https://img.shields.io/pypi/pyversions/pegasustools
[pypi-version]:             https://img.shields.io/pypi/v/pegasustools
[rtd-badge]:                https://readthedocs.org/projects/pegasustools/badge/?version=latest
[rtd-link]:                 https://pegasustools.readthedocs.io/en/latest/?badge=latest
[pre-commit-badge]:         https://results.pre-commit.ci/badge/github/PegasusPIC/pegasustools/main.svg
[pre-commit-link]:          https://results.pre-commit.ci/latest/github/PegasusPIC/pegasustools/main
[ruff-badge]:               https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json
[ruff-link]:                https://github.com/astral-sh/ruff

[![Princeton RSE Badge](https://img.shields.io/badge/Princeton_RSE-2025-%23F58025.svg?logo=data:image/svg+xml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIGlkPSJMYXllcl8xIiB2aWV3Qm94PSIwIDAgMzkyLjkgNTAwIj48ZGVmcz48c3R5bGU+LmNscy0xLC5jbHMtM3tzdHJva2Utd2lkdGg6MH0uY2xzLTN7ZmlsbDojZmZmfTwvc3R5bGU+PC9kZWZzPjxwYXRoIGQ9Ik0zODIgMjExYzE3LTgwIDktMTM4IDktMTM4QzI1OCAxMDkgMTk2IDAgMTk2IDBTMTM1IDEwOSAyIDczYzAgMC05IDU4IDkgMTM4aDM3MVoiIGNsYXNzPSJjbHMtMSIvPjxwYXRoIGQ9Ik0xMSAyMTFhNDgxIDQ4MSAwIDAgMCAxODUgMjg5IDU0NSA1NDUgMCAwIDAgMTM0LTE1M2MyOC00OCA0My05NSA1Mi0xMzZIMTFaIiBzdHlsZT0iZmlsbDojZjU4MDI1O3N0cm9rZS13aWR0aDowIi8+PHBhdGggZD0iTTE5NiAyMTggNjMgMzQ3YzEyIDIxIDI2IDQzIDQzIDY0bDkwLTg5IDkxIDg5YzE3LTIxIDMxLTQzIDQzLTY0TDE5NiAyMThaIiBjbGFzcz0iY2xzLTEiLz48cGF0aCBkPSJtMTc2IDg2LTE4IDNjLTkgMi0yMCAzLTMwLTF2ODZjNCAzIDExIDMgMTcgM2wzMC00YzctMSAxNC0xIDIwIDNWOTFjLTUtNi0xMi02LTE5LTVaTTIzNSA4OWwtMTktM2MtNi0xLTEzLTEtMTggNXY4NWM2LTQgMTMtNCAxOS0zbDMxIDRjNSAwIDEzIDAgMTctM1Y4OGMtMTAgNC0yMSAzLTMwIDFaIiBjbGFzcz0iY2xzLTMiLz48cGF0aCBkPSJtMTk2IDE5MSAxMC0xdi02YTM0NyAzNDcgMCAwIDAgNzAgMFY5OGwtOC0xdjc4cy0xIDMtNSA0Yy05IDMtMTUgMi0yMyAxbC0xNy0zYy05LTEtMTktNC0yNSA1di0xaC0zdjFjLTItMy00LTQtNi01LTYtMi0xMyAwLTE5IDBsLTE4IDNjLTcgMS0xMyAyLTIyLTEtNC0xLTUtNC02LTRWOTdsLTggMXY4NmM0IDEgMTcgMyAzMCAzIDIwIDAgMzktMyA0MS0zdjZsOSAxWk0xMDUgMTA5aDh2MTZoLTh6TTEwNSAxNTFoOHYxNWgtOHpNMjg4IDEyNWgtOHYtMTZoOHpNMjg4IDE2NmgtOHYtMTVoOHoiIGNsYXNzPSJjbHMtMyIvPjxwYXRoIGQ9Im0xNTIgMTA0LTMgMS01IDEyLTEgMXYtMWwtMy01LTEtNC0yLTMtMi0xdi0xaDh2MWwtMyAxaDFsMyA5IDMtNyAxLTItMi0xLTEtMWg3djFNMTY3IDExN2gtMTR2LTFoMmwxLTJ2LTlsLTMtMXYtMWgxM3Y0bC0zLTNoLTV2NWgybDItMXYtMWgxdjZoLTFsLTEtM2gtM3Y0bDEgMXYxaDVsMy0zdjRNMTg0IDEwN2gtMWwtMS0yLTItMWgtMnYxMGMwIDIgMSAyIDMgMnYxaC04di0xbDMtMXYtOWwtMS0yaC0ybC0zIDN2LTRoMTR2NE0xNTEgMTMwaC0xbC0xLTItMi0yaC0ydjExbDMgMmgtOGMyIDAgMi0xIDMtMnYtMTFoLTNsLTMgM3YxLTVoMTR2NU0xNjcgMTQwbC03LTFoLTcgMWwyLTF2LTEwYzAtMi0xLTItMi0ydi0xaDEybDEgMXYzaC0xbC0yLTItMS0xaC00djVoMmwxLTEgMS0xaDFsLTEgMyAxIDNoLTFsLTItMi0xLTFoLTF2NmwxIDFoM2wyLTFzMi0xIDItM2gxdjRsLTEgMU0xNzcgMTQwbC0zLTFoLTJ2LTRoMWwxIDIgMyAyIDItMSAxLTJ2LTFsLTItMS0zLTEtMi0yLTEtMmMwLTIgMi00IDQtNGw0IDF2LTFoMXY1aC0xbC0xLTMtMy0xLTIgMiAyIDIgMiAxIDIgMWMyIDEgMiAyIDIgNHMtMiA0LTUgNE0xNTcgMTYyaC0xNHYtMWgybDEtM3YtOGwtMy0yaDEzdjNoLTFsLTItMmgtNXY1aDJsMi0xdi0yaDF2N2wtMS0xLTEtMmgtM3Y1bDEgMWg1bDMtM3Y0TTE3NyAxNDhjLTEgMC0yIDEtMiAzdjExaC0xbC0xMC0xMXY4bDEgMmgydjFoLTd2LTFsMy0xdi05bC0xLTF2LTFsLTItMWg1bDcgOCAyIDJ2LTdsLTEtMi0yLTFoNy0xTTIyNCAxMDRjLTEgMC0yIDAtMiAzdjEwaC0xbC0xMC0xMXY4bDEgMmgydjFoLTd2LTFsMy0xdi04bC0xLTJ2LTFoLTJ2LTFoNWw3IDggMiAydi03bC0xLTJoLTJ2LTFoN3YxTTIzNyAxMDVsLTMtMi0yIDItMiA1IDEgNSAzIDJjMiAwIDMtMSAzLTJsMS01LTEtNW0yIDEwYy0xIDItMyAzLTUgM2wtNS0zLTItNSAyLTVjMi0yIDQtMiA1LTJsNCAxYzIgMSA0IDMgNCA2IDAgMi0xIDQtMyA1TTI2MCAxMDRsLTMgMS01IDEyLTEgMXYtMWwtMy01LTEtNC0yLTMtMi0xdi0xaDh2MWwtMiAxIDMgOSAzLTcgMS0yLTItMS0xLTFoN3YxTTIyMCAxMzBoLTFsLTEtMi0yLTJoLTJ2MTFsMyAyaC04YzIgMCAyLTEgMy0ydi05bC0xLTJoLTJsLTMgM3YxLTVoMTR2NU0yMjggMTI4bC0xIDItMSAzaDRsLTItNW05IDEyaC0xbC0zLTEtMyAxdi0xbDItMS0xLTItMS0yaC00bC0yIDN2MWwyIDFoLTYgMWwyLTEgMS00IDMtNSAxLTJ2LTJoMWwxIDEgMiA2IDIgMyAxIDMgMiAxdjFNMjU5IDE0MGwtNi0xaC0xIDFsMS0ydi0xMGwtMyA2LTEgMy0xIDNoLTFsLTEtMi01LTExdjEwYzAgMiAxIDMgMyAzdjFoLTFsLTMtMWgtM2wyLTEgMS0ydi04bC0xLTJoLTJ2LTFoNmwxIDEgNCA5IDEtMiAzLTYgMS0yaDV2MWwtMiAxdjhsMSA0aDF2MU0yMjAgMTUyaC0xbC0xLTItMy0xaC0xdjEwYzAgMiAxIDIgMyAydjFoLTh2LTFsMi0xdi0xMWgtMmwtMyAzaC0xdi00aDE1djRNMjM3IDE0OGwtMiAyLTYgMTJoLTFsLTItNi0yLTQtMS0yLTItMmg3bC0yIDF2MWw0IDkgMy03di0ybC0yLTJoNk0yNTkgMTYyaC03di0xaDFsMS0ydi0xMGwtMyA3LTEgMi0xIDNoLTFjLTEgMCAwIDAgMCAwbC0xLTItNS0xMHY5YzAgMiAxIDMgMyAzdjFoLTZ2LTFsMi0xdi0xMWwtMi0xaDZsNCAxMCAxLTIgMy03IDEtMWg1bC0yIDF2OWwxIDNoMXYxIiBjbGFzcz0iY2xzLTEiLz48L3N2Zz4=&labelColor=%235A575B)](https://researchcomputing.princeton.edu/services/research-software-engineering)
<!-- prettier-ignore-end -->

## Summary

[PegasusTools](https://github.com/PegasusPIC/pegasustools) is an analysis
package for the Pegasus++ Particle-In-Cell (PIC) code. It can be easily
installed with `pip install pegasustools` or `uv pip install pegasustools`. The
documentation for the latest stable version can be found
[here](https://pegasustools.readthedocs.io/en/stable/). Once installed it can be
imported directly into any Python program via `import pegasustools as pt`

## Found a Bug or Have a Feature Request?

Please open an issue and we'll figure out a solution.

## Contributing

If you wish to contribute please review the contribution guide in
[CONTRIBUTING.md](./.github/CONTRIBUTING.md). All contributions need to come via
pull requests. I recommend you fork this repo, make your changes, then submit a
PR from your feature branch.

## Citation

If `PegasusTools` has been significant to a project that leads to an academic
publication, please acknowledge our work by citing it using the information in
the included citation.cff file; citations in APA or BibTex format can be found
in the "About" section of the GitHub repository.

## Bibliography

- [M. W. Kunz, J. M. Stone, X.-N. Bai, 2014, JCoP, 259, 154 \
  _Pegasus: A new hybrid-kinetic particle-in-cell code for astrophysical plasma dynamics_](https://ui.adsabs.harvard.edu/abs/2014JCoPh.259..154K/abstract)
- Icon made by max.icons from [www.flaticon.com](https://www.flaticon.com)

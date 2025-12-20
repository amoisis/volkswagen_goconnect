# Volkswagen GoConnect Integration for Home Assistant

[![GitHub Release](https://img.shields.io/github/v/release/amoisis/volkswagen_goconnect?style=flat-square)](https://github.com/amoisis/volkswagen_goconnect/releases)
[![Tests & Coverage](https://img.shields.io/github/actions/workflow/status/amoisis/volkswagen_goconnect/tests.yml?style=flat-square&label=tests)](https://github.com/amoisis/volkswagen_goconnect/actions/workflows/tests.yml)
[![codecov](https://img.shields.io/codecov/c/github/amoisis/volkswagen_goconnect?style=flat-square)](https://codecov.io/gh/amoisis/volkswagen_goconnect)
[![Last Commit](https://img.shields.io/github/last-commit/amoisis/volkswagen_goconnect?style=flat-square)](https://github.com/amoisis/volkswagen_goconnect/commits)

## Installation

[![Open your Home Assistant instance and open a repository inside the Home Assistant Community Store.](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=amoisis&repository=volkswagen-goconnect&category=integration)

You can also install manually by copying the `custom_components` from this repository into your Home Assistant installation


### Cars Supported
Any car fitted with the Connected Cars module (GoConnectApp). There are some urls that look like they reference country if it is not working and you do not live in Australia, if you can find the correct urls please put a pull request in and we can integrate additional countries as required.

#### Australia
* ID.4
* ID.5
* ID Buzz

## Want to Help Develop Volkswagen GoConnect Integration?

This repository contains multiple files, here is a overview:

File | Purpose | Documentation
-- | -- | --
`.devcontainer.json` | Used for development/testing with Visual Studio Code. | [Documentation](https://code.visualstudio.com/docs/remote/containers)
`custom_components/volkswagen_goconnect/*` | Integration files, this is where everything happens. | [Documentation](https://developers.home-assistant.io/docs/creating_component_index)
`LICENSE` | The license file for the project. | [Documentation](https://help.github.com/en/github/creating-cloning-and-archiving-repositories/licensing-a-repository)
`README.md` | The file you are reading now, should contain info about the integration, installation and configuration instructions. | [Documentation](https://help.github.com/en/github/writing-on-github/basic-writing-and-formatting-syntax)
`requirements.txt` | Python packages used for development/lint/testing this integration. | [Documentation](https://pip.pypa.io/en/stable/user_guide/#requirements-files)

### How?

1. Create a new repository in GitHub, using this repository as a template by clicking the "Use this template" button in the GitHub UI.
2. Open your new repository in Visual Studio Code devcontainer (Preferably with the "`Dev Containers: Clone Repository in Named Container Volume...`" option).
3. Run the `scripts/develop` to start HA and test out your new integration.

## Testing

This integration includes comprehensive tests using pytest. To run the tests:

```bash
# Run all tests
pytest tests/

# Run tests with coverage
pytest tests/ --cov=custom_components.volkswagen_goconnect

# Run specific test file
pytest tests/test_api.py

# Run tests in verbose mode
pytest tests/ -v
```

### Test Coverage

The test suite includes:

- **test_api.py**: Tests for the API client including login, vehicle data retrieval, and error handling
- **test_sensor.py**: Tests for sensor platform including entity creation, value extraction, and conditional sensors
- **test_binary_sensor.py**: Tests for binary sensor platform including charging and vehicle status sensors
- **test_coordinator.py**: Tests for the data update coordinator
- **test_config_flow.py**: Tests for the configuration flow
- **test_entity.py**: Tests for the base entity class including device info and unique ID generation

### Mock Data

The `conftest.py` file provides fixtures for test data:

- `mock_api_data`: Mock data for a standard petrol vehicle with all available fields
- `mock_api_data_electric`: Mock data for an electric vehicle

## Next steps

These are some next steps you may want to look into:
- Add more integration tests
- Add brand images (logo/icon) to https://github.com/home-assistant/brands.
- Create your first release.
- Share your integration on the [Home Assistant Forum](https://community.home-assistant.io/).
- Submit your integration to [HACS](https://hacs.xyz/docs/publish/start).

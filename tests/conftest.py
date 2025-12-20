"""Fixtures for volkswagen_goconnect tests."""

from unittest.mock import AsyncMock, MagicMock
import sys
from pathlib import Path

import pytest
from homeassistant.core import HomeAssistant

# Add custom_components to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from custom_components.volkswagen_goconnect.api import VolkswagenGoConnectApiClient


@pytest.fixture
def hass() -> HomeAssistant:
    """Return a mock Home Assistant instance."""
    mock_hass = MagicMock(spec=HomeAssistant)
    mock_hass.config_entries = MagicMock()
    mock_hass.config_entries.async_entries = MagicMock(return_value=[])
    mock_hass.data = {}
    return mock_hass


@pytest.fixture
def mock_client():
    """Create a mock API client."""
    return AsyncMock(spec=VolkswagenGoConnectApiClient)


@pytest.fixture
def mock_api_data():
    """Return mock API response data."""
    return {
        "data": {
            "viewer": {
                "vehicles": [
                    {
                        "vehicle": {
                            "id": "test-vehicle-id",
                            "vin": "TEST123VIN",
                            "name": "Test Vehicle",
                            "licensePlate": "ABC123",
                            "make": "Volkswagen",
                            "model": "Golf",
                            "year": 2023,
                            "fuelType": "Petrol",
                            "activated": True,
                            "isBlocked": False,
                            "odometer": {
                                "id": "odometer-1",
                                "odometer": 15000,
                                "time": "2025-12-19T10:30:00Z",
                            },
                            "fuelPercentage": {
                                "id": "fuel-pct-1",
                                "percent": 75,
                                "time": "2025-12-19T10:30:00Z",
                            },
                            "fuelLevel": {
                                "id": "fuel-level-1",
                                "liter": 45,
                                "time": "2025-12-19T10:30:00Z",
                            },
                            "chargePercentage": {
                                "id": "charge-pct-1",
                                "pct": 0,
                                "time": "2025-12-19T10:30:00Z",
                            },
                            "ignition": {
                                "id": "ignition-1",
                                "on": False,
                                "time": "2025-12-19T10:30:00Z",
                            },
                            "rangeTotalKm": {
                                "id": "range-1",
                                "km": 500,
                                "time": "2025-12-19T10:30:00Z",
                            },
                            "isCharging": False,
                            "chargingStatus": {
                                "startChargePercentage": 0,
                                "startTime": None,
                                "endedAt": None,
                                "chargedPercentage": 0,
                                "averageChargeSpeed": 0,
                                "chargeInKwhIncrease": 0,
                                "rangeIncrease": 0,
                                "timeUntil80PercentCharge": None,
                                "showSummaryForChargeEnded": False,
                            },
                            "highVoltageBatteryUsableCapacityKwh": {
                                "id": "battery-capacity-1",
                                "kwh": 0,
                                "time": "2025-12-19T10:30:00Z",
                            },
                            "workshop": {
                                "id": "workshop-1",
                                "number": "WS001",
                                "name": "Test Workshop",
                                "address": "123 Service Lane",
                                "zip": "12345",
                                "city": "Test City",
                                "timeZone": {
                                    "offset": "+10:00",
                                    "__typename": "TimeZone",
                                },
                                "phone": "+1234567890",
                                "emergencyContactPhoneNumber": "+0987654321",
                                "latitude": -37.8136,
                                "longitude": 144.9631,
                                "brand": "Volkswagen",
                                "mobileBookingUrl": "https://example.com/booking",
                                "openingHours": [
                                    {
                                        "day": "monday",
                                        "from": "08:00",
                                        "to": "17:00",
                                        "__typename": "WorkshopOpeningHour",
                                    },
                                    {
                                        "day": "tuesday",
                                        "from": "08:00",
                                        "to": "17:00",
                                        "__typename": "WorkshopOpeningHour",
                                    },
                                ],
                            },
                            "brandContactInfo": {
                                "webshopUrl": "https://vw.example.com",
                                "webshopName": "VW Store",
                                "roadsideAssistancePhoneNumber": "+1800VW",
                                "roadsideAssistanceName": "VW Roadside",
                                "roadsideAssistanceUrl": "https://vw.example.com/roadside",
                                "roadsideEmergencyAssistanceUrl": "https://vw.example.com/emergency",
                                "roadsideAssistancePaid": True,
                            },
                            "primaryFleet": {
                                "id": "fleet-1",
                                "name": "Personal Vehicles",
                            },
                            "service": {
                                "servicePredictions": [
                                    {
                                        "type": "service",
                                        "days": {
                                            "value": 180,
                                            "valid": True,
                                            "predictedDate": "2026-06-19",
                                        },
                                        "km": {
                                            "value": 5000,
                                            "valid": True,
                                            "predictedDate": "2026-06-19",
                                        },
                                    }
                                ]
                            },
                        }
                    }
                ]
            }
        }
    }


@pytest.fixture
def mock_api_data_electric():
    """Return mock API response data for electric vehicle."""
    return {
        "data": {
            "viewer": {
                "vehicles": [
                    {
                        "vehicle": {
                            "id": "test-ev-id",
                            "vin": "TESTEVVIN",
                            "name": "Test EV",
                            "licensePlate": "EV123",
                            "make": "Volkswagen",
                            "model": "ID.4",
                            "year": 2023,
                            "fuelType": "electric",
                            "activated": True,
                            "isBlocked": False,
                            "odometer": {
                                "id": "odometer-1",
                                "odometer": 5000,
                                "time": "2025-12-19T10:30:00Z",
                            },
                            "chargePercentage": {
                                "id": "charge-pct-1",
                                "pct": 85,
                                "time": "2025-12-19T10:30:00Z",
                            },
                            "ignition": {
                                "id": "ignition-1",
                                "on": False,
                                "time": "2025-12-19T10:30:00Z",
                            },
                            "rangeTotalKm": {
                                "id": "range-1",
                                "km": 420,
                                "time": "2025-12-19T10:30:00Z",
                            },
                            "isCharging": False,
                            "chargingStatus": {
                                "startChargePercentage": 0,
                                "startTime": None,
                                "endedAt": None,
                                "chargedPercentage": 0,
                                "averageChargeSpeed": 0,
                                "chargeInKwhIncrease": 0,
                                "rangeIncrease": 0,
                                "timeUntil80PercentCharge": None,
                                "showSummaryForChargeEnded": False,
                            },
                            "highVoltageBatteryUsableCapacityKwh": {
                                "id": "battery-capacity-1",
                                "kwh": 82,
                                "time": "2025-12-19T10:30:00Z",
                            },
                            "workshop": {
                                "id": "workshop-1",
                                "number": "WS002",
                                "name": "Test EV Workshop",
                                "address": "456 EV Service Road",
                                "zip": "54321",
                                "city": "EV City",
                                "timeZone": {
                                    "offset": "+11:00",
                                    "__typename": "TimeZone",
                                },
                                "phone": "+1234567891",
                                "emergencyContactPhoneNumber": "+0987654322",
                                "latitude": -35.24188574,
                                "longitude": 149.0620333,
                                "brand": "volkswagen",
                                "mobileBookingUrl": "https://example.com/ev-booking",
                                "openingHours": [
                                    {
                                        "day": "monday",
                                        "from": "07:30",
                                        "to": "17:00",
                                        "__typename": "WorkshopOpeningHour",
                                    },
                                    {
                                        "day": "tuesday",
                                        "from": "07:30",
                                        "to": "17:00",
                                        "__typename": "WorkshopOpeningHour",
                                    },
                                    {
                                        "day": "wednesday",
                                        "from": "07:30",
                                        "to": "17:00",
                                        "__typename": "WorkshopOpeningHour",
                                    },
                                    {
                                        "day": "thursday",
                                        "from": "07:30",
                                        "to": "17:00",
                                        "__typename": "WorkshopOpeningHour",
                                    },
                                    {
                                        "day": "friday",
                                        "from": "07:30",
                                        "to": "17:00",
                                        "__typename": "WorkshopOpeningHour",
                                    },
                                ],
                            },
                            "brandContactInfo": {
                                "roadsideAssistanceName": "VW Roadside Assist",
                            },
                        }
                    }
                ]
            }
        }
    }

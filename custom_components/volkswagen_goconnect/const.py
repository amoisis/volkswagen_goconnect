"""Constants for volkswagen_goconnect."""

from logging import Logger, getLogger

LOGGER: Logger = getLogger(__package__)

DOMAIN = "volkswagen_goconnect"
CONF_ABRP_ENABLED = "abrp_enabled"
CONF_IGNITION_POLLING_INTERVAL = "ignition_polling_interval"
CONF_POLLING_INTERVAL = "polling_interval"
SIGNAL_ABRP_ACKNOWLEDGE = "volkswagen_goconnect_abrp_acknowledge_{entry_id}"
ATTRIBUTION = "Data provided by Volkswagen GoConnect"
ABRP_HTTP_OK = 200
ABRP_URL = "https://api.iternio.com/1/tlm/send"
ABRP_COUNTER_CACHE_MAX_ENTRIES = 32
ABRP_COUNTER_CACHE_TTL_SECONDS = 86400
BASE_URL_AUTH = "https://auth-api.au1.connectedcars.io"
BASE_URL_AUTH_LOGIN = BASE_URL_AUTH + "/auth/login"
BASE_URL_API = "https://api.au1.connectedcars.io/graphql"
AUTH_URL = BASE_URL_AUTH_LOGIN + "/email/password"
AUTH_TOKEN_URL = BASE_URL_AUTH_LOGIN + "/deviceToken"
REGISTER_DEVICE_URL = BASE_URL_AUTH + "/user/registerDevice"
HTTP_DEBUG_ENV_VALUES = {"1", "true", "yes", "on"}
MIN_REQUEST_INTERVAL_SECONDS = 0.2
POWER_MAX_INTERVAL_SECONDS = 180
POWER_MAX_STREAM_DRIFT_SECONDS = 10
REQUEST_TIMEOUT_SECONDS = 10
SERIES_MIN_POINTS = 2
SENSITIVE_KEYS = {
    "access_token",
    "authorization",
    "client_secret",
    "cookie",
    "deviceToken",
    "id_token",
    "password",
    "refresh_token",
    "secret",
    "set-cookie",
    "token",
}
SENSOR_ERROR_CODE_MAX_ROWS = 5
SENSOR_ERROR_CODE_MAX_TEXT_LENGTH = 120
THROTTLE_BASE_DELAY_SECONDS = 1.0
THROTTLE_MAX_RETRIES = 3
QUERY_ALL_VEHICLES_DATA = """query AllVehiclesData {
  viewer {
    vehicles {
      vehicle {
        id
        vin
        activated
        bookingUrl
        mobileBookingUrl
        isBlocked
        name
        serviceLastAtMileage
        serviceLastAtDate
        oilChangeLastAtDate
        primaryUser {
          ...UserName
          __typename
        }
        position {
          id
          latitude
          longitude
          __typename
        }
        fuelPercentage {
          ...FuelPercentage
          __typename
        }
        fuelType
        fuelLevel {
          ...FuelLevel
          __typename
        }
        chargePercentage {
          ...ChargePercentage
          __typename
        }
        odometer {
          ...Odometer
          __typename
        }
        updateTime
        driverScore {
          driverScore
          previousDriverScore
          __typename
        }
        service {
          ...VehicleServiceData
          __typename
        }
        ignition {
          on
          __typename
        }
        snoozes {
          fleetId
          start
          end
          active
          __typename
        }
        licensePlate
        openLeads: leads(statuses: [open]) {
          id
          status
          dismissed
          important
          severityScore
          type
          context {
            ...LeadEngineLampContext
            ...LeadErrorCodeContext
            __typename
          }
          __typename
        }
        allLeads: leads(statuses: [open, closed]) {
          id
          status
          dismissed
          important
          severityScore
          type
          context {
            ...LeadEngineLampContext
            ...LeadErrorCodeContext
            __typename
          }
          __typename
        }
        serviceLeads: leads(types: [service_reminder]) {
          id
          __typename
        }
        primaryFleet {
          id
          name
          __typename
        }
        model
        brand
        year
        make
        workshop {
          ...MobileWorkshop
          __typename
        }
        brandContactInfo {
          ...NamespaceBrandContactInfo
          __typename
        }
        splitUserControl
        rangeTotalKm {
          id
          km
          time
          __typename
        }
        speedometers(limit: 1, order: DESC) {
          ...Speedometer
          __typename
        }
        outdoorTemperatures(limit: 1, order: DESC) {
          ...OutdoorTemperature
          __typename
        }
        refuelEvents(limit: 1, order: DESC) {
          id
          time
          __typename
        }
        isCharging
        chargingStatus {
          ...ChargingStatus
          __typename
        }
        highVoltageBatteryUsableCapacityKwh {
          ...HighVoltageBatteryUsableCapacityKwh
          __typename
        }
        carBatteryCharge {
          id
          kwh
          time
          __typename
        }
        carBatteryDischarge {
          id
          kwh
          time
          __typename
        }
        carBatteryCharges(limit: 2, order: DESC) {
          id
          kwh
          time
          __typename
        }
        carBatteryDischarges(limit: 2, order: DESC) {
          id
          kwh
          time
          __typename
        }
        highVoltageBatteryTemperature {
          id
          celsius
          time
          __typename
        }
        batteryEfficiencyKmPerKwh
        averageBatteryConsumptionInKwhPer100Km {
          efficiencyKwhPer100Km
          date
          __typename
        }
        chargeEvents(limit: 1, order: DESC) {
          id
          endTime
          __typename
        }
        latestBatteryVoltage {
          ...BatteryVoltage
          __typename
        }
        __typename
      }
      __typename
    }
  }
}

fragment UserName on User {
  id
  firstname
  lastname
  __typename
}

fragment FuelPercentage on VehicleFuelPercentage {
  id
  percent
  time
  __typename
}

fragment FuelLevel on VehicleFuelLevel {
  id
  liter
  time
  __typename
}

fragment ChargePercentage on VehicleChargePercentage {
  id
  pct
  time
  __typename
}

fragment Odometer on VehicleOdometer {
  id
  odometer
  time
  __typename
}

fragment Speedometer on VehicleSpeed {
  id
  speed
  time
  __typename
}

fragment OutdoorTemperature on VehicleOutdoorTemperature {
  celsius
  time
  __typename
}

fragment VehicleServiceData on VehicleServiceData {
  predictedDate
  oilEstimateUncertain
  oilInterval
  oilIntervalTime
  serviceBookedTime
  servicePredictions {
    ...VehicleServiceDataPrediction
    __typename
  }
  __typename
}

fragment VehicleServiceDataPrediction on VehicleServicePrediction {
  type
  days {
    value
    valid
    predictedDate
    available
    outdated
    time
    __typename
  }
  km {
    value
    valid
    predictedDate
    available
    outdated
    time
    __typename
  }
  __typename
}

fragment MobileWorkshop on Workshop {
  id
  number
  name
  address
  zip
  city
  timeZone {
    offset
    __typename
  }
  phone
  latitude
  longitude
  brand
  mobileBookingUrl
  openingHours {
    day
    from
    to
    __typename
  }
  __typename
}

fragment NamespaceBrandContactInfo on OrganizationNamespaceBrandContactInfo {
  roadsideAssistancePhoneNumber
  roadsideAssistanceName
  roadsideAssistanceUrl
  roadsideAssistancePaid
  __typename
}

fragment LeadEngineLampContext on LeadEngineLampContext {
  lamps {
    color
    frequency
    subtitle
    __typename
  }
  lampCount
  __typename
}

fragment LeadErrorCodeContext on LeadErrorCodeContext {
  errorCode
  provider
  ecu
  description
  rawCode
  severity
  firstErrorCodeTime
  lastErrorCodeTime
  errorCodeCount
  __typename
}

fragment ChargingStatus on VehicleChargeStatus {
  startChargePercentage
  startTime
  endedAt
  chargedPercentage
  averageChargeSpeed
  chargeInKwhIncrease
  rangeIncrease
  timeUntil80PercentCharge
  showSummaryForChargeEnded
  __typename
}

fragment HighVoltageBatteryUsableCapacityKwh on VehicleCanHighVoltageBatteryUsableCapacityKwh {
  id
  kwh
  time
  __typename
}

fragment BatteryVoltage on VehicleBatteryVoltage {
  voltage
  time
  __typename
}"""
QUERY_IGNITION_DATA = """query IgnitionData {
  viewer {
    vehicles {
      vehicle {
        id
        ignition {
          on
          __typename
        }
        chargePercentage {
          id
          pct
          time
          __typename
        }
        isCharging
        __typename
      }
      __typename
    }
  }
}"""
QUERY_ABRP_DATA = """query AbrpData {
  viewer {
    vehicles {
      vehicle {
        id
        licensePlate
        ignition {
          on
          __typename
        }
        chargePercentage {
          id
          pct
          time
          __typename
        }
        isCharging
        position {
          id
          latitude
          longitude
          __typename
        }
        odometer {
          id
          odometer
          time
          __typename
        }
        rangeTotalKm {
          id
          km
          time
          __typename
        }
        speedometers(limit: 1, order: DESC) {
          id
          speed
          time
          __typename
        }
        outdoorTemperatures(limit: 1, order: DESC) {
          celsius
          time
          __typename
        }
        highVoltageBatteryUsableCapacityKwh {
          id
          kwh
          time
          __typename
        }
        carBatteryCharge {
          id
          kwh
          time
          __typename
        }
        carBatteryDischarge {
          id
          kwh
          time
          __typename
        }
        highVoltageBatteryTemperature {
          id
          celsius
          time
          __typename
        }
        __typename
      }
      __typename
    }
  }
}"""
HTTP_HEADERS_USER_AGENT = "okhttp/4.12.0"
HTTP_HEADERS_ORGANIZATION_NAMESPACE = "vwaustralia:app"
HTTP_HEADERS_APP_VERSION = "1.79.12"

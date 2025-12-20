"""Constants for volkswagen_goconnect."""

from logging import Logger, getLogger

LOGGER: Logger = getLogger(__package__)

DOMAIN = "volkswagen_goconnect"
ATTRIBUTION = "Data provided by Volkswagen GoConnect"
BASE_URL_AUTH = "https://auth-api.au1.connectedcars.io"
BASE_URL_AUTH_LOGIN = BASE_URL_AUTH + "/auth/login"
BASE_URL_API = "https://api.au1.connectedcars.io/graphql"
AUTH_URL = BASE_URL_AUTH_LOGIN + "/email/password"
AUTH_TOKEN_URL = BASE_URL_AUTH_LOGIN + "/deviceToken"
REGISTER_DEVICE_URL = BASE_URL_AUTH + "/user/registerDevice"
CONF_POLLING_INTERVAL = "polling_interval"
QUERY_API_VEHICLETYPE = (
    "query VehiclesType { viewer { id vehicles { vehicle { ...VehicleType "
    "__typename } __typename } __typename }} fragment VehicleType on Vehicle { "
    "id fuelType primaryUser { id __typename } primaryFleet { id isLightFleet "
    "workHours { day __typename } name featureFlags __typename }  __typename}"
)
QUERY_VEHICLE_DETAILS = """query Vehicle($id: ID!) {
  vehicle(id: $id) {
    ...Vehicle
    __typename
  }
}

fragment Vehicle on Vehicle {
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
  productFeatures
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
  class
  updateTime
  absoluteImageUrl
  service {
    ...VehicleServiceData
    __typename
  }
  ignition {
    ...Ignition
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
  leads(types: [service_reminder]) {
    id
    __typename
  }
  insurance {
    ...Insurance
    __typename
  }
  leasing {
    ...Leasing
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
  hasFleet
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
  __typename
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

fragment Ignition on VehicleIgnition {
  id
  on
  time
  __typename
}

fragment Insurance on VehicleInsurance {
  key
  name
  url
  reportClaimUrl
  logo
  phone
  phones {
    make
    phoneNumber
    __typename
  }
  __typename
}

fragment Leasing on VehicleLeasing {
  key
  name
  url
  address
  logo
  phone
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
  emergencyContactPhoneNumber
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
  webshopUrl
  webshopName
  roadsideAssistancePhoneNumber
  roadsideAssistanceName
  roadsideAssistanceUrl
  roadsideEmergencyAssistanceUrl
  roadsideAssistancePaid
  __typename
}"""
QUERY_VEHICLE_SYSTEM_OVERVIEW = """query VehicleSystemOverview($id: ID!, $statuses: [LeadStatus!] = [open]) {
  vehicle(id: $id) {
    id
    productFeatures
    licensePlate
    leads(statuses: $statuses) {
      id
      status
      dismissed
      type
      context {
        ...LeadEngineLampContext
        __typename
      }
      __typename
    }
    rangeTotalKm {
      id
      km
      time
      __typename
    }
    odometer {
      ...Odometer
      __typename
    }
    ignition {
      ...Ignition
      __typename
    }
    fuelLevel {
      ...FuelLevel
      __typename
    }
    fuelPercentage {
      ...FuelPercentage
      __typename
    }
    refuelEvents(limit: 1, order: DESC) {
      id
      time
      __typename
    }
    fuelType
    isCharging
    chargingStatus {
      ...ChargingStatus
      __typename
    }
    highVoltageBatteryUsableCapacityKwh {
      ...HighVoltageBatteryUsableCapacityKwh
      __typename
    }
    chargePercentage {
      ...ChargePercentage
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
    recentBatteryVoltages {
      ...BatteryVoltage
      __typename
    }
    service {
      ...VehicleSystemOverviewServiceData
      __typename
    }
    insurance {
      ...Insurance
      __typename
    }
    leasing {
      ...Leasing
      __typename
    }
    primaryFleet {
      ...FleetName
      __typename
    }
    __typename
  }
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

fragment Odometer on VehicleOdometer {
  id
  odometer
  time
  __typename
}

fragment Ignition on VehicleIgnition {
  id
  on
  time
  __typename
}

fragment FuelLevel on VehicleFuelLevel {
  id
  liter
  time
  __typename
}

fragment FuelPercentage on VehicleFuelPercentage {
  id
  percent
  time
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

fragment ChargePercentage on VehicleChargePercentage {
  id
  pct
  time
  __typename
}

fragment BatteryVoltage on VehicleBatteryVoltage {
  voltage
  time
  __typename
}

fragment VehicleSystemOverviewServiceData on VehicleServiceData {
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

fragment Insurance on VehicleInsurance {
  key
  name
  url
  reportClaimUrl
  logo
  phone
  phones {
    make
    phoneNumber
    __typename
  }
  __typename
}

fragment Leasing on VehicleLeasing {
  key
  name
  url
  address
  logo
  phone
  __typename
}

fragment FleetName on Fleet {
  id
  name
  __typename
}"""
HTTP_HEADERS_USER_AGENT = "okhttp/4.12.0"
HTTP_HEADERS_ORGANIZATION_NAMESPACE = "vwaustralia:app"
HTTP_HEADERS_APP_VERSION = "1.79.12"

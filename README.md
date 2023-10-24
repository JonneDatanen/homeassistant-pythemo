# `homeassistant-pythemo` - Themo Integration for Home Assistant

`homeassistant-pythemo` is an integration for Home Assistant that leverages the `pythemo` library, providing direct control and monitoring of your Themo devices.

## Installation

To install `homeassistant-pythemo`, use HACS (Home Assistant Community Store):

1. Open HACS in your Home Assistant instance.
2. Navigate to the "Integrations" tab.
3. Click on the `+` button to add a new integration.
4. Search for "homeassistant-pythemo" and install it.

## Configuration

To set up the Themo integration, add the following configuration to your `configuration.yaml` file:

```yaml
themo:
  username: your_email@example.com
  password: your_password
```

Replace `your_email@example.com` and `your_password` with your Themo account credentials.

## Features

1. **Climate Object**: Adjust and monitor the temperature settings of your Themo thermostat.
2. **Light Object**: Control the light on your Themo device.

3. **Sensor Object**: Measure power with the Themo device. Due to discrepancies in the data provided by the cloud, the power measurements might not always be accurate.

## Usage

After adding the configuration and restarting Home Assistant, the Themo devices linked to your account will automatically be integrated into your Home Assistant dashboard. From there, you can:

- Monitor and adjust temperature settings using the Climate object.
- Control the Themo device light with the Light object.
- View power measurements via the Sensor object, but be cautious of the potential data inaccuracies from the cloud.

## Known Issues

- The Sensor object's power measurements might exhibit inaccuracies due to issues with the data from the cloud.

## Contributions

For issues, contributions, or feature requests related to this integration, please refer to the GitHub repository. For cloud connection implementation details, check out the `pythemo` package.

## License

This project is licensed under the MIT License. See the `LICENSE` file in the GitHub repository for more details.

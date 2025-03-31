# `homeassistant-pythemo` - Themo Integration for Home Assistant

`homeassistant-pythemo` is an integration for Home Assistant that provides control and monitoring of your Themo devices via Home Assistant.

## Installation

To install `homeassistant-pythemo`, use HACS (Home Assistant Community Store):

1. Open HACS in your Home Assistant instance.
2. Navigate to the "Integrations" tab.
3. Click on the three dots in the top right corner and select "Custom repositories".
4. In the "Repository" field, enter `https://github.com/JonneDatanen/homeassistant-pythemo`.
5. In the "Category" dropdown, select "Integration".
6. Click "Add" to add the repository.
7. Now, search for "themo" in the "Integrations" tab and install it.

## Configuration

To set up the Themo integration, follow these steps:

1. Go to the Home Assistant UI.
2. Navigate to `Configuration` > `Devices & Services`.
3. Click on `Add Integration` and search for `Themo`.
4. Follow the on-screen instructions to enter your Themo account credentials.

## Features

1. **Climate Entity**: Adjust and monitor the temperature settings of your Themo thermostat.
2. **Light Entity**: Control the light on your Themo device.
3. **Power Entity**: Estimated power of the Themo device. The power is calculated as the device power status (1/0) multiplied by the configure maximum power of the device. Note that the power measurements can be very inaccurate due to really inaccurate power status.
4. **Floor Temperature Entity**: Monitor the floor temperature with the Themo device.
5. **Air Temperature Entity**: Monitor the air temperature with the Themo device.

## Known Issues

- **Note: This integration is currently tested on only one device, and there is no guarantee that it will work properly on other devices.**
- Power entity exhibits serious inaccuracies until the API starts serving correct values.

## Contributions

For issues, contributions, or feature requests related to this integration, please refer to the GitHub repository. For cloud connection implementation details, check out the [pythemo](https://github.com/JonneDatanen/pythemo) package or [Themo API Documentation](https://connect.themo.io/swagger/index.html).

## License

This project is licensed under the MIT License. See the `LICENSE` file in the GitHub repository for more details.

## Additional Resources

- [Themo API Documentation](https://connect.themo.io/swagger/index.html)
- [pythemo](https://github.com/JonneDatanen/pythemo)
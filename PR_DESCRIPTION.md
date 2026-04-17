# Pull Request: Fix HA setup errors, auth flow, and platform correctness

## What this PR fixes

All bugs described here are relative to `main`. Intermediate states introduced and resolved within this branch are not listed.

---

## Critical — Integration setup crashes silently on any error

**File:** `custom_components/themo/__init__.py`

`authenticate()` and `get_all_devices()` were called bare. Any error during HA startup (wrong password, API unreachable, network timeout) raised an unhandled exception and left the config entry permanently broken until HA was manually restarted.

**Fix:** Both calls are now wrapped with HA-idiomatic exceptions:
- `ThemoAuthenticationError` → raises `ConfigEntryAuthFailed` — HA displays a re-authentication prompt to the user automatically.
- `ThemoConnectionError | httpx.TimeoutException` → raises `ConfigEntryNotReady` — HA retries setup with an exponential backoff automatically.

---

## Critical — Multiple Themo accounts/entries corrupt each other's data

**File:** `custom_components/themo/__init__.py`, `custom_components/themo/helpers.py`

`hass.data[DOMAIN]` was a flat dict. A second config entry would overwrite the first. Unloading any entry wiped data for all entries, making all Themo entities unavailable.

**Fix:** Data is now stored per config entry:
```python
hass.data.setdefault(DOMAIN, {})[config_entry.entry_id] = { ... }
```
Unload removes only the relevant entry using `.get(DOMAIN, {}).pop(entry_id, None)`, which also safely no-ops if setup failed before writing to `hass.data`. `helpers.py` updated to read from `hass.data[DOMAIN][entry.entry_id]`.

---

## Critical — Options flow crashes and is non-functional; no way to update credentials

**Files:** `custom_components/themo/config_flow.py`, `custom_components/themo/strings.json`, `custom_components/themo/translations/en.json`

The options flow on `main` always showed its form and never handled `user_input` — it was a complete no-op that never saved anything. In addition, `ThemoOptionsFlowHandler.__init__` used an attribute name that conflicts with HA internals on newer versions.

**Fix:** The options flow has been removed entirely and replaced with a proper HA re-authentication flow (`async_step_reauth` / `async_step_reauth_confirm`). When the integration raises `ConfigEntryAuthFailed` (e.g. at startup), HA automatically triggers this flow. Behaviour:
- Username is pre-filled from the stored config; password field is blank (credentials are never sent to the browser).
- New credentials are validated against the Themo API before anything is saved.
- On success, `config_entry.data` is updated and the entry is reloaded immediately.
- On failure, the form is re-shown with the appropriate error message.
- If the config entry no longer exists mid-flow, the flow aborts cleanly.

Strings updated: `reauth_confirm` step, `reauth_successful` and `entry_not_found` abort reasons added. Dead `options` block removed.

---

## Medium — Polling loop exposes all entities to crashes from one device's errors

**File:** `custom_components/themo/__init__.py`

The coordinator polling loop only caught `httpx.ConnectTimeout`. Any other exception (connection reset, DNS failure, HTTP 4xx/5xx from the schedules endpoint, deserialization error) propagated uncaught and crashed the entire update, making all Themo entities unavailable.

Note: `get_device_schedules` in the pythemo library calls `response.raise_for_status()` directly without wrapping, meaning `httpx.HTTPStatusError` (e.g. HTTP 429, 503) was a realistic uncaught failure path.

**Fix:**
- Broadened the primary catch to `(ThemoConnectionError, httpx.TimeoutException)`, covering all httpx timeout variants and connection errors.
- Added a `except Exception` fallback per device that logs the full traceback and continues to the next device, so one device's error never affects the others.

---

## Low — `current_temperature` returned a status string instead of a temperature

**File:** `custom_components/themo/climate.py`

`current_temperature` returned `self._device.info`, which maps to the `"Info"` API key and is typed `str | None` — a device status string, not a temperature. HA would silently discard the value due to type mismatch and show no current temperature in the climate card.

**Fix:** Changed to `self._device.room_temperature` (`float | None`), the correct ambient temperature field.

---

## Low — Setting temperature to 0°C was silently ignored

**File:** `custom_components/themo/climate.py`

```python
if temperature and self.hvac_mode == HVACMode.HEAT:
```
`0.0` is falsy in Python, so a setpoint of 0°C was silently discarded instead of being sent to the device.

**Fix:** Changed to `if temperature is not None and self.hvac_mode == HVACMode.HEAT`.

---

## Low — All sensor entities used the deprecated `state` property

**File:** `custom_components/themo/sensor.py`

All three sensors (`ThemoPowerSensor`, `ThemoFloorTemperatureSensor`, `ThemoRoomTemperatureSensor`) overrode `state` instead of `native_value`. This bypasses HA's unit conversion pipeline and triggers deprecation warnings in HA ≥ 2023.x. The power sensor also had no guard against `None` values — `device.power * device.max_power * 1e3` would raise `TypeError` if either field was `None` (e.g. on the first coordinator fetch before the device has reported state).

**Fix:** All three sensors now override `native_value` with return type `float | None`. The power sensor returns `None` explicitly if either field is `None`.

---

## Info — Light toggle logged at INFO level

**File:** `custom_components/themo/light.py`

Every `turn_on` / `turn_off` call logged at `INFO`, producing excessive log volume in automations.

**Fix:** Downgraded to `DEBUG`.

---

## Info — Unused imports removed

**Files:** `custom_components/themo/helpers.py`, `custom_components/themo/sensor.py`

- `import logging` and `_LOGGER` in `helpers.py` were defined but never used — removed.
- `from . import DOMAIN` in `sensor.py` is unused directly (used by `helpers.py`) — annotated with `# noqa: F401`.

---

## Files changed

| File | Change |
|------|--------|
| `custom_components/themo/__init__.py` | Setup error handling, multi-entry data storage, polling error isolation |
| `custom_components/themo/config_flow.py` | Options flow removed, re-auth flow added |
| `custom_components/themo/helpers.py` | Updated data access, unused import removed |
| `custom_components/themo/climate.py` | Correct temperature field, 0°C setpoint fix |
| `custom_components/themo/sensor.py` | `native_value`, None guard, noqa annotation |
| `custom_components/themo/light.py` | Log level |
| `custom_components/themo/strings.json` | Reauth strings, options block removed |
| `custom_components/themo/translations/en.json` | Reauth strings, options block removed |

---

## Needs verification before merge

- **Power sensor arithmetic:** `self._device.power * self._device.max_power * 1e3` with `native_unit_of_measurement = UnitOfPower.KILO_WATT`. The unit direction depends on whether `max_power` from the API is in watts or kilowatts, which cannot be confirmed without a live device response. Verify the reported value against a known device wattage.

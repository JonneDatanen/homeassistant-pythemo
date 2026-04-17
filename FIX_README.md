# Fix Branch: `fix/themo-ha-errors-2026-04-14`

## Summary

This branch contains two commits that resolve critical runtime errors in the Themo Home Assistant integration. The bugs would cause setup failures, silent multi-entry data corruption, and an unresponsive options flow.

---

## Commits

| SHA | Subject |
|-----|---------|
| `b13f449` | Fix HA setup handling and options flow crash |
| `44cd4f2` | Fix options flow config entry lifecycle |

---

## Changes by File

### `custom_components/themo/__init__.py`

#### 1. Proper error handling during integration setup

**Before:** `authenticate()` and `get_all_devices()` were called without a try/except. Any network or credential error during setup raised an unhandled exception, leaving the config entry in an undefined broken state.

**After:** Wrapped in try/except with HA-idiomatic exceptions:
- `ThemoAuthenticationError` → raises `ConfigEntryAuthFailed` — HA shows the user a re-authentication prompt.
- `ThemoConnectionError | httpx.TimeoutException` → raises `ConfigEntryNotReady` — HA retries setup automatically after a backoff delay.

**Impact:** Critical. Without this fix, any startup error (wrong password, API down) would permanently break the entry until HA was restarted manually.

#### 2. Per-device update loop error broadening

**Before:** Only caught `httpx.ConnectTimeout` in the per-device polling loop.

**After:** Catches `(ThemoConnectionError, httpx.TimeoutException)`, covering transient DNS failures, connection resets, and all httpx timeout variants.

**Impact:** Medium. Narrow exception catch could let transient errors crash the coordinator update, making all Themo entities unavailable.

#### 3. Multi-entry safe `hass.data` storage

**Before:**
```python
hass.data[DOMAIN] = {"devices": devices, "coordinator": coordinator}
```
A flat dict keyed by domain only. A second Themo config entry would overwrite the first. Unloading any entry wiped data for all entries.

**After:**
```python
hass.data.setdefault(DOMAIN, {})[config_entry.entry_id] = {
    "devices": devices,
    "coordinator": coordinator,
}
```
Data is now keyed by `entry_id`. Unload uses `.pop(entry.entry_id, None)` to remove only the relevant entry.

**Impact:** Critical for multi-device setups (multiple Themo accounts). Also required by HA integration quality guidelines.

---

### `custom_components/themo/config_flow.py`

#### 4. Options flow `config_entry` attribute fix

**Before (main):** `ThemoOptionsFlowHandler.__init__` stored the entry as `self.config_entry`, shadowing the attribute that HA injects automatically in newer versions, causing a crash.

**After (b13f449):** `__init__` was removed entirely; `self.config_entry` was used directly, relying on HA's injected attribute — correct for HA 2024+.

**After (44cd4f2):** `__init__` was re-added storing as `self._config_entry` to be safe across HA versions.

**After (this fix):** `ThemoOptionsFlowHandler` has been removed entirely. Credential changes are now handled by the re-auth flow (see #8 below).

**Impact:** Critical. Opening the options dialog on newer HA would crash with `AttributeError`.

#### 5. Options flow was non-functional (main regression)

**Before (main):** `async_step_init` always showed the form and never handled `user_input` — a complete no-op. Nothing was ever saved.

**After (b13f449):** Added `user_input` check and `async_create_entry` — but this introduced the HIGH credential routing bug (see vulnerabilities section).

**After (this fix):** The entire options flow is removed. Credentials are now managed exclusively through the re-auth flow, which is the correct HA pattern.

**Impact:** High. The dialog appeared to work but was silently non-functional.

#### 6. Options form now pre-fills username; password is intentionally blank

> **This section describes a change that has since been superseded.** The options flow has been removed in favour of a re-auth flow. See #8 below.

#### 8. Re-authentication flow added [NEW]

`ThemoConfigFlow` now implements `async_step_reauth` and `async_step_reauth_confirm`. When HA raises `ConfigEntryAuthFailed` (e.g. at startup with expired credentials), HA automatically triggers this flow. The user is shown a form with the username pre-filled and the password blank. On submit:
- Credentials are validated against the Themo API before anything is saved.
- On success, `config_entry.data` is updated via `async_update_entry` (writing to the correct place) and the entry is reloaded.
- On failure, the form is re-shown with the appropriate error.

This replaces the options flow for credential management entirely.

**Strings updated:** `strings.json` and `translations/en.json` now include a `reauth_confirm` step and `reauth_successful` abort reason. The dead `options` block has been removed from both files.

---

### `custom_components/themo/helpers.py`

#### 7. Updated data access to match new `hass.data` structure

**Before:** `hass.data[DOMAIN]["devices"]` / `hass.data[DOMAIN]["coordinator"]`

**After:** `hass.data[DOMAIN][entry.entry_id]["devices"]` / `hass.data[DOMAIN][entry.entry_id]["coordinator"]`

**Impact:** Required companion change to fix #3 above. Without this, all three platforms (climate, light, sensor) would raise `KeyError` on load after `__init__.py` was patched.

---

## Vulnerabilities & Edge Cases Found During Review

The following issues were identified during analysis. Items marked **[FIXED]** have been resolved; all others remain open.

### SECURITY — Password transmitted in plaintext to browser [FIXED]

**Origin: Introduced by this fix branch, commit `44cd4f2`. Not present on `main`.**

The inline options schema set `default=self._config_entry.data.get(CONF_PASSWORD, "")` on the password field. HA serialises the entire form schema — including all default values — into a JSON payload sent to the browser. This meant the stored plaintext password was visible in the HTTP response and browser DevTools every time the options dialog was opened.

**Fix applied:** The `default` argument has been removed from the `CONF_PASSWORD` field. The password field is now blank when the dialog opens. If the user submits without typing a password, the existing stored password is silently retained.

---

### HIGH — Options flow saves to `entry.options`, not `entry.data` [FIXED]

**Origin: Introduced by commit `b13f449` on this fix branch. Not present on `main` (options flow on `main` never saved anything).**

When `async_create_entry(data=user_input)` is called from an `OptionsFlow`, HA stores the result in `config_entry.options`, not `config_entry.data`. `async_setup_entry` reads credentials exclusively from `config_entry.data`, so any credential update via the options flow was silently discarded after restart.

**Fix applied:** The options flow has been removed entirely. Credential updates now go through `async_step_reauth_confirm`, which calls `async_update_entry(entry, data=user_input)` — writing directly and correctly to `config_entry.data`.

### MEDIUM — Unload can `KeyError` if setup failed early [FIXED]

**Origin: Introduced by commit `b13f449` on this fix branch.** `main` used `hass.data[DOMAIN] = {}` on unload; the fix branch changed it to `hass.data[DOMAIN].pop(entry.entry_id, None)`, but this assumes `hass.data[DOMAIN]` was already created. If `async_setup_entry` raised `ConfigEntryNotReady` before reaching the `hass.data.setdefault(...)` call, the key would not exist.

**Fix applied:**
```python
hass.data.get(DOMAIN, {}).pop(entry.entry_id, None)
```
This safely no-ops if the domain key was never created.

### MEDIUM — Options flow does not re-authenticate [FIXED]

**Origin: Introduced by commit `b13f449` on this fix branch. Not present on `main` (options flow on `main` never saved anything).**

The options flow saved `user_input` directly without calling `ThemoClient.authenticate()`. Invalid credentials would be accepted and stored silently, and the integration would only fail on the next HA restart with no actionable error shown to the user.

**Fix applied:** The re-auth flow validates credentials against the Themo API before calling `async_update_entry`. If authentication fails, the form is re-shown with the appropriate error. Invalid credentials can never be saved.

### LOW — `async_update_data` swallows only network errors per device [FIXED]

**Origin: Present on `main`.**

The polling loop only caught `(ThemoConnectionError, httpx.TimeoutException)`. Any other exception from `device.update_state()` would propagate uncaught, killing the coordinator update and making all entities unavailable with no targeted log entry. This is a real risk: `device.update_state()` calls both `fetch_data()` and `fetch_schedules()`. While `get_device_data` wraps all exceptions as `ThemoConnectionError`, `get_device_schedules` calls `response.raise_for_status()` directly — meaning `httpx.HTTPStatusError` (e.g. HTTP 429, 503) from the schedules endpoint would escape the existing catch.

**Fix applied:** Added a broad `except Exception` fallback that logs the full traceback with `_LOGGER.exception(...)` and continues to the next device, preventing one device's error from affecting others.

### LOW — `ThemoPowerSensor.native_value` crashes with `TypeError` when fields are `None` [FIXED]

**Origin: Present on `main`.**

`device.power` and `device.max_power` are both typed `float | None` in the pythemo `Device` model. The expression `self._device.power * self._device.max_power * 1e3` raises `TypeError` if either is `None` (e.g. on a partial API response or before the first successful state update). Despite the return type annotation `float | None`, the body never actually returned `None`.

**Fix applied:** Added an explicit None guard — returns `None` early if either field is `None`.

### LOW — `async_set_temperature` silently drops a 0°C setpoint [FIXED]

**Origin: Present on `main`.**

```python
if temperature and self.hvac_mode == HVACMode.HEAT:
```
`0.0` is falsy in Python. A setpoint of exactly 0°C would be silently ignored. For a floor heating thermostat this is unlikely in practice but is still incorrect logic.

**Fix applied:** Changed to `if temperature is not None and ...`.

### LOW — `async_step_reauth_confirm` crashes if config entry is deleted mid-flow [FIXED]

**Origin: Introduced by this fix branch.**

`async_get_entry` returns `None` if the entry was deleted between the reauth flow being triggered and the user submitting the form. The None-guard only covered the form default; the success path called `async_update_entry(entry, ...)` and `async_reload(entry.entry_id)` unconditionally, which would raise `AttributeError` on `None`.

**Fix applied:** Added an early `if entry is None: return self.async_abort(reason="entry_not_found")` guard at the top of the method. `entry_not_found` added to `strings.json` and `translations/en.json`.

### INFO — Unused imports [FIXED]

**Origin: Present on `main`.**

- `import logging` / `_LOGGER` in `helpers.py` — defined but never used; removed.
- `from . import DOMAIN` in `sensor.py` — imported but not used directly in that file (helpers imports it separately); annotated with `# noqa: F401` to clarify the intent.

### LOW — `ClimateEntity.current_temperature` uses `device.info` [FIXED]

**Origin: Present on `main`.** The `info` field is typed `str | None` in the pythemo `Device` model — it maps to the `"Info"` API key and contains a status string, not a temperature reading. Returning it as `current_temperature` would cause HA to silently discard the value (type mismatch) or display corrupt data.

**Fix applied:** Changed to `self._device.room_temperature` (`float | None`), which is the correct ambient temperature reading the thermostat controls against.

### LOW — `SensorEntity` uses deprecated `state` property [FIXED]

**Origin: Present on `main`.** All three sensor classes overrode `state` instead of `native_value`. The `native_value` property is the correct modern contract for `SensorEntity` and allows HA to perform unit conversion. Using `state` bypasses unit conversion logic and triggers deprecation warnings in HA ≥ 2023.x.

**Fix applied:** All three sensors (`ThemoPowerSensor`, `ThemoFloorTemperatureSensor`, `ThemoRoomTemperatureSensor`) now override `native_value` with the return type widened to `float | None` to match the nullable `Device` model fields.

### INFO — `info`-level logging for every light toggle [FIXED]

**Origin: Present on `main`.** `light.py` logged at `INFO` on every `turn_on`/`turn_off` call. Automations toggling lights frequently would produce excessive log volume.

**Fix applied:** Both calls changed to `_LOGGER.debug(...)`.

---

## Files Changed

| File | Lines changed | Type |
|------|--------------|------|
| `custom_components/themo/__init__.py` | +24 / -8 | Bug fix |
| `custom_components/themo/config_flow.py` | +44 / -35 | Bug fix + security fix |
| `custom_components/themo/helpers.py` | +3 / -4 | Companion fix + cleanup |
| `custom_components/themo/climate.py` | +1 / -1 | Bug fix (wrong field + 0°C guard) |
| `custom_components/themo/sensor.py` | +5 / -3 | Deprecation fix + None guard |
| `custom_components/themo/light.py` | +2 / -2 | Log level fix |
| `custom_components/themo/strings.json` | +11 / -10 | Updated for reauth |
| `custom_components/themo/translations/en.json` | +11 / -10 | Updated for reauth |

---

## Testing Recommendations

- [ ] Verify integration loads cleanly with valid credentials
- [ ] Verify `ConfigEntryAuthFailed` is raised (and HA shows re-auth prompt) for bad credentials at startup
- [ ] Verify `ConfigEntryNotReady` is raised (and HA retries) when API is unreachable
- [ ] Verify re-auth form pre-fills username and leaves password blank
- [ ] Verify re-auth rejects invalid credentials with an error (does not save)
- [ ] Verify re-auth with valid credentials updates `config_entry.data` and reloads the entry
- [ ] Verify that two Themo config entries can coexist without overwriting each other
- [ ] Verify that unloading one entry does not remove data for the other
- [ ] Verify unloading an entry that failed setup (never reached `hass.data`) does not raise `KeyError`
- [ ] Verify `current_temperature` in climate card shows a numeric temperature (not `None` or a string)
- [ ] Verify power sensor reports `None` (unavailable) rather than crashing when device state is not yet populated
- [ ] Verify sensor `native_value` is reported correctly in HA (no deprecation warnings in logs)
- [ ] Verify light toggle does not produce `INFO` log entries (only `DEBUG`)
- [ ] Verify options gear icon no longer appears in the HA integrations UI (options flow removed)
- [ ] Verify `ThemoPowerSensor` reading against a known device wattage to confirm `* 1e3` arithmetic is correct

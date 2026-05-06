# onrobot-api

This is a repository for Python API of OnRobot grippers. The `script` folder includes modules for **RG2**, **2GF7**, **VGC10**, and **Soft Gripper** gripper models.

Modules:

- **Device**: `device.py`
- **RG2**: `rg2.py`
- **2GF7**: `twofg.py`
- **VGC10**: `vgc10.py`
- **Soft Gripper**: `sg.py`

---

## Run checks locally

```bash
uv sync --dev
uv run python -m compileall .
uv run ruff check .
uv run pytest -q
uv build
```

Configure repository branch protection to require the `CI` workflow before merge.

---

## Gripper Status

|  Status | Description  |
|---|---|
| 0 | Stable |
| -1 | Error |
| -2 | Connection Failed  |

## Auto Detection and Dimensions

Use `detect_gripper` to identify a connected supported gripper and optionally
receive a ready-to-use client instance:

```python
from onrobot import Device, detect_gripper

device = Device("192.168.101.95")
detected = detect_gripper(device)
print(detected.key)
print(detected.dimensions)
```

`detect_gripper_type(device)` returns only the detected key. Supported keys are
`twofg7`, `rg2`, `vgc10`, `vg10`, and `sg`.

Each modern client also exposes `get_dimensions(t_index=0)`, returning a
`GripperDimensions` dataclass. All numeric dimension fields are in millimeters.
Static body dimensions are populated from OnRobot datasheets; live TCP-relevant
fields such as current width, depth, finger settings, and tool type are enriched
from XML-RPC where the Compute Box exposes them.

---

## Python API reference for **2FG7**

|  Methods | Description  |  Input |
|---|---|---|
| grip  | Moves the gripper to the desired position  | **t_width**: *Default=20.0 (mm)*, **n_force**: *Default=20 (N)*, **p_speed**: *Default=10(%)*, **f_wait**: *Default=True*  |
| move  | Moves the gripper to the desired position  | **t_width**: *Default=20.0 (mm)*, **f_wait**: *Default=True*|
| stop  | Stops the action  | - |
| isConnected  | Returns **True** if the gripper is connected, **False** otherwise  | - |
| isBusy  | Returns **True** if there is an obstacle during operation, **False** otherwise   | - |
| isGripped  | Returns **True** if an object is gripped, **False** otherwise   | - |
| getStatus  | Returns current status of the gripper (No connection=-2, Error=-1, Stable=0)  | - |
| get_ext_width  | Returns current width between fingers | - |
| get_force  | Returns current force on the gripper (in Newton) | - |
| get_min_ext_width  | Returns minimum gripping width  | - |
| get_max_ext_width  | Returns minimum gripping width  | - |
| get_finger_orientation_label  | Returns `"inward"` or `"outward"` when available  | - |
| set_finger_orientation  | Sets finger orientation (`"inward"`/`"outward"` or boolean flag)  | - |
| get_dimensions | Returns static and live gripper dimensions in mm | - |

Primary API naming now follows `snake_case` (for example `is_connected`,
`is_busy`, `is_gripped`). Legacy camelCase methods are still available as
compatibility wrappers and emit deprecation warnings.

Note: `set_finger_orientation` falls back to the Compute Box REST endpoint
`/api/dc/twofg/set_finger_orientation/{t_index}/{true|false}` when the XML-RPC
method is not available.

### Status stream (Socket.IO)

The Compute Box publishes device status over Socket.IO. Use the helper to
subscribe and read the latest gripper variables (width, force, orientation, etc):

```python
from onrobot.status_client import OnRobotStatusClient

client = OnRobotStatusClient("192.168.101.180")
client.connect()
status = client.get_device_variable(device_id=0, product_code=0xC0)
print(status)
```

### **Input parameter explanation**

- **t_width**: width to move the gripper to in mm's (*float*)
- **n_force**: force to move the gripper width in N (*float*)
- **p_speed**: speed of the gripper in % compared to full speed (*int*)
- **f_wait**: wait for the gripper to end or not (*Boolean*)

### **Example script for 2FG7**

```python
from device import Device
from twofg import TWOFG

device = Device()
gripper = TWOFG(device)
gripper.isConnected()   # for checking connection
```

---

## Python API reference for **RG2**

Primary methods:

| Methods | Description | Input |
|---|---|---|
| `move_grip` | Moves the gripper to the desired width and force | **twidth**: mm, **tforce**: N, **wait**: bool |
| `grip_with_detection` | Moves and waits for grip detection when requested | **twidth**: mm, **tforce**: N, **wait**: bool |
| `is_connected` | Returns `True` when RG2 is connected | - |
| `get_width` | Returns current width in mm | - |
| `get_depth` / `get_rel_depth` | Return current absolute/relative depth in mm | - |
| `get_ft_offset` | Returns current fingertip offset in mm | - |
| `get_dimensions` | Returns static and live gripper dimensions in mm | - |

Legacy methods remain available as compatibility wrappers.

---

## Python API reference for **Soft Gripper**

The Soft Gripper API uses XML-RPC and requires explicit initialization before
motion commands. The default static tool type is `SG-a-S`.

Supported tool types:

| Tool type | Tool ID |
|---|---:|
| `SG-a-H` | 2 |
| `SG-a-S` | 3 |
| `SG-b-H` | 4 |

Primary methods:

| Methods | Description | Input |
|---|---|---|
| `initialize` | Initializes the selected SG tool type | **tool_type**: *Default=`SG-a-S`*, **wait**: *Default=True* |
| `calibrate` | Calibrates the Soft Gripper | **wait**: *Default=True* |
| `move_to_width` | Moves to a target width without grip mode | **width**: mm, **gentle**: *Default=True*, **wait**: *Default=True* |
| `grip` | Runs a grip command | **width**: mm, **gentle**: *Default=False*, **wait**: *Default=True* |
| `gentle_grip` | Runs a gentle grip command | **width**: mm, **wait**: *Default=True* |
| `home` | Sends the gripper to home position | **wait**: *Default=True* |
| `stop` | Stops the current action | - |
| `is_connected` | Returns `True` when Soft Gripper is connected | - |
| `is_initialized` | Returns current initialization state | - |
| `is_busy` | Returns current busy state | - |
| `is_gripped` | Returns current grip detection state | - |
| `is_calibrated` | Returns current calibration state | - |
| `get_tool_id` | Returns current SG tool ID | - |
| `get_width` | Returns current width | - |
| `get_depth` | Returns current depth | - |
| `get_depth_relative` | Returns relative depth | - |
| `get_max_depth` | Returns static silicone depth | - |
| `get_min_max` | Returns `min_open` and `max_open` | - |
| `get_min_open` / `get_max_open` | Return current width limits | - |
| `get_status` / `get_error` | Return current status and error code | - |
| `get_operation_counter` | Returns the Soft Gripper operation counter | - |
| `get_dimensions` | Returns static and live gripper dimensions in mm | - |
| `get_all_variables` | Returns the raw SG variable dictionary | - |
| `get_all_double_variables` | Returns raw double variable array | - |
| `get_all_integer_variables` | Returns raw integer variable array | - |
| `get_all_boolean_variables` | Returns raw boolean variable array | - |
| `start_status_stream` | Starts Socket.IO status updates | **on_update**: callback, **timeout_s**: *Default=2.0* |
| `get_status_snapshot` | Returns latest SG Socket.IO variable snapshot | - |
| `stop_status_stream` | Stops Socket.IO status updates | - |

Example:

```python
from onrobot import Device, SG

device = Device("192.168.101.95")
gripper = SG(device)  # defaults to SG-a-S
gripper.initialize()
gripper.move_to_width(width=56)
```

---

## Python API reference for **VG10/VGC10**

The VG API supports both VG10 and VGC10 product IDs and controls vacuum per
channel through XML-RPC.

Primary methods:

| Methods | Description | Input |
|---|---|---|
| `grip_vacuum` | Starts vacuum on channels A and B | **vacuum_a**/**vacuum_b**: 1-80, **wait**: *Default=False* |
| `release_vacuum` | Releases selected channels | **channel_a**/**channel_b**: booleans, **wait**: *Default=False* |
| `idle_vacuum` | Turns off pump on selected channels | **channel_a**/**channel_b**: booleans |
| `is_connected` | Returns `True` when VG10 or VGC10 is connected | - |
| `is_vg10` / `is_vgc10` | Returns concrete connected VG model | - |
| `get_vacuum` | Returns `a_vacuum` and `b_vacuum` | - |
| `get_vacuum_a` / `get_vacuum_b` | Return individual channel vacuum | - |
| `get_dimensions` | Returns static VG10/VGC10 dimensions in mm | - |
| `get_all_double_variables` | Returns raw vacuum double array | - |
| `get_operation_counter` | Returns VG operation counter | - |
| `start_status_stream` | Starts Socket.IO status updates | **on_update**: callback, **timeout_s**: *Default=2.0* |
| `get_status_snapshot` | Returns latest VG10/VGC10 Socket.IO variable snapshot | - |
| `stop_status_stream` | Stops Socket.IO status updates | - |

Legacy methods `grip`, `release`, `idle`, `getvacA`, and `getvacB` remain
available as compatibility wrappers.

---

## Decoding byte string to a python script

run `api_byte2script.py` to create `legacy/api_original.py`

```bash
python3 /path/to/onrobot-api/api_byte2script.py
```

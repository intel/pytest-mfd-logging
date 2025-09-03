> [!IMPORTANT] 
> This project is under development. All source code and features on the main branch are for the purpose of testing or evaluation and not production ready.

# Pytest MFD Logging
pytest plugin to handle logging.

## Usage

Logging will be configured if only plugin is installed, no need to call it explicitly.
Default values for logging parameters are stored in pytest_mfd_logging\configs\pytest.ini.

Hierarchy of parameters importance:
1) command line params
2) values from ini file located in project's root
3) default values from `configs\pytest.ini`

- `configs\pytest.ini` content:
```
[pytest]
log_cli=True
log_format=%(asctime)s %(name)22.22s:%(funcName)-18.18s %(levelname)-13.13s
log_date_format=%Y-%m-%d %H:%M:%S
log_cli_level=DEBUG

log_file_format=%(asctime)s %(name)22.22s:%(funcName)-18.18s %(levelname)-13.13s
log_file_date_format=%Y-%m-%d %H:%M:%S
log_file_level=DEBUG
```

- FILE LOGGING: it's already configured, but not enabled. If you want to log to a file you need to provide a path to a file.
Path should be provided in root's .ini file (`log_file`) or in args (`--log-file`).

## Live logging
We still log things with Python logger, but display part is based on pytest logging mechanism.
pytest is just gathering all logs, but it's not turning off other loggers.
That's why when enabling live logging in pytest double logs are printed - one print from logging module, one from pytest.
To get rid of redundant logs we can remove stream handler from root logger.
This is better solution than turning off whole logger, because we don't close other handlers.
This is implemented in pytest_mfd_logging.py / _remove_stream_handler().

To be able to use mfd_common_libs' log levels in .ini file or in cmd args we need to add those custom levels to logger. 
This is implemented in pytest_mfd_logging.py / _add_all_logging_levels().

When triggering tests from cmd after live logs we can see displayed captured logs from setup - to turn off pass `--show-capture=no`.

- Why format in .ini file is missing %(msg)s or %(message)s?
  - Because we're defining there only "prefix", which will be formatted and after that msg will be added.
- Why we're defining there only "prefix"?
  - Because to make indentations for every line of msg (to make it more column-like logs) we need to wrap pytest's formatters with our custom.
    Our formatter is formatting "prefix" with pytest's formatter, extending msg with spaces and joining them together.
    So if you'll define your own "prefix" - msg will be added.
    But if you'll provide format which has %(msg) or %(message) inside - our formatter will not overwrite pytest's.

## JSON logging
With the usage of `pytest-json-report` (https://pypi.org/project/pytest-json-report/) we can get all logs with its details as a JSON after tests.
This plugin is also gathering things like duration or plugins used.
Dict with results can be accessed by few different hooks - in our case we're using `pytest_json_modifyreport`.
We can parse it as we wish - just to show how it's working we've implemented flow:
1) if plugin enabled, we receive dict with data in `pytest_json_modifyreport`
2) for each test we create separate file
3) in each file 3 sections are created - SETUP, TEST, TEARDOWN
4) from pytest.ini file we get log format
5) logs for each section are parsed with asked format
6) after logs, duration is printed

- Example of a parsed JSON:
```
2022-12-28 17:27:37 - CMD - rpyc.py:execute_command - Executing >10.102.55.33> 'ip addr del 1.1.2.1/32 dev eth1', cwd: None
2022-12-28 17:27:37 - MODULE_DEBUG - rpyc.py:execute_command - Finished executing '['ip', 'addr', 'del', '1.1.2.1/32', 'dev', 'eth1']', rc=0, output:
-------------------- TEARDOWN passed in 1.9042961000000034 --------------------
```

Logs can be parsed to different format, there can be implemented check if log level is above the one from ini file, and so on...
The only concern is performance in tests which would produce tons of logs.

`--json-report`: to enable

`--parsed-json-path`: path to a folder in which parsed json logs will be stored (folder will be created if doesn't exist)

`--json-report-file`: path to dump raw json into a file

- Example of command line to enable json logging
```
--json-report --json-report-file C:\logs.json --parsed-json-path C:\logs
```

- Example of a log msg with its details:
```json
{
    "name": "mfd_connect.base",
    "msg": "RPyCConnection established with: OSType.POSIX, OSName.LINUX, OSBitness.OS_64BIT, 10.11.12.13",
    "args": null,
    "levelname": "MODULE_DEBUG",
    "levelno": 13,
    "pathname": "C:\\Users\\someuser\\venv\\lib\\site-packages\\mfd_connect\\base.py",
    "filename": "base.py",
    "module": "base",
    "exc_info": null,
    "exc_text": null,
    "stack_info": null,
    "lineno": 215,
    "funcName": "log_connected_host_info",
    "created": 1672247127.0405319,
    "msecs": 40.53187370300293,
    "relativeCreated": 1161.8530750274658,
    "thread": 13316,
    "threadName": "MainThread",
    "processName": "MainProcess",
    "process": 3480,
    "asctime": "2022-12-28 18:05:27"
}
``` 

## Parameters ids
This plugin provides implementation of PyTest hook `pytest_make_parametrize_id`. It will automatically show values of parameters for each set,
generated by `pytest.mark.parametrize`.
Example:
```python
@pytest.mark.parametrize(
    'a, b',
    [
        (1, {'Two Scoops of Django': '1.8'}),
        (True, 'Into the Brambles'),
        ('Jason likes cookies', [1, 2, 3]),
    ],
)
@pytest.mark.parametrize(
    'c',
    [
        'hello world',
        123,
    ],
)
def test_foobar(a, b, c):
    assert True
```
```shell
test_ids.py::test_foobar[|c = hello world|-|a = 1|-|b = {'Two Scoops of Django': '1.8'}|] PASSED
test_ids.py::test_foobar[|c = hello world|-|a = True|-|b = Into the Brambles|] PASSED
test_ids.py::test_foobar[|c = hello world|-|a = Jason likes cookies|-|b = [1, 2, 3]|] PASSED
test_ids.py::test_foobar[|c = 123|-|a = 1|-|b = {'Two Scoops of Django': '1.8'}|] PASSED
test_ids.py::test_foobar[|c = 123|-|a = True|-|b = Into the Brambles|] PASSED
test_ids.py::test_foobar[|c = 123|-|a = Jason likes cookies|-|b = [1, 2, 3]|] PASSED

================================================== 6 passed in 0.03s ==================================================
```

## Log Filtering by level or name
To make filtering logs easy we've introduced `--filter-out-levels` command line parameter.
This can be useful when log levels you want to see and these which you want to filter out are not in right order, so they can't be simply disabled by for example `log-cli-level`.
Those cli params can be provided together.

`--filter-out-levels` accepts a list of substrings of log levels names or partial names (separated by whitespace only names).
Capitalization of letters does not matter as they all will be `.upper()`.
Given substrings are checked by `in` operator of `string` type.
So to match for example `MFD_DEBUG` you can pass `MFD`, `MFD_`, `_DEBUG`, `MFD_DEBUG`, ...

Example for single log level or partial log level name:
- `--filter-out-levels MFD`

Example for more filtered out log levels (when list is provided):
- `--filter-out-levels BL MFD TEST_DEBUG`

To check what log levels are available please refer to:
1) [mfd-common-libs](https://github.com/intel/mfd-common-libs/blob/main/mfd_common_libs/log_levels.py)
   for custom Amber log levels.
2) [logging](https://docs.python.org/3.10/library/logging.html#logging-levels)
   for Python's build-in module `logging` levels,

Command line examples:

Let's assume our logging has 6 levels:
1) DEBUG = 10
2) MFD_DEBUG = 11
3) BL_DEBUG = 12
4) INFO = 20
5) MFD_INFO = 21
6) BL_INFO = 22

- `--filter-out-levels MFD` - log levels displayed from points: 1), 3), 4), 6)
- `--log-cli-level INFO` - log levels displayed from points: 4), 5), 6)
- `--log-cli-level INFO --filter-out-levels MFD` - log levels displayed from points: 4), 6)
- `--filter-out-levels MFD BL` - log levels displayed from points: 1), 4)

## Test origin marker

You can mark `test` / `class` / `file` with one of the markers:
- `MBT_Waypoints`
- `MBT_AI`
- `AI`

> [!IMPORTANT]
> If no marker will be detected, test will be assumed to be written manually by engineer.

#### How?

`test` / `class` can be marked with the decorator like so

```python
from pytest_mfd_logging import marker

@marker.MBT_Waypoints
class TestSomeModule:
    ...
```

```python
from pytest_mfd_logging import marker

class TestSomeModule:

    @marker.MBT_AI
    def test_connections(self):
        ...
```

`file` can be marked with keyword like so
```python
from pytest_mfd_logging import marker

pytestmark = marker.AI
```

#### Results

Marker will become visible in logs and in JSON report.

In logs as a message:
```text
2024-06-12 13:14:42.907 pytest_mfd_logging.pyt:pytest_runtest_set TEST_INFO     Test tests/simple/test_connections.py::TestSomeModule::test_connection was implemented with MBT_AI
```

In JSON report in metadata section:
```json
"metadata": {
  "created_with": "MBT_AI"
}
```

If no marker will be detected proper message will be logged:
```text
2024-06-12 13:17:59.982 pytest_mfd_logging.pyt:pytest_runtest_set TEST_INFO     Test tests/simple/test_connections.py::TestSomeModule::test_connection was implemented manually
```

#### How to combine `test` marker with `class` or `file`?

It's allowed to combine different levels of markers.\
Marker logged to the console will be the first one met when checking scopes - starting from the `test` scope and moving up so to class, file, and so on.\
In JSON report same marker logged to the console will be visible in metadata.

Example

```python
from pytest_mfd_logging import marker

pytestmark = marker.AI


@marker.MBT_Waypoints
class TestSomeModule:

    @marker.MBT_AI
    def test_connection(self):
        ...
```

Will result in reporting

```text
2024-06-12 13:19:00.447 pytest_mfd_logging.pyt:pytest_runtest_set TEST_INFO     Test tests/simple/test_connections.py::TestSomeModule::test_connection was implemented with MBT_AI
```

```json
"metadata": {
  "created_with": "MBT_AI"
}
```

## HTML template
Due to the fact that we're using our custom Formatter to increase readability of logs, 
we were not able to use default Jinja template for `pytest-reporter-html1` plugin.
Because of limitations of Jinja and mentioned plugin we were also not able to use extension mechanisms.
That's why in `templates` folder you can find whole html/Jinja template.
If you want to generate html report just use those arguments:

`--template`: html index file, in this case it would be `html/index.html`, 
              because we've implemented hook to automatically provide plugin's `templates` folder to Jinja environment

`--report`: html report path

## OS supported:

* Every OS supported by pytest

## Issue reporting

If you encounter any bugs or have suggestions for improvements, you're welcome to contribute directly or open an issue [here](https://github.com/intel/pytest-mfd-logging/issues).
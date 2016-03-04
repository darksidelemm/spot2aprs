# spot2aprs
Spot Tracker to APRS Utility

## Usage
This script is intended to be run as a cron-job, at whatever update rate you wish (noting that the Spot API terms and conditions specify a maximum 2.5 min update rate).

```
usage: python spot2aprs.py [-h] [--symboltable SYMBOLTABLE] [--symbolcode SYMBOLCODE]
                    [--maxage MAXAGE] [--verbose]
                    mycall passcode spotkey

positional arguments:
  mycall                Callsign and SSID, for use on APRS, i.e. N0CALL-1.
  passcode              APRS-IS Passcode.
  spotkey               FindMeSpot API Key

optional arguments:
  -h, --help            show this help message and exit
  --symboltable SYMBOLTABLE
                        APRS Symbol Table (see
                        http://www.aprs.org/symbols.html)
  --symbolcode SYMBOLCODE
                        APRS Symbol Code
  --maxage MAXAGE       Maximum age of position reports to upload (minutes).
  --verbose             Increase verbosity.
```


## Dependencies
* Python 2.7 (Python 3 will probably work too)
* Python Requests
 * Install with: `pip install requests`
* Python-APRS
 * pip version has bugs (for now), so install using:
   * `git clone https://github.com/darksidelemm/aprs.git`
   * `cd aprs`
   * `sudo python setup.py install`

#!/usr/bin/env python2.7
#
#	Spot Tracker APRS Uploader
#
#	Mark Jessop <vk5qi@rfhead.net>
#
#
#	TODO:
#	[ ] Nicer error checking (instead of just bombing out)

import socket
socket.setdefaulttimeout(10)
import aprs, requests, json, sys, argparse, datetime, dateutil.parser, dateutil.tz


def create_location_frame(source, latitude, longitude, altitude, course, speed,
                          symboltable, symbolcode, comment=None,
                          destination='APRS', path=[]):
    """
    Creates an APRS Location frame.
    :param source: Source callsign (or callsign + SSID).
    :param latitude: Latitude.
    :param longitude: Longitude.
    :param altitude: Altitude.
    :param course: Course.
    :param speed: Speed.
    :param symboltable: APRS Symboltable.
    :param symbolcode: APRS Symbolcode.
    :param comment: Comment field. Default: Module + version.
    :param destination: Destination callsign. Default: 'APRS'.
    :param path: APRS Path.
    :return: APRS location frame.
    :rtype: str
    """
    comment = comment or 'APRS Python Module'

    location_text = ''.join([
        '!',
        latitude,
        symboltable,
        longitude,
        symbolcode,
        "%03d" % course,
        '/',
        "%03d" % speed,
        '/',
        'A=',
        "%06d" % altitude,
        ' ',
        comment
    ]).encode()

    print(location_text)

    return aprs.Frame(source, destination, path, location_text)


spot_api_url = "https://api.findmespot.com/spot-main-web/consumer/rest-api/2.0/public/feed/%s/message.json"

parser = argparse.ArgumentParser()
# Mandatory Arguments
parser.add_argument("mycall",type=str, help="Callsign and SSID, for use on APRS, i.e. N0CALL-1.")
parser.add_argument("passcode",type=int, help="APRS-IS Passcode.")
parser.add_argument("spotkey",type=str,help="FindMeSpot API Key")
# Optional Arguments
parser.add_argument("--symboltable",default='/',help="APRS Symbol Table (see http://www.aprs.org/symbols.html)")
parser.add_argument("--symbolcode",default='j',help="APRS Symbol Code")
parser.add_argument("--maxage",default=15,help="Maximum age of position reports to upload (minutes).")
parser.add_argument("--verbose",action="store_true",help="Increase verbosity.")
args = parser.parse_args()


if args.verbose:
    print("Options")
    print("-------")
    print("Callsign:\t\t %s" % args.mycall)
    print("Spot API Key:\t\t %s" % args.spotkey)
    print("APRS Symbol Table:\t %s" % args.symboltable)
    print("APRS Symbol Code:\t %s" % args.symbolcode)
    print("Maximum Spot Age:\t %d" % int(args.maxage))


#
#	Attempt to gather the JSON blob from the Spot API.
#

spot = requests.get(spot_api_url % str(args.spotkey))

# Bomb out of we don't get a HTTP OK back from the server. 
if spot.status_code != 200:
    print("ERROR: API Status code %d" % spot.status_code)
    sys.exit(1)


spot_data = spot.json()['response']['feedMessageResponse']

if args.verbose:
    print("Received %d Spot Messages." % spot_data.get('count',0))

# Pull out latest message from the huge list of messages.
last_message = spot_data.get('messages', {}).get('message', {})[0]

# Extract data from message.

# Parse ISO 8601 time string.
message_time = dateutil.parser.parse(last_message['dateTime'])
# Time-zone aware age calculation
current_time = datetime.datetime.utcnow()
current_time = current_time.replace(tzinfo=dateutil.tz.tzutc())
message_age = current_time - message_time
message_age_minutes = int(message_age.seconds/60.0)

latitude = last_message['latitude']
longitude = last_message['longitude']
comment = "%s %s %s Batt: %s" % (last_message['messengerName'],last_message['modelId'],last_message['messageType'],last_message['batteryState'])

if args.verbose:
    print("\n\nGot Spot: %.5f, %.5f  %s" % (latitude, longitude, comment))
    print("Message Time: %s" % str(last_message['dateTime']))
    print("Message Age: %d minutes." % (message_age_minutes))

# Don't proceed to the APRS upload section if the message is too old.
if message_age_minutes > int(args.maxage):
    print("Message too old (%d min), not uploading." % message_age_minutes)
    sys.exit(1)

# Create APRS frame.

frame = create_location_frame(
    source=args.mycall,
    destination='APRS',
    latitude = aprs.geo_util.dec2dm_lat(latitude),
    longitude = aprs.geo_util.dec2dm_lng(longitude),
    course=0,
    speed=0, # TODO: Estimate speed from previous positions. Probably not too much value given long update times.
    altitude=0,
    symboltable=args.symboltable[0],
    symbolcode=args.symbolcode[0],
    comment=comment
    )

if args.verbose:
    print("\n\n APRS Frame: %s" % frame)

#
#	Attempt to upload to APRS-IS
#
ais = aprs.TCP(args.mycall.encode(),str(args.passcode))
ais.start()
ais.send(bytes(frame))

if args.verbose:
    print("Uploaded frame to APRS-IS!")


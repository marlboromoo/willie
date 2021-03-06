# coding=utf-8
"""
ip.py - Willie IP Lookup Module
Copyright 2011, Dimitri Molenaars, TyRope.nl,
Copyright © 2013, Elad Alfassa <elad@fedoraproject.org>
Licensed under the Eiffel Forum License 2.

http://willie.dftba.net
"""

import re
import pygeoip
import socket
import os

try:
    import gzip
    from urllib import urlretrieve
    can_download = True
except ImportError:
    can_download = False

from willie.module import commands, example


def configure(config):
    """

    | [ip] | example | purpose |
    | ---- | ------- | ------- |
    | GeoIP_db_path | None | Full path for the GeoIP database. If not specified or None, the bot will try to look for the database in /usr/share/GeoIP, and if it's not there it'll try to automatically download the database into its configuration directory |
    """
    if config.option('Configure a custom location for the GeoIP db?', False):
        config.add_section('ip')
        config.interactive_add('ip', 'GeoIP_db_path', 'Full path to the GeoIP database', None)


def _decompress(source, target, delete_after_decompression = True):
    """ Decompress a GZip file """
    f_in = gzip.open(source, 'rb')
    f_out = open(target, 'wb')
    f_out.writelines(f_in)
    f_out.close()
    f_in.close()
    if delete_after_decompression:
        os.remove(source)


def _find_geoip_db(bot):
    """ Find the GeoIP database """
    config = bot.config
    if config.has_section('ip') and config.ip.GeoIP_db_path is not None:
        if (os.path.isfile(os.path.join(config.ip.GeoIP_db_path, 'GeoLiteCity.dat')) and 
           os.path.isfile(os.path.join(config.ip.GeoIP_db_path, 'GeoIPASNum.dat'))):
            return config.ip.GeoIP_db_path
        else:
            bot.debug(__file__, 'GeoIP path configured but DB not found in configured path', 'warning')
    if (os.path.isfile(os.path.join(bot.config.homedir, 'GeoLiteCity.dat')) and
            os.path.isfile(os.path.join(bot.config.homedir, 'GeoIPASNum.dat'))):
        return bot.config.homedir
    elif (os.path.isfile(os.path.join('/usr/share/GeoIP', 'GeoLiteCity.dat')) and
           os.path.isfile(os.path.join('/usr/share/GeoIP', 'GeoIPASNum.dat'))):
            return '/usr/share/GeoIP'
    elif can_download:
        bot.debug(__file__, 'Downloading GeoIP database', 'always')
        bot.say('Downloading GeoIP database, please wait...')
        geolite_city_url = 'http://geolite.maxmind.com/download/geoip/database/GeoLiteCity.dat.gz'
        geolite_ASN_url = 'http://download.maxmind.com/download/geoip/database/asnum/GeoIPASNum.dat.gz'
        geolite_city_filepath = os.path.join(bot.config.homedir, 'GeoLiteCity.dat.gz')
        geolite_ASN_filepath = os.path.join(bot.config.homedir, 'GeoIPASNum.dat.gz')
        urlretrieve(geolite_city_url, geolite_city_filepath)
        urlretrieve(geolite_ASN_url, geolite_ASN_filepath)
        _decompress(geolite_city_filepath, geolite_city_filepath[:-3])
        _decompress(geolite_ASN_filepath, geolite_ASN_filepath[:-3])
        return bot.config.homedir
    else:
        return False


@commands('iplookup', 'ip')
@example('.ip 8.8.8.8')
def ip(bot, trigger):
    """IP Lookup tool"""
    if not trigger.group(2):
        return bot.reply("No search term.")
    query = trigger.group(2)
    db_path = _find_geoip_db(bot)
    if db_path is False:
        bot.debug(__file__, 'Can\'t find (or download) usable GeoIP database', 'always')
        bot.say('Sorry, I don\'t have a GeoIP database to use for this lookup')
        return False
    geolite_city_filepath = os.path.join(_find_geoip_db(bot), 'GeoLiteCity.dat')
    geolite_ASN_filepath = os.path.join(_find_geoip_db(bot), 'GeoIPASNum.dat')
    gi_city = pygeoip.GeoIP(geolite_city_filepath)
    gi_org = pygeoip.GeoIP(geolite_ASN_filepath)
    host = socket.getfqdn(query)
    response = "[IP/Host Lookup] Hostname: %s" % host
    response += " | Location: %s" % gi_city.country_name_by_name(query)
    region = gi_city.region_by_name(query)['region_name']
    if region is not '':
        response += " | Region: %s" % region
    isp = gi_org.org_by_name(query)
    if isp is not None:
        isp = re.sub('^AS\d+ ', '', isp)
    response += " | ISP: %s" % isp
    bot.say(response)

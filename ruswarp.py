import daemon
import lockfile
import logging
import netifaces
import os
import pymongo
import time
import settings
import subprocess

from driver import RuswarpDriver

logger = logging.getLogger()
logger.setLevel(logging.DEBUG)
fh = logging.FileHandler("logs/app.log")
logger.addHandler(fh)


class RuswarpContext(daemon.DaemonContext):
    vpn_backoff = 0

    def open(self):
        if self.is_open:
            return
        super(RuswarpContext, self).open()

        self.ensure_vpn()
        self.driver = RuswarpDriver()
        self.db_client = pymongo.MongoClient(settings.MONGODB_URI)

    def close(self):
        if not self.is_open:
            return
        self.driver.quit()
        self.db_client.close()
        super(RuswarpContext, self).close()

    def open_vpn(self):
        subprocess.call("sudo pon {}".format(settings.VPN_NAME), shell=True)

    def close_vpn(self):
        subprocess.call("sudo poff {}".format(settings.VPN_NAME), shell=True)

    def ensure_vpn(self):
        try:
            # TODO How robust is this check?
            netifaces.ifaddresses('ppp0')
            logger.info('Found VPN')
            # Reset the backoff
            self.vpn_backoff = 0
        except ValueError:
            # Sleep for backoff period
            time.sleep(self.vpn_backoff)
            # Try to connect again
            self.open_vpn()
            # Set the backoff in case it fails
            self.vpn_backoff += settings.VPN_BACKOFF
            # Give time for connection to establish
            # TODO Clumsy; can we wait for response or listen for an event?
            time.sleep(2)
            return self.ensure_vpn()


daemon_log = open('logs/daemon.log', 'w')

context = RuswarpContext(
    pidfile=lockfile.FileLock('/tmp/ruswarp.pid'),
    working_directory=os.getcwd(),
    files_preserve=[fh.stream],
    stdout=daemon_log,
    stderr=daemon_log
)

if __name__ == '__main__':
    with context:
        # Instantiate the database client
        db = context.db_client.get_default_database()
        entries = db['raw']
        # Start up the headless browser
        context.driver.get(settings.URL)
        context.driver.wait_for_element(settings.WAIT_FOR)
        while True:
            data = context.driver.get_data()
            entries.insert(data)
            time.sleep(settings.POLL)
            context.ensure_vpn()

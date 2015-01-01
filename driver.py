

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from datetime import datetime

class RuswarpDriver(webdriver.PhantomJS):
    def parse_data_value(self, value_txt):
        """
        Return the value coerced to be a float, bool or left as a string.
        Try to convert to a number, and then the less common boolean.
        """
        try:
            return float(value_txt)
        except ValueError:
            if value_txt == 'false':
                return False
            if value_txt == 'true':
                return True
            return value_txt

    def parse_data_rows(self, rows):
        """ Generator that yields data name, value pairs from a iter of rows """
        for row in rows:
            name_el, value_el, _ = row.find_elements_by_css_selector('td')
            # Get the text content for each element
            # Coerce the value into the correct type
            name = name_el.text
            value = self.parse_data_value(value_el.text)
            # Check we have found a value
            if not name or not value:
                continue
            yield (name, value,)

    def get_data(self):
        """ Return dict containing all the tag names and their values """
        # Make the containing div visible, otherwise the values won't render
        self.execute_script("document.getElementById('DataViewerFrame').style.display = 'block'")
        table = self.find_element_by_id('propertyTable')
        rows = table.find_elements_by_css_selector('tbody tr')
	data = {
            name: value for name, value in self.parse_data_rows(rows)
        }
        # Record a timestamp
        data['time'] = datetime.utcnow()
        return data

    def wait_for_element(self, element_id):
        """ Wait for a given DOM id to exist """
        wait = WebDriverWait(self, 10)
        wait.until(EC.presence_of_element_located((By.ID, element_id)))

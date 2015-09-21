import sys
import datetime
import codecs
from bs4 import BeautifulSoup
from filetimes import filetime_to_dt

service_center = "+33695000657"

def unix_time(dt):
	epoch = datetime.datetime.utcfromtimestamp(0)
	delta = dt - epoch
	return delta.total_seconds()

def android_time(dt):
	return unix_time(dt) * 1000.0

class WP_SMS:
	def __init__(self, msg):
		self.body = msg.body.string
		self.sender = msg.sender.string
		self.recepients = [r.string for r in msg.recepients.findAll("string")]
		self.timestamp = filetime_to_dt(int(msg.localtimestamp.string))

	def is_incoming(self):
		return self.sender != None

	def __str__(self):
		inc = "incoming" if self.is_incoming() else "sent"
		return "WP_SMS:\n\t[" + inc + "]\n\tfrom: " + str(self.sender) + "\n\tto: " + str(self.recepients) + "\n\tdate: " + self.timestamp + "\n\tbody: " + self.body

	def to_sms_backup(self):
		sms_type = "1" if self.is_incoming() else "2"
		sms_body = self.body.replace("&", "&amp;").replace("\r\n", "\n").replace("\n", "&#10;").replace("\"", "&quot;")
		sms_service_center = service_center if self.is_incoming() else "null"
		sms_timestamp = str(int(android_time(self.timestamp)))
		def xml_node(address):
			return ("<sms "
					"protocol=\"0\" "
					"address=\"" + address + "\" "
					"date=\"" + sms_timestamp + "\" "
					"type=\"" + sms_type + "\" "
					"subject=\"null\" "
					"body=\"" + sms_body + "\" "
					"toa=\"null\" "
					"sc_toa=\"null\" "
					"service_center=\"" + sms_service_center + "\" "
					"read=\"1\" "
					"status=\"-1\" "
					"locked=\"0\" "
					"date_sent=\"0\" "
					"readable_date=\"\" "
					"contact_name=\"\" "
					"/>")
		if self.is_incoming():
			return [xml_node(self.sender)]
		else:
			return [xml_node(a) for a in self.recepients]


def load_msg(filename):
	with open(filename, 'r') as file:
		full_file = file.read()
		xml = BeautifulSoup(full_file, "html.parser")
		messages = [WP_SMS(msg) for msg in xml.arrayofmessage.findAll("message")]
		return messages;

def export_smsbackup(smses, filename):
	xml = ("<?xml version='1.0' encoding='UTF-8' standalone='yes' ?>"
	       "<?xml-stylesheet type=\"text/xsl\" href=\"sms.xsl\"?>\n"
	       "<smses count=\"" + str(len(smses)) + "\">\n")
	count = 0
	for sms in smses:
		for node in sms.to_sms_backup():
			xml += "    " + node + "\n"
			count += 1
	xml += "</smses>"
	with codecs.open(filename, 'w', 'utf-8') as f:
		f.write(xml)
	return count


if __name__ == "__main__":
	if len(sys.argv) != 3:
		print("Unrecognized command line. Format: wp_sms_to_sms_backup <source> <dest>\n"
			"where:\n"
			"   <source> = sms backup file from windows phone, usually ends with \".msg\"\n"
			"   <dest>   = file to write, it will be readable by the \"SMS Backup & Restore\" app\n")
	else:
		src = sys.argv[1]
		dst = sys.argv[2]
		print("Loading " + src + "...")
		smses = load_msg(src)
		print(str(len(smses)) + " sms found")
		nbxml = export_smsbackup(smses, dst)
		print(str(nbxml) + " sms nodes written to " + dst)


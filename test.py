import mysql.connector

config = {
  'user': 'hoi4intel',
  'password': 'tiYNfCYhsRKsm5M4FDGGtCim7AHRen49yCcQEhb7',
  'host': 'host.igportals.eu',
  'raise_on_warnings': True,
}

try:
	cnx = mysql.connector.connect(**config)
	print("Connection passed. Listing DB's:\n")
	cursor = cnx.cursor()
	cursor.execute("show databases")
	for db in cursor:
		print(str(db[0]))
	print("\nClosing connection!\n")
	cnx.close()
except Exception as ex:
	print("Fail: " + str(ex))

import mysql.connector

bot_token = ")T8gBRffdud4)AnY*^rUvjQrtV%FfIgSmpUsW6b+&V+V(VJ4JvWC&U$^D%!n%DNK"

# GOOGLE API KEY FOR PERSPECTIVE API
API_KEY = ''

# TOKEN FOR COMMUNICATION BETWEEN DASHBOARD AND BOT
comms_token = ''

# AI Commands
openai_api_key = ""
openai_api_base = ""

# Dashboard Server URL
ws_url = "http://localhost:8000"
discord_invite_url = ""

# MySQL credentials
host = 'localhost'
database = 'wwcbot'
user = 'wwcbot'
password = 'vErYsEcUrE'
hoi = False
# UUID Of the computer running the bot primarily (for production)
host_uuid = 495081613286  # Example UUID, get it by running uuid.getnode() in the python CLI

def setup():
    connection = mysql.connector.connect(host=host,
                                         database=database,
                                         user=user,
                                         password=password,
                                         autocommit=True)

    cursor = connection.cursor()
    return cursor, connection


def dictionary_setup():
    connection = mysql.connector.connect(host=host,
                                         database=database,
                                         user=user,
                                         password=password,
                                         autocommit=False,
                                         charset='utf8mb4')
    cursor = connection.cursor(dictionary=True)
    return cursor, connection

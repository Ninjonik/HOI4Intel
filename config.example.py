import mysql.connector
import redis

bot_token = ")T8gBRffdud4)AnY*^rUvjQrtV%FfIgSmpUsW6b+&V+V(VJ4JvWC&U$^D%!n%DNK"

# GOOGLE API KEY FOR PERSPECTIVE API
API_KEY = ''

# MODERATE CONTENT API KEY
moderate_content_api_key = ''

# TOKEN FOR COMMUNICATION BETWEEN DASHBOARD AND BOT
comms_token = ''

# Dashboard Server URL
ws_url = "http://localhost:8000"
discord_invite_url = ""

# MySQL credentials
host = 'localhost'
database = 'wwcbot'
user = 'wwcbot'
password = 'vErYsEcUrE'

# Redis credentials
redis_host = ''
redis_port = 6379
redis_username = ''
redis_password = ''

# UUID Of the computer running the bot primarily (for production)
host_uuid = 495081613286  # Example UUID, get it by running uuid.getnode() in the python CLI

prev_redis_instance = None


def redis_connect():
    global prev_redis_instance

    if prev_redis_instance:
        prev_redis_instance.close()

    new_redis_instance = redis.Redis(
        host=redis_host,
        port=redis_port,
        username=redis_username,
        password=redis_password,
        charset = "utf-8",
        decode_responses = True,
    )

    prev_redis_instance = new_redis_instance
    return new_redis_instance


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

import redis

lcd_message = {'line_1': 'Temperature: ', 'line_2': 'Humidity: '}
PREVIOUS_LINE="\x1b[1F"
RED_BACK="\x1b[41;37m"
GREEN_BACK="\x1b[42;30m"
YELLOW_BACK="\x1b[43;30m"
RESET="\x1b[0m"

# Singleton redis to prevent connection conflicts
r = redis.Redis(host='127.0.0.1', port=6379)
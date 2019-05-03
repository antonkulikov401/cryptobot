import app
import app.db_utils


def main():
    with open('token', 'r') as token_file:
        token = token_file.readline()[:-1]
    app.init_bot(token)
    app.bot.polling(none_stop=True, interval=1)


if __name__ == '__main__':
    app.db_utils.open_connection()
    app.db_utils.create_tables()
    main()
    app.db_utils.close_connection()

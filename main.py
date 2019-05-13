import app
import app.db_utils


def main():
    app.init_bot()
    app.bot.polling(none_stop=True, interval=1)


if __name__ == '__main__':
    app.db_utils.open_connection()
    app.db_utils.create_tables()
    main()
    app.db_utils.close_connection()

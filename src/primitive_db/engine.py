import prompt

HELP = """<command> exit - выйти из программы
<command> help - справочная информация"""


def welcome():
    """Запустить интерактивный цикл команд."""
    print("Первая попытка запустить проект!")
    print("\n***")
    print(HELP)

    while True:
        try:
            command = prompt.string("Введите команду: ").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            return

        if command == "exit":
            return
        if command == "help":
            print(HELP)
        else:
            print("Неизвестная команда. Введите help для справки.")

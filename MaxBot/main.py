from max_api import MaxApiClient
from bot_logic import BotLogic
import time

TOKEN = "f9LHodD0cOK0Qd9ejbieobIqGs4vgVmvWllZLrdCURamLNdJAfqzw-lRgpKLiAMfm57repfI5jlzJtEH0Dfc"

def main():
    api = MaxApiClient(TOKEN)
    bot = BotLogic(api)

    marker = None

    print("Бот запущен...")

    while True:
        try:
            updates, marker = api.get_updates(marker)

            for update in updates:
                bot.handle_update(update)

        except Exception as e:
            print(f"Ошибка в основном цикле: {e}")
            time.sleep(5)

if __name__ == "__main__":
    main()
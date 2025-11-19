import asyncio
from web3 import Web3
import random

# Количество транзакций
NUM_TRANSACTIONS = 1000

# Чтение приватных ключей
with open('private.txt', 'r') as f:
    private_keys = [line.strip() for line in f]

# Чтение прокси
with open('proxy.txt', 'r') as f:
    proxies = [line.strip() for line in f]

# Подключение к Plume Mainnet через WSS
w3 = Web3(Web3.LegacyWebSocketProvider('wss://rpc.plume.org'))

# Проверка подключения
if not w3.is_connected():
    raise Exception("Не удалось подключиться к сети Plume")


async def send_transaction(private_key, proxy, tx_number, total_txs):
    try:
        # Получение адреса кошелька
        account = w3.eth.account.from_key(private_key)
        wallet_address = account.address

        # Проверка баланса $PLUME
        balance = w3.eth.get_balance(wallet_address)
        amount = w3.to_wei(1, 'ether')  # 1 PLUME
        if balance < amount:
            print(f"Ошибка: Недостаточно $PLUME на {wallet_address} (баланс: {w3.from_wei(balance, 'ether')} PLUME)")
            return False

        # Проверка баланса для газа
        gas_price = w3.to_wei('1001', 'gwei')
        estimated_gas_cost = 21000 * gas_price
        if balance < amount + estimated_gas_cost:
            print(
                f"Ошибка: Недостаточно $PLUME для газа на {wallet_address} (баланс: {w3.from_wei(balance, 'ether')} PLUME)")
            return False

        # Параметры транзакции
        nonce = w3.eth.get_transaction_count(wallet_address)
        tx = {
            'from': wallet_address,
            'to': wallet_address,  # Отправка на тот же кошелёк
            'value': amount,
            'nonce': nonce,
            'gas': 21000,
            'gasPrice': gas_price
        }

        # Подпись и отправка
        signed_tx = w3.eth.account.sign_transaction(tx, private_key=private_key)
        tx_hash = w3.eth.send_raw_transaction(signed_tx.raw_transaction)
        print(f"Транзакция {tx_number}/{total_txs} отправлена для {wallet_address}: {w3.to_hex(tx_hash)}")

        # Ожидание подтверждения
        receipt = w3.eth.wait_for_transaction_receipt(tx_hash, timeout=120)
        if receipt.status == 1:
            print(f"Транзакция {tx_number}/{total_txs} успешно подтверждена")
        else:
            print(f"Транзакция {tx_number}/{total_txs} не удалась")
            return False

        # Пауза 2 секунды
        await asyncio.sleep(2)
        return True

    except Exception as e:
        print(f"Ошибка при обработке транзакции {tx_number} для {wallet_address}: {str(e)}")
        return False


async def main():
    if NUM_TRANSACTIONS <= 0:
        print("Укажите положительное количество транзакций")
        return
    if not private_keys:
        print("Файл private.txt пуст")
        return

    total_txs = NUM_TRANSACTIONS
    print(f"Всего транзакций: {total_txs}")

    for i in range(total_txs):
        private_key = private_keys[i % len(private_keys)]  # Циклический выбор кошелька
        proxy = random.choice(proxies)  # Случайный выбор прокси
        success = await send_transaction(private_key, proxy, i + 1, total_txs)
        if not success:
            print(f"Пропуск транзакции {i + 1} из-за ошибки, продолжаем с следующей")


if __name__ == "__main__":
    asyncio.run(main())
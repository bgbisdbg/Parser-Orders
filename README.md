<h1>Парсер закупок</h1>

1. Устанавливаем зависимости из файла requirements.txt.

2. Запускаем сервер RabbitMQ (если нет, то нужно установить).

3. Запускаем код через терминал PyCharm. Вводим команду.

   ```
   celery -A main:app worker --loglevel=info --pool=eventlet
   ```
4. Получаем результат:

5. 
   ![image](https://github.com/bgbisdbg/Library/assets/136889642/6fc16eba-03f2-481a-992e-1aa66706590b)

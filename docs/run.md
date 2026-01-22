How to Run the New System:

  You will need a running Redis server. Once Redis is available, you must start the three processes in separate terminals from
  your project's root directory:

   1. Start the RQ Worker:
   1     # Make sure your virtual environment is activated
   2     python worker.py

   2. Start the Telegram Bot Poller:

   1     # In a new terminal
   2     python bot.py

   3. Start the Flask Web Application:
   1     # In a third terminal
   2     python run.py

  This new architecture is significantly more robust, scalable, and maintainable.
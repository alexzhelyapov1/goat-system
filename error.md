client:745 WebSocket connection to 'ws://127.0.0.1:40049/?token=EMbP7OQrJnQs' failed: 
createConnection @ client:745Understand this error
client:755 WebSocket connection to 'ws://localhost:5000/?token=EMbP7OQrJnQs' failed: 
createConnection @ client:755Understand this error
client:765 [vite] failed to connect to websocket.
your current setup:
  (browser) 127.0.0.1:40049/ <--[HTTP]--> localhost:5000/ (server)
  (browser) 127.0.0.1:40049/ <--[WebSocket (failing)]--> localhost:5000/ (server)
Check out your Vite / network configuration and https://vite.dev/config/server-options.html#server-hmr .
connect @ client:765Understand this error
HabitForm.tsx:2 Uncaught SyntaxError: The requested module '/src/types/habit.ts' does not provide an export named 'Habit' (at HabitForm.tsx:2:10)
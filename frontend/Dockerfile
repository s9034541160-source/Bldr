FROM node:18-alpine

WORKDIR /app

# Копирование файлов зависимостей
COPY package*.json ./

# Установка зависимостей
RUN npm install

# Копирование кода приложения
COPY . .

# Открытие порта
EXPOSE 3000

# Запуск dev сервера
CMD ["npm", "run", "dev", "--", "--host", "0.0.0.0"]


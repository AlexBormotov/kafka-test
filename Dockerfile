FROM nginx:alpine

# Копируем файлы проекта в директорию nginx
COPY index.html /usr/share/nginx/html/
COPY mouseTracker.js /usr/share/nginx/html/
COPY README.md /usr/share/nginx/html/

# Настраиваем nginx для обработки запросов к API
COPY nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"] 
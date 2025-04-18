FROM nginx:alpine

# Копируем файлы проекта в директорию nginx
COPY templates/index.html /usr/share/nginx/html/
COPY static/ /usr/share/nginx/html/static/
COPY README.md /usr/share/nginx/html/

# Настраиваем nginx для обработки запросов к API
COPY nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"] 
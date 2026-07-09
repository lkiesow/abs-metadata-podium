FROM python:3.14-slim
WORKDIR /app
COPY . .
RUN pip install --no-cache-dir .
ENV ABS_METADATA_PODIUM_HOST=0.0.0.0
EXPOSE 8000
CMD ["abs-metadata-podium"]

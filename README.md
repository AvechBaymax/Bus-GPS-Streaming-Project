# 🚌 Bus GPS Data Pipeline

Real-time big data pipeline xử lý GPS tracking data của hệ thống xe bus sử dụng **Kafka + Hadoop + Spark + PostgreSQL**.

## 📊 **Dataset**

- **Source**: GPS tracking data của 2,575 xe bus
- **Size**: 849MB (9.8M records/day)
- **Columns**: datetime, vehicle_id, lng/lat, driver, speed, door_status
- **Scale**: ~310GB/year với real-time streaming

## 🏗️ **Architecture**

```
📄 CSV Data → 📤 Kafka Producer → ☁️ Kafka Topics → 📥 Consumer → 🐘 PostgreSQL
                                       ↓
                               🔥 Spark Processing
                                       ↓
                               🗄️ Hadoop Storage
```

## 🐳 **Tech Stack**

- **Message Queue**: Apache Kafka 7.4.0
- **Stream Processing**: Apache Spark 3.4.0
- **Storage**: Hadoop 3.2.1 + PostgreSQL 15
- **Orchestration**: Docker Compose
- **Language**: Python 3.x
- **Libraries**: confluent-kafka, pandas, psycopg2

## 🚀 **Quick Start**

### 1. Clone & Setup

```bash
git clone <your-repo-url>
cd first_project
python -m venv .venv
.venv\Scripts\activate  # Windows
pip install -r requirements.txt
```

### 2. Start Infrastructure

```bash
docker-compose up -d
```

### 3. Create Sample Data

```bash
python scripts/create_sample_data.py
```

### 4. Run Pipeline

```bash
# Producer: CSV → Kafka
python src/kafka/producer.py

# Consumer: Kafka → PostgreSQL
python src/kafka/consumer.py
```

## 📁 **Project Structure**

```
first_project/
├── docker-compose.yml          # Infrastructure stack
├── data/
│   ├── raw_2025-04-01.csv     # Original dataset (849MB)
│   └── samples/                # Test samples (1K-100K records)
├── src/
│   ├── kafka/
│   │   ├── producer.py         # CSV → Kafka
│   │   └── consumer.py         # Kafka → PostgreSQL
│   └── spark/                  # Spark processing jobs
├── scripts/
│   ├── create_sample_data.py   # Sample data generator
│   └── init_db.sql            # Database setup
└── requirements.txt
```

## 🎯 **Kafka Topics**

- **`bus-gps-tracking`**: Real-time GPS coordinates
- **`bus-door-events`**: Door open/close events
- **`bus-operational-data`**: Speed, driver info

## 📈 **Performance**

- **Throughput**: ~1000 records/second
- **Latency**: <100ms end-to-end
- **Compression**: LZ4 (~60% reduction)
- **Partitioning**: By vehicle_id (load balancing)

## 🔧 **Development**

### Sample Data Sizes:

- `sample_quick_test.csv`: 1K records (80KB)
- `sample_small_dev.csv`: 10K records (790KB)
- `sample_medium_test.csv`: 100K records (7.8MB)

### Testing:

```bash
# Test với sample nhỏ
python src/kafka/producer.py data/samples/sample_quick_test.csv

# Performance test
python src/kafka/producer.py data/samples/sample_medium_test.csv
```

## 📋 **TODO**

- [x] Docker infrastructure setup
- [x] Sample data creation
- [x] Kafka Producer implementation
- [ ] Kafka Consumer + PostgreSQL integration
- [ ] Spark batch processing
- [ ] Real-time dashboard
- [ ] Performance monitoring

## 🤝 **Contributing**

1. Fork the project
2. Create feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit changes (`git commit -m 'Add AmazingFeature'`)
4. Push to branch (`git push origin feature/AmazingFeature`)
5. Open Pull Request

## 📄 **License**

MIT License - see LICENSE file for details.

# Open container bash

docker exec -it first_project-kafka-1 bash

# Create topic

ocker exec first_project-kafka-1 kafka-topics --create --topic bus-gps-tracking --bootstrap-server localhost:9092 --partitions 3 --replication-factor 1

# Describe topic

docker exec first_project-kafka-1 kafka-topics --describe --topic bus-gps-tracking --bootstrap-server localhost:9092

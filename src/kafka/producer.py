import json
import csv
import sys
from datetime import datetime
from threading import Event
import math
import time
from confluent_kafka import Producer

# Configuration - PRODUCTION READY
conf = {
    'bootstrap.servers': 'localhost:9092',  # Docker Kafka exposed port
    'enable.idempotence': True,  # Đảm bảo không bị duplicate
    'acks': 'all',  # Đảm bảo message được ghi nhận
    'retries': 3,  # Số lần thử lại khi gửi thất bại
    'max.in.flight.requests.per.connection': 5,  # Giới hạn số request đồng thời

    # Batching settings
    'linger.ms': 2,  # Giảm số lần gửi bằng cách chờ
    'batch.size': 32*1024,  # Kích thước batch gửi  32KB
    'compression.type': 'lz4',  # Nén dữ liệu để tiết kiệm băng thông

    # Timeout settings
    'message.timeout.ms': 15000,  # Timeout cho mỗi message
    'delivery.timeout.ms': 30000,  # Tổng timeout cho delivery
}

# Create producer instance
producer = Producer(conf)

# Create callback for delivery reports
def delivery_report(err, msg):
    if err is not None:
        print(f"Message delivery failed: {err}")
    else:
        print(f"Message delivered to {msg.topic()} [{msg.partition()}] at offset {msg.offset()}")

# create send_message function - non-blocking, simple version
def send_async(producer, topic, key, value):
    """
    Gửi message non-blocking (asynchronous) - NEWBIE FRIENDLY VERSION
    Caller nên gọi:
        - producer.poll(0) thường xuyên trong vòng lặp gửi
        - producer.flush() khi shutdown để đảm bảo gửi hết
    Parameters:
        producer : confluent_kafka.Producer
        topic    : str - tên topic
        key      : str - partition key (nếu cần đảm bảo ordering)
        value    : str - JSON string (đã serialize)
    Returns:
        bool - True if queued successfully, False if failed
    """
    try: 
        # Ghi message vào buffer của producer - trả kết quả ngay
        producer.produce(
            topic=topic,
            key=key,
            value=value,
            callback=delivery_report 
        )
        return True  # Success - message queued
    except BufferError:
        # Local queue đầy -> phải chờ/handle backpressure
        print("Buffer full, try calling poll() or slow down")
        return False  # Failed - buffer full
    except Exception as e:
        print(f"Send error: {e}")
        return False  # Failed - other error

# producer.flush() 
# + Block cho đến khi tất cả message trong queue của producer đã được gửi 
# + Đã nhận ACK 
# + Callback đã chạy xong.
# producer.poll(): 
# + Gửi message trong buffer nếu đã đến lúc
# + Xử lí ACK và chạy hết các hàm callback tương ứng

# =============================================================================
# CSV PROCESSING FUNCTION
# =============================================================================

def process_csv_to_kafka(csv_file_path, topic='bus-gps-tracking', max_records=None):
    """
    Process CSV file và send vào Kafka topic
    
    Parameters:
        csv_file_path: Path to CSV file
        topic: Kafka topic name  
        max_records: Limit records for testing
    
    Returns:
        dict: Processing results
    """
    print(f"Processing: {csv_file_path}")
    print(f"Sending to Topic: {topic}")
    
    sent_count = 0
    failed_count = 0
    total_count = 0
    
    try:
        with open(csv_file_path, 'r', encoding='utf-8') as file:
            csv_reader = csv.DictReader(file)
            
            for row in csv_reader:
                total_count += 1
                
                try:
                    # Convert CSV row to bus data
                    bus_data = {
                        'datetime': row['datetime'],
                        'vehicle': row['vehicle'],
                        'lng': float(row['lng']) if row['lng'] else None,
                        'lat': float(row['lat']) if row['lat'] else None,
                        'speed': float(row['speed']) if row['speed'] else None,
                        'driver': float(row['driver']) if row['driver'] else None,
                        'door_up': row['door_up'].lower() == 'true' if row['door_up'] else False,
                        'door_down': row['door_down'].lower() == 'true' if row['door_down'] else False,
                    }
                    
                    # Send to Kafka
                    success = send_async(
                        producer=producer,
                        topic=topic,
                        key=row['vehicle'],  # Partition by vehicle_id
                        value=json.dumps(bus_data)
                    )
                    
                    if success:
                        sent_count += 1
                    else:
                        failed_count += 1
                        
                except Exception as e:
                    print(f"Row {total_count} error: {e}")
                    failed_count += 1
                
                # Poll every 100 messages
                if total_count % 100 == 0:
                    producer.poll(0)
                    print(f"Progress: {sent_count:,} sent, {failed_count} failed")
                
                # Check limit
                if max_records and total_count >= max_records:
                    print(f"Reached limit: {max_records}")
                    break
        
        # Final cleanup
        print("Flushing messages...")
        remaining = producer.flush(30)
        
        if remaining > 0:
            print(f"{remaining} messages not delivered")
            failed_count += remaining
        
        # Results
        success_rate = (sent_count / total_count * 100) if total_count > 0 else 0
        
        print(f"""
            COMPLETED!
            Total: {total_count:,}
            Sent: {sent_count:,}
            Failed: {failed_count}
            Success: {success_rate:.1f}%
        """)
        
        return {
            'total': total_count,
            'sent': sent_count,
            'failed': failed_count,
            'success_rate': success_rate
        }
        
    except FileNotFoundError:
        print(f"File not found: {csv_file_path}")
        return {'total': 0, 'sent': 0, 'failed': 0, 'success_rate': 0}
    except Exception as e:
        print(f"Error: {e}")
        return {'total': total_count, 'sent': sent_count, 'failed': failed_count, 'success_rate': 0}

# =============================================================================
# MAIN FUNCTION FOR TESTING
# =============================================================================
'''
if __name__ == "__main__":
    """Main function để test producer"""
    
    # Default test file
    test_file = "data/samples/sample_quick_test.csv"
    
    # Check command line arguments
    if len(sys.argv) > 1:
        test_file = sys.argv[1]
    
    print("KAFKA PRODUCER TEST")
    print(f"File: {test_file}")
    
    # Test processing
    result = process_csv_to_kafka(
        csv_file_path=test_file,
        topic='bus-gps-tracking',
        max_records=100  # Limit for testing
    )
    
    # Evaluate results
    if result['success_rate'] >= 90:
        print("TEST PASSED! Producer is working well.")
    elif result['success_rate'] >= 70:
        print("TEST OK but has some issues.")
    else:
        print("TEST FAILED! Check Kafka connection.")
        sys.exit(1)
'''